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
    c. extract      keyword anchors + nearest-box layout + wrapped-address merge -> declarations
    d. scale        ArUco DICT_4X4_50 -> credit-card rectangle -> inspector PDP mm -> none  [P4]
    e. measure      height_mm, width/height ratio, contrast, same-panel grouping (only with scale)
    f. rules        rules/pc_rules_2011.yaml -> violations [rule_id, rule_ref, severity, message,
                    evidence]                                                            [P3]
    g. score+report 100 - penalties; HTML -> PDF + DOCX + JSON -> Storage scans/<id>/report.*  [P5]
    h. write back   ocr_words, declarations, violations, reports, scans.status = done | failed

  Steps d-g are not built yet. `run_local` catches NotImplementedError from the rule engine and
  scores 100, so the queue works before the rules do; that try/except is deleted in P3.
  One `Word` is one PP-OCR line box, never a split of one — the split coordinates would be
  invented, and this project does not invent measurements.

Supabase — Postgres + Auth + Storage + Realtime, RLS on every table
Dashboard — Next.js server components read the views directly under the caller's RLS
```

## Schema (see `supabase/migrations/0001_init.sql`)

profiles(role) · products · scans · scan_images · ocr_words · declarations · violations · reports · evidence · audit_log · model_calls.
Views: `dashboard_summary`, `top_violations` (30 days), `violations_by_category`. All `security_invoker`.
Function `claim_scan()` (service role only). Trigger: new auth user → profile with role `viewer`.

## RLS summary

| Role | profiles | products | scans / scan_images / evidence | pipeline tables | audit_log |
|---|---|---|---|---|---|
| viewer | read | read | read | read | — |
| inspector | read | read, insert, update own | read all, insert/update own | read | — |
| admin | all | all | all | read | read |
| service role (worker) | bypasses RLS | | | writes | |

Storage bucket `scans` (private): authenticated read; inspector/admin insert/update; admin delete.

## Measurement

`eval/` is a first-class part of the system, not a test folder: 53 cases (37 real photographs and
listing screenshots, 16 rendered labels), a hand-written `gold.json` per case, and a committed
result file per labelled run. `docs/EVAL.md` is the method; `docs/PROGRESS.md` is the numbers.

The one architectural concession to it is that `run_local` takes its OCR step as an argument, so
the eval can memoise PaddleOCR on disk and a rerun measures the change rather than re-reading 260
photographs. Nothing else passes anything but the default.

## Why it is defensible

- The rule engine is deterministic and cites the rule. No AI decides compliance. No external AI API anywhere.
- Nothing is estimated: no scale reference → the font check says "not verifiable" and costs no points.
- Every part is open source and self-hostable. Rules live in a YAML file DoCA can edit without code.
- Every claim about accuracy has a committed result file behind it, including the four changes
  that were measured and rejected.

## Deployment (₹0)

- Frontend: Vercel Hobby. Env: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- Supabase free tier. Pauses after 7 idle days — keep the worker polling, unpause before the demo. Photos resized to 1600 px to stay under 1 GB.
- Worker: one container from `worker/Dockerfile` on a Hugging Face Space (free CPU, Docker SDK; sleeps after ~48 h idle, first request wakes it; needs an HTTP listener on 7860 — a stdlib thread, P9) or an Oracle Always Free ARM VM. Laptop is the fallback. Env: `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.

## Scaling later

`claim_scan()` uses `for update skip locked`, so N worker containers can poll the same table safely. OCR is the only heavy step; a GPU worker would plug in at `ocr.py` with no other change. Storage and Postgres grow linearly with scans; the 1600 px cap keeps a scan under ~1 MB.
