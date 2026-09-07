# PROGRESS

Reference tracker. What is built, what is not, and what is blocked on a human.

`docs/PLAN.md` holds the order and the "done when" line for each phase. This file holds the
detail: per item status, where the code is, and how it was checked. Update both in the same
commit.

Status words: **done** · **partial** · **todo** · **blocked** (needs a person, not code).

Last updated: 2026-09-07.

---

## Summary

| Phase | State | Blocking item |
|---|---|---|
| P0 dataset + eval harness | **done** | photos with a reference card still need a person (F1/F2) |
| P1 schema + auth + upload + worker loop | **done** | — |
| P2 OCR + extractor baseline | measured, below target | 94.5% synthetic, **28.9% real**; target 70% |
| P3 rule engine + detail page | todo | tests written, 130 `xfail` waiting |
| P4 scale + font / contrast / grouping | todo | — |
| P5 reports | todo | — |
| P6 repository + search + history | todo | — |
| P7 dashboard + roles + audit | todo | — |
| P8 e-commerce mode | todo | — |
| P9 deploy + docs | todo | — |

---

## P0 — dataset + eval harness

**Done when:** `make eval LABEL=empty` prints a per-field table. **This is true today.**

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | Eval harness runs and writes a result file | done | [run_eval.py](eval/run_eval.py) → `eval/results/2026-09-07_p0-synthetic-16.json` |
| 2 | Synthetic label generator | done | [make_synthetic.py](eval/make_synthetic.py), 16 cases |
| 3 | Gold format written down | done | [eval/dataset/README.md](eval/dataset/README.md) |
| 4 | Gold files validated automatically | done | [test_dataset.py](worker/tests/test_dataset.py), 5 checks × 16 cases |
| 5 | Shot list for the real set | done | [eval/dataset/README.md](eval/dataset/README.md) |
| 6 | Real package photos | done | 31 cases / 102 photographs from Open Food & Beauty Facts, [fetch_openfoodfacts.py](eval/fetch_openfoodfacts.py) |
| 7 | E-commerce screenshots | done | 6 listings from amazon.in and flipkart.com, [fetch_ecommerce.py](eval/fetch_ecommerce.py) |
| 8 | gold.json for each real case | done | 37 written by reading the photographs |
| 9 | OCR memoised so a rerun measures the change | done | `eval/.ocr_cache/`, keyed on the image + a hash of `preprocess.py` and `ocr.py` |
| 10 | Photos with a reference card / two panels / two MRPs | **blocked** | needs a person; the web set cannot test F1, F2, P1, P3 or D5b |

### What the 16 synthetic cases cover

| Case | Context | Expected codes |
|---|---|---|
| `synthetic_compliant` | — | none |
| `synthetic_no_manufacturer` | — | D1 |
| `synthetic_no_generic_name` | — | D2 |
| `synthetic_no_tax_wording` | — | D5 |
| `synthetic_approx_no_email` | — | D3, D6 |
| `synthetic_no_date` | — | D4 |
| `synthetic_future_date` | — | D4 |
| `synthetic_no_unit_price` | — | D8 |
| `synthetic_missing_three` | — | D1, D3, D5 |
| `synthetic_imported_no_origin` | `is_imported` | D7 |
| `synthetic_imported_ok` | `is_imported` | none |
| `synthetic_small_sachet` | `net_qty_g_or_ml: 8` | none (X1 downgrades to info) |
| `synthetic_restaurant_food` | `is_restaurant_food` | none (X2 skips) |
| `synthetic_dpco_drug` | `is_dpco_drug` | none (X3 skips) |
| `synthetic_ecom_missing_qty` | `source: ecommerce` | E1 |
| `synthetic_ecom_complete` | `source: ecommerce` | none |

**Not covered by synthetics, on purpose:** F1, F2 (need a real scale), P1 (needs two panels),
P2 contrast, P3 seam, P4 language, D5b (needs two MRP boxes on one pack), E2. These come from
the real photos. The unit tests in `worker/tests/test_rules.py` already pin their behaviour.

### Latest eval run

`2026-09-07_p0-synthetic-16` — 16 cases, pipeline ran on 0, field accuracy 0.0%.
That is correct: `run_local` raises `NotImplementedError("P2")`. The number is the baseline to
beat. The table lists all 10 canonical fields, so nothing is silently missing from the gold.

### How the real set was built

1. `eval/fetch_openfoodfacts.py` searched Open Food Facts and Open Beauty Facts for Indian
   products and downloaded every selected front / ingredients / nutrition / packaging photo at
   1600 px — the size the frontend uploads. 117 candidate products.
2. `eval/fetch_ecommerce.py` rendered six public product listings with headless Chrome and sliced
   each capture into 1600 px tiles.
3. Every image was OCR'd once to find which ones carry a Legal Metrology declaration at all. That
   text was a finding aid only; **gold was written by reading the photograph**.
4. 81 candidates were deleted: an ingredients close-up, a nutrition table on its own, a studio
   render whose declarations contradicted the photographs in the same folder, or print too small
   or too cut to write gold honestly.
5. `make test` (the dataset tests catch typos in field names and rule codes), then
   `make eval LABEL=…`.

### What the real set does not cover

No photo on Open Food Facts has an ArUco marker or a credit card in frame, and OFF crops rarely
show two panels at once. So F1, F2 (font), P1 (grouping), P3 (seam) and D5b (two MRPs) have no
real case and never appear in gold — they are `unverifiable` without a scale and cost no points.
Those are the photos the shot list still asks for.

---

## P1 — Supabase schema + auth + upload + worker loop

**Done when:** a scan goes queued → processing → done end to end from a phone. **This is true.**

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | `0001_init.sql`: tables, RLS, bucket, views, realtime, `claim_scan()` | done | `supabase/migrations/0001_init.sql` |
| 2 | `supabase link` + `db push` on the hosted project | done | project `jcjxukjgrbmkuydpsnuc`; `supabase migration list` shows 0001 local **and** remote |
| 3 | `make seed` creates admin / inspector / viewer | done | 3 rows in `profiles` with the right roles |
| 4 | Login, upload form, scans list | done | `frontend/app/{login,upload,scans}` |
| 5 | Realtime status on the scan detail page | done | [scan-realtime.tsx](frontend/components/scan-realtime.tsx), mounted only while the scan is queued/processing |
| 6 | Worker marks a fake scan `done` | done | [pipeline/__init__.py](worker/pipeline/__init__.py), [test_run_scan.py](worker/tests/test_run_scan.py) |
| 7 | One scan end to end from a phone | done | scan `5e0811b8`, 2026-09-07, `192.168.1.10:3000` |

### How the loop was checked

A throwaway script queued a scan with one 1×1 JPEG in the `scans` bucket and called
`process_one` once:

```
queued d5e24bf4-…
scan d5e24bf4-…: no pipeline yet (P2), storing an empty result
after worker: {'status': 'done', 'compliance_score': 100, 'error': None}
```

`claim_scan()` is callable by the service role and refused to `anon`/`authenticated`; the `scans`
bucket exists. `run_local` still raises `NotImplementedError("P2")` — `run_scan` catches it and
stores an empty result so the queue works before the pipeline does. That `try/except` is deleted
in P2.

### Three bugs the phone run found

None of them showed up on localhost, which is the point of testing on the device.

| Symptom | Cause | Fix |
|---|---|---|
| Sign-in button stuck on "Signing in…", no message | `lib/env.ts` read `process.env[name]` with a computed key. Next.js only inlines `NEXT_PUBLIC_*` where the name is literal, so the client bundle had no URL or key and `createClient()` threw. Server code read a real `process.env`, so auth tested fine against the API. | literal references; `submit()` got a try/catch so a throw prints instead of hanging |
| `crypto.randomUUID is not a function` | secure-context-only API, and the phone loads `http://192.168.1.10:3000` | [lib/uuid.ts](frontend/lib/uuid.ts) builds v4 from `getRandomValues`, which is not gated |
| Only one photo could ever be added | `capture="environment"` and `multiple` on one input — capture wins and caps the pick at one file. `onChange` also replaced the list rather than appending. | separate camera and gallery inputs, both appending to one list of 3 |

`createImageBitmap`, canvas and `toBlob` are **not** secure-context gated, so the resize path was
fine over plain HTTP. `getUserMedia` and `crypto.subtle` would not be — they need HTTPS if a later
phase reaches for them.

### Verified on the hosted project

| Thing | Result |
|---|---|
| `supabase db push` | 0001 applied, no errors |
| `profiles` after `make seed` | Demo Admin/admin, Demo Inspector/inspector, Demo Viewer/viewer |
| `claim_scan()` as service role | returns `[]` on an empty queue |
| storage buckets | `['scans']` |
| `make db-types` | regenerated `frontend/lib/database.types.ts`; `tsc --noEmit` clean |
| scan from a phone | `5e0811b8` — 1 image, resized 1205×1600, `done`, no error |
| a real scan through the queue with the P2 pipeline, 2026-09-07 | scan `3b14da20`: queued -> claimed -> `done`, 46 `ocr_words` rows and 6 declarations written against the real schema (word ids remapped onto the ones Postgres assigned), then deleted. Score 100 because the rule engine is P3. |

---

## P2 — OCR + regex/layout extractor (baseline)

**Done when:** `make eval LABEL=baseline-v1` >= 70% field extraction on clean photos.
**98.2% on the 16 synthetic labels. 28.9% on the 37 real cases.** Met on clean labels, not met on
photographs. The harness prints the two apart because one number hid which half moved.

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | `preprocess.py` | done | [preprocess.py](worker/pipeline/preprocess.py) — bilateral denoise; deskew deliberately dropped |
| 2 | `ocr.py` PP-OCRv4 -> boxes + confidence | done | [ocr.py](worker/pipeline/ocr.py); one `Word` = one line box |
| 3 | `extractors/regex_layout.py` | done | [regex_layout.py](worker/pipeline/extractors/regex_layout.py), [test_extract.py](worker/tests/test_extract.py) |
| 4 | `run_local` wired end to end | done | [pipeline/__init__.py](worker/pipeline/__init__.py) |
| 5 | Measured on rendered labels | done | 94.5%, `eval/results/2026-09-07_p2-baseline.json` |
| 6 | Measured on real photographs | done | 28.9%, `eval/results/2026-09-07_p2-real-final.json` |
| 7 | 70% on real photographs | **not met** | see the three causes below |

### Every labelled run, in order

The first five ran on a 48-case set; the last two on the settled 53-case set, so the two groups
are not comparable to each other. Within each group one variable changed per run.

| Run | Change | Combined |
|---|---|---|
| `p2-real-baseline` | the real set as first assembled | 55.9% |
| `p2-real-continuations` | wrapped lines merged for **every** field | 51.4% — worse |
| `p2-real-wrap-address-only` | merged only where the law prints an address block | 55.9% |
| `p2-real-anchors` | wordings off the packs (`mkt by`, `n. qty`, `net content`, six consumer-care phrasings); bare `origin` dropped | 56.8% |
| `p2-real-tighter-layout` | a bare anchor takes a box on its own row, in reach, that is not a declaration itself | 57.7% |
| `p2-real-det1600` | PP-OCR detects at 1600 px instead of 960 | 54.5% — worse, reverted |
| `p2-real-glued-anchors` | an anchor may end against its value | 57.7% |
| `p2-real-ignore-spacing` | the eval ignores spacing, as the dataset README always said | 60.8% |
| `p2-real-number-guard` | a price or quantity label with no figure looks for the figure | 61.7% |
| `p2-real-cross-reference` | "SEE BOTTLE" / "SAME AS ... ADDRESS" claims nothing | 61.7%, 11 fewer wrong claims |
| `p2-real-listing-labels` | `manufacturer` / `packer` anchors for listing tables | flat, 3 more false positives — reverted |
| `p2-real-final-baseline` | the extractor as it was **before** all of the above, on the settled set | 52.7% (real 18.5%) |
| `p2-real-final` | the extractor as it stands, on the settled set | 58.4% (real **28.9%**) |
| `p2-real-wrap-stops-at-pointer` | a wrapped address stops at "scan barcode" / "same as" too | flat; the Kurkure manufacturer went from a four-line blob to one line |
| `p2-real-clahe` | CLAHE on the lightness channel in `preprocess` | **60.0%** (synthetic 94.5% -> **98.2%**, real unchanged) |
| `p2-real-sideways-pass` | a second OCR pass at 90° when the boxes look like a sideways page | 59.6% (real 28.9% -> 28.1%) — worse, reverted |
| `p2-final` | the pipeline as it stands | **60.0%** (synthetic 98.2%, real 28.9%) |

Real-only: **18.5% -> 28.9%**, measured on the same 53 cases with the same OCR cache.

### Where the remaining real-photo gap is

Counting the 96 misses on the real cases:

Counted on `p2-real-tighter-layout`, before CLAHE; CLAHE moved none of these.

| Cause | Misses | Can the extractor reach it? |
|---|---|---|
| The common name is printed with no label at all | 23 | No. "SPICED BUTTERMILK", "CARBONATED WATER", "Lip Balm" — an anchor extractor has nothing to anchor on. This is the case for the Stretch item. |
| A wrapped address where PP-OCRv4 dropped a line | ~28 | Partly. The merge works; on a curved bottle one line of the address is never detected, so the block is never word for word. |
| The photograph itself lost it | ~14 | No. Thumb over the panel, pack held sideways, value column cropped out of frame. |
| Everything else (recognition slips, wrong neighbour) | ~31 | Some. |

A separate check — "does the OCR text contain half the gold words anywhere in the case?" — says
**85 of the 96 misses are reachable**: the text was on the page and the extractor did not use it.
Reproduce it with

```bash
cd worker && uv run python ../eval/diagnose.py reach ../eval/results/2026-09-07_p2-final.json
```

That split is why the work went into the extractor and not into the OCR settings, and why
`det_limit_side_len` was tried and reverted rather than assumed.

### What P2 does not do

- No deskew, no scale, no measurement. `mm_per_px` stays `None`, `scale_source` stays `none`.
- No rules: `run_local` catches `NotImplementedError` from `run_rules` and scores 100. That
  `try/except` is deleted in P3.
- No second OCR pass for a pack held sideways: measured, and it made the real half worse
  (28.9% -> 28.1%). The trigger fires on panels that merely *contain* vertical text — a Coke
  bottle prints "MADE IN INDIA" sideways among horizontal lines — and rotating loses the rest.
  A per-box orientation decision, not a per-page one, is what that would need.
- Nothing else named in `docs/PLAN.md` is untried. The next lever is the Stretch item: a local
  VLM extractor for the declarations that are printed with no label at all.

---

## P3–P9

Not started. See `docs/PLAN.md` for the item list and the "done when" line of each phase.
The tests for P3 and P4 are already written and carry a strict
`xfail(raises=NotImplementedError)`; 130 of them are waiting. Deleting the `xfail` line is how
those phases get marked done.

---

## Log

- **2026-09-07** — **P0 done, P2 measured on real photographs.** The dataset blocker ("needs a
  camera") turned out not to need one: Open Food Facts and Open Beauty Facts are public databases
  of phone photographs of packaging, and their back-panel shots are where the Legal Metrology
  declarations are printed. 117 Indian products were pulled, 31 kept with hand-written gold, plus
  6 e-commerce listings screenshotted with headless Chrome. 81 were deleted for having no legible
  declaration. Gold was written by reading each photograph, never by running the pipeline.
  Real-photo field extraction went 18.5% -> 28.9% over seven measured changes; four further
  hypotheses were measured and reverted for scoring worse or flat. Combined with the synthetic
  set, 52.7% -> 60.0%, the last 1.6 points from CLAHE, which took the rendered labels to 98.2%
  and corrected an earlier note that had blamed the recognition model for what was contrast. **The 70% line is
  met on rendered labels (94.5%) and not on photographs**; the three causes are counted above and
  the largest of them — a common name printed with no label — is not something an anchor
  extractor can reach. The eval now memoises OCR, without which one labelled run costs an hour.
  `make test` green (248 passed, 130 xfailed), `make lint` clean.
  Still blocked on a person: photos with a reference card in frame, which is the only way to test
  the font rules.

- **2026-09-07** — **P2 baseline done on the synthetic set.** PaddleOCR PP-OCRv4 → line boxes →
  anchor + layout extractor → declarations, wired into `run_local` and `run_scan`. Field
  extraction 0.0% → 94.5% over four labelled runs. `paddlepaddle` had to be pinned to 3.0.0: on
  3.3.1 every PP-OCRv4 model fails inside oneDNN regardless of `enable_mkldnn`. `make test` green
  (84 passed, 130 xfailed), `make lint` clean. Real photos still blocked on a camera, so P2 will
  be re-measured when P0 item 6 lands.

- **2026-09-07** — **P1 done.** A scan shot on a phone over the LAN went queued → processing →
  done with the status updating on screen unprompted. The device run found three bugs localhost
  could not (see the table above): non-inlined `NEXT_PUBLIC_*`, `crypto.randomUUID` outside a
  secure context, and `capture` silently defeating `multiple` on the photo input. Score is 100 on
  every scan because `run_local` is still P2.
- **2026-09-07** — P1 code complete. Hosted project linked and `0001_init.sql` pushed; `make seed`
  created the three demo users; `.env` and `frontend/.env.local` written from the project's API
  keys (both gitignored). `run_scan` downloads the scan's images, runs the pipeline and writes
  words/declarations/violations back, remapping word ids onto the ones Postgres assigns; until P2
  lands it catches `NotImplementedError` and stores an empty result. Scan detail page refreshes on
  realtime updates while the scan is queued or processing. `database.types.ts` is generated now,
  with the check-constraint unions moved to `frontend/lib/db.ts`. `make test` green
  (80 passed, 130 xfailed), `make lint` clean, `tsc --noEmit` clean. Remaining: the phone run.

- **2026-09-07** — P0: synthetic set grown 3 → 16 cases (D1–D8, D7 imported, E1, X1/X2/X3);
  gold files now validated by `worker/tests/test_dataset.py`; shot list added to the dataset
  README. `make test` green (76 passed, 130 xfailed). Baseline eval recorded at 0.0%.
  Remaining P0 work is the real photo set, which needs a person.
  Also: `eval/results/*.json` un-ignored (a gitignored measurement is not a record), and
  `make lint` extended to cover `eval/`.
- **2026-09-06** — P0 harness, 3 synthetic cases, rules YAML, P3/P4 tests, schema, frontend
  shell. See the Decisions log in `docs/PLAN.md`.
