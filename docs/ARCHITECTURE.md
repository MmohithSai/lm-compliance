# ARCHITECTURE

## Data flow

```
Phone / laptop browser — Next.js PWA on Vercel
  1. login (Supabase Auth, email + password)
  2. resize photos to <= 1600 px on the client
  3. upload to Storage: scans/<scan_id>/<n>.jpg          (scan_id generated on the client)
  4. insert scans row (status = queued, source, has_reference_card, pdp_width_mm, pdp_height_mm)
     + one scan_images row per photo
  5. subscribe to Realtime on that scans row; show progress

Python worker — laptop / HF Space / Oracle VM, service-role key, talks *out* only
  loop every 3 s: rpc claim_scan()  -> one queued row flips to processing (atomic, skip locked)
    a. preprocess   OpenCV bilateral denoise + CLAHE on the LAB lightness channel.  [P2, built]
                    No deskew: PP-OCRv4 finds rotated quads itself, and rotating the page would
                    put every box in a space the detail page cannot draw in.
    b. ocr          PaddleOCR PP-OCRv4 -> one box per printed *line* [text, box, confidence]
                    -> ocr_words.  Injectable (`run_local(..., ocr=)`) so the eval can memoise it.
    c. extract      keyword anchors + nearest-box layout + wrapped-address merge -> declarations.
                    Photographs in upload order (`order("storage_path")`, and the extractor keeps
                    that order). A label that names a figure has to be followed by one of the
                    right shape (a price is not a batch code, a date is what month_and_year
                    reads); a label may be a two-line cell; a printed figure is the value of one
                    label; anchors survive the spaces PP-OCR drops; the three address fields take
                    the fullest candidate; an unlabelled unit price is found by its shape.
                    [P2, audited 2026-09-08]
    d. scale        ArUco DICT_4X4_50 -> credit-card rectangle -> inspector PDP mm -> none.
                    Per photograph, never borrowed between frames. The card is only looked for
                    when the inspector said one is in the shot: ungated, the shape claimed a
                    scale in 14 eval frames with no card in them.                    [P4, built]
    e. measure      height_mm, width/height ratio and contrast of the *print inside* each OCR
                    box (Otsu, then the glyphs), measured on the photograph as uploaded rather
                    than the preprocessed copy, and only where step d found a scale. No scale ->
                    all three stay None and F1/F2/P2 report "not verifiable".        [P4, built]
    f. rules        rules/pc_rules_2011.yaml -> violations [rule_id, rule_ref, severity, message,
                    evidence]                                                            [P3]
    g. score+report 100 - penalties; one Report model -> JSON + report.html -> PDF (WeasyPrint)
                    + DOCX (python-docx) -> Storage scans/<id>/report.*             [P5, built]
                    A format that will not render is stored as a null path; it never fails
                    the scan and never takes the other two with it.
    g'. can this be judged?  before anything is written: the text PP-OCR returned, in characters.
                    Under 80 the scan stops here as `failed`, with a sentence for the inspector
                    in `scans.error` and no words, declarations, violations or report file
                    behind it. `score([])` is 100 by construction, so an unreadable photograph
                    that reaches `done` shows 100 / 100 for a pack nobody read.       [P8, built]
    h. write back   ocr_words, declarations, violations, reports, scans.status = done | failed

  An e-commerce scan (`source = ecommerce`) is judged by Rule 6(10) and nothing else: steps d
  and e are pointless on a screenshot — a scale measured there measures the screen — and the
  rule engine's `_applies` never applies F1, F2, F3, P1, P2 or P3 to one. Not "unverifiable":
  never applied, because a screenshot is not the package.

  Grouping (P1) has no failure side and will not get one here: a
  scale says how big a pixel is, not whether two photographs show one panel or two.
  One `Word` is one PP-OCR line box, never a split of one — the split coordinates would be
  invented, and this project does not invent measurements.

Supabase — Postgres + Auth + Storage + Realtime, RLS on every table
Dashboard — Next.js server components read the views directly under the caller's RLS
```

## Schema (see `supabase/migrations/0001_init.sql`)

profiles(role) · products · scans · scan_images · ocr_words · declarations · violations · reports · evidence · audit_log · rules · model_calls.
Views: `scan_search` (P6) and, for the dashboard, `dashboard_summary`, `top_violations`,
`scans_by_category`, `dashboard_recent_scans`. All `security_invoker`, so a caller sees totals
over exactly the scans their RLS lets them read.
`rules` is a mirror of `rules/pc_rules_2011.yaml`, refreshed by the worker at start up
(`sync_rules`), so the dashboard can name a rule without a second copy of the law in the repo.
Functions: `claim_scan()` (service role only), `auth_role()` (authenticated only, called by every
policy), `audit()` (trigger only). Triggers: new auth user → profile with role `viewer`; insert,
update and delete on `scans`, `products` and `evidence` → `audit_log`, actor `auth.uid()`, null
for the service role. No trigger on `audit_log` itself.

## RLS summary

| Role | profiles | products | scans / scan_images / evidence | pipeline tables | audit_log |
|---|---|---|---|---|---|
| viewer | read | read | read | read | — |
| inspector | read | read, insert, update own | read all, insert/update own | read | — |
| admin | all | all | all | read | read |
| service role (worker) | bypasses RLS | | | writes | |

Storage bucket `scans` (private): authenticated read; inspector/admin insert/update; admin delete.

## Measurement

`eval/` is a first-class part of the system, not a test folder: 56 cases (38 real photographs and
listing screenshots, 18 rendered labels, two of them carrying a 50 mm ArUco marker at a known
scale), a hand-written `gold.json` per case, and a committed result file per labelled run.
`eval/error_report.py` puts every real-photo miss beside the OCR line that best covers it and
names the stage that lost it; `eval/compare.py` diffs two runs per field and per case, marking
each change better or worse against gold. `docs/EVAL.md` is the method; `docs/PROGRESS.md` is
the numbers; `docs/AUDIT.md` is the 2026-09-08 audit of P0–P8 against the implementation.

The one architectural concession to it is that `run_local` takes its OCR step as an argument, so
the eval can memoise PaddleOCR on disk and a rerun measures the change rather than re-reading 260
photographs. Nothing else passes anything but the default.

## Why it is defensible

- The rule engine is deterministic and cites the rule. No AI decides compliance. No external AI API anywhere.
- Nothing is estimated: no scale reference in that frame → the font *and contrast* checks say
  "not verifiable" and cost no points. A scale is never borrowed from another photograph, and a
  card-shaped rectangle is only a card when the inspector said one is in the shot.
- A photograph nobody can read gets no verdict at all. The gate is the number of characters
  PP-OCR returned (`MIN_READABLE_CHARS = 80` in `worker/pipeline/__init__.py`), and it is
  measured, not guessed: across the 56 eval cases the least legible reads 134 characters and a
  listing screenshot 5,300–10,100, while one real Amazon tile blurred, shrunk 8× or motion
  blurred until it is unreadable falls from 218 to 44–59. Confidence is deliberately *not* part
  of the test — PP-OCR answers a blurred panel by not detecting the small print and still
  reports the few headline words at 0.94–0.97, so it does not move where the count collapses.
- Every part is open source and self-hostable. Rules live in a YAML file DoCA can edit without code.
- Every claim about accuracy has a committed result file behind it, including every change that
  was measured and then thrown away — nine so far, and they are the most useful entries in the
  record, because they stop the next person retrying them.
- The answer does not depend on the order the photographs arrive in. Read in upload order, and
  the fields that could still differ (the address blocks) take the fullest candidate. Measured
  before the fix: reversing the images changed 7 of 37 multi-image cases and flipped a D5 verdict.
- What the system cannot do is counted, not hidden: real-photo field extraction is 44.0% (62 of
  141 declarations, 2026-09-08), and `eval/results/<run>_errors.md` says for each of the 79
  misses whether the OCR never saw the print (23), the pack printed no label to anchor on (20),
  the words were read but not grouped (17), or a character was misread (9).

## Deployment (₹0)

- Frontend: Vercel Hobby. Env: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- Supabase free tier. Pauses after 7 idle days — keep the worker polling, unpause before the demo. Photos resized to 1600 px to stay under 1 GB.
- Worker: one container from `worker/Dockerfile` on a Hugging Face Space (free CPU, Docker SDK; sleeps after ~48 h idle, first request wakes it; needs an HTTP listener on 7860 — a stdlib thread, P9) or an Oracle Always Free ARM VM. Laptop is the fallback. Env: `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.

## Scaling later

`claim_scan()` uses `for update skip locked`, so N worker containers can poll the same table safely. OCR is the only heavy step; a GPU worker would plug in at `ocr.py` with no other change. Storage and Postgres grow linearly with scans; the 1600 px cap keeps a scan under ~1 MB.
