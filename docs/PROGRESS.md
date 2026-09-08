# PROGRESS

Reference tracker. What is built, what is not, and what is blocked on a human.

`docs/PLAN.md` holds the order and the "done when" line for each phase. This file holds the
detail: per item status, where the code is, and how it was checked. Update both in the same
commit.

Status words: **done** · **partial** · **todo** · **blocked** (needs a person, not code).

Last updated: 2026-09-08.

---

## Summary

| Phase | State | Blocking item |
|---|---|---|
| P0 dataset + eval harness | **done** | photos with a reference card still need a person (F1/F2) |
| P1 schema + auth + upload + worker loop | **done** | — |
| P2 OCR + extractor baseline | measured, below target | 98.2% synthetic, **29.8% real**; target 70% |
| P3 rule engine + detail page | **done** | — (the page was finally opened in a browser during P5; it crashed, see the log) |
| P4 scale + font / contrast / grouping | **done**, half of it measured | 5 real photos with a card still need a person (same blocker as P0 item 10) |
| P5 reports | **done** | — |
| P6 repository + search + history | **done** | — |
| P7 dashboard + roles + audit | **done** | — |
| P8 e-commerce mode | todo | — |
| P9 deploy + docs | todo | — |

---

## P0 — dataset + eval harness

**Done when:** `make eval LABEL=empty` prints a per-field table. **This is true today.**

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | Eval harness runs and writes a result file | done | [run_eval.py](eval/run_eval.py) → `eval/results/2026-09-07_p0-synthetic-16.json` |
| 2 | Synthetic label generator | done | [make_synthetic.py](eval/make_synthetic.py), 18 cases (16 + 2 with a marker, added in P4) |
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

**Not covered by synthetics, on purpose:** P1 (needs two panels), P3 seam, P4 language, D5b
(needs two MRP boxes on one pack), E2. These come from the real photos, and the unit tests in
`worker/tests/test_rules.py` already pin their behaviour. F1, F2 and P2 were in this list until
P4: two further rendered cases now carry a 50 mm ArUco marker at a known scale
(`synthetic_marker_font_ok`, `synthetic_marker_font_small`), which tests the measuring chain but
not a photograph of one — the shot list is still open.

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
**98.2% on the 16 synthetic labels. 29.8% on the 38 real cases.** Met on clean labels, not met on
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
| 8 | Printed declaration tables | done | 2026-09-08, six labelled runs: real 28.4% -> 29.8%, **7 fewer false accusations, no new misses** |

### Reading a printed declarations table

A real scan of a Reynolds pen box turned up a layout the whole web set is blind to: the
declarations set in a **bordered two-column table**, label cell left, value cell right, two of the
labels wrapping onto a second line. The extractor read none of its values, and the report told the
inspector the pack had no MRP, no date and no manufacturer, all of which it prints plainly. The
pack is now `eval/dataset/phone_reynolds_jetter_classic_ballpen`, added **before** anything was
changed to read it.

Three parts, one labelled run each, plus three that were measured and thrown away:

| Run | Change | Real | Verdict |
|---|---|---|---|
| `p4base-with-table-pack` | baseline, the new case added | 28.4% | — |
| `p4-same-row-is-vertical-overlap` | row test = overlap half a line | 27.4% | reverted |
| `p4-same-row-anchor-middle` | row test = anchor's middle inside the value | 27.4% | reverted |
| `p4-table-cell-last-resort` | reach into the cell only after the strict row and the line below both fail, best aligned box | 28.4% | kept |
| `p4-wrapped-label-cell` | merge the label cell's second line | 29.1% | kept |
| `p4-label-cell-same-table-row` | merge rule = begins before the value ends | 28.4% | reverted |
| `p4-table-cell-second-pass` | the cell reach is a second pass over the panel | 29.8% | kept |
| `p4-label-cell-is-a-chain` | follow the label cell one line at a time | 29.8% | kept, 2 fewer false violations |
| `p4-centred-address-block` | a continuation may be centred, not only left aligned | 29.8% | kept, 2 fewer false D6 |
| `p4-address-block-seven-lines` | `MAX_LINES` 7 + a "manufactured, marketed" anchor | 29.8% | kept, violation precision 0.71 -> 0.74 |

Two of those deserve their own line, because both were mistakes I made and the eval caught:

- **Loosening the row test does not work.** Twice, two different ways, 1.5 points each time. The
  reason is not the test but the tiebreak: the leftmost box of a loosened set is often the wrong
  one, and on `off_bru` it was the **barcode**, read as a net weight. The fix that works keeps the
  strict test first and only falls back to the cell, taking the best aligned box, never the nearest.
- **A weak match must not claim a field.** The first version let a loosely aligned cell box win,
  which shut out a box printed further down that had its date right beside it. Running the cell
  reach as a second pass over the whole panel fixed it and was worth 0.7 points on its own.

The pen box scan went **100 (nothing read) -> 17 -> 52 -> 87**. What is left on it is one
false D2, because PP-OCR read `Ceneric Name Ball Pen` — a single wrong character, the same class
of miss as `Bjscuits`, and not something an extractor can reach.

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

## P3 — rule engine + scan detail page

**Done when:** `test_rules.py` green; one real scan shown start to finish.
**Green since 2026-09-08**, with the caveat in item 6.

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | All 20 checks in `CHECKS` | done | [rules_engine.py](worker/pipeline/rules_engine.py); the 130 `xfail`s are gone, 115 rule tests pass |
| 2 | Rule 26 exemptions | done | X1 downgrades to info, X2/X3 skip the rule, X4 is a note. `EXEMPT_WHEN` + `SKIPS_THE_RULE` |
| 3 | Violations stored with rule ref and evidence | done | `store()` was already writing them; scan `7f7eb986` has 3 fails + 4 `unverifiable` rows |
| 4 | Detail page: image with boxes, declarations, violations, score | done | [scans/[id]/page.tsx](frontend/app/scans/[id]/page.tsx), [scan-evidence.tsx](frontend/components/scan-evidence.tsx). Click a violation, its boxes turn red |
| 5 | Engine reproduces gold from gold declarations | done | 53/53, `test_engine_reproduces_gold_from_gold_declarations`. Found one wrong gold file on its first run |
| 6 | One real scan end to end | done | `7f7eb986` (synthetic label, score 25) and `5e0811b8` (a phone photo of a Reynolds pen box, 45 OCR lines, score 17). Both seen on screen |
| 7 | An unreadable photo cannot score 100 | done | `run_scan` fails the scan instead; `test_run_scan_fails_when_the_ocr_read_nothing` |

### Three things the first look at the page found

| Symptom | Cause | Fix |
|---|---|---|
| Boxes drawn in the wrong places | the page divided by `scan_images.width`/`height`, and the throwaway script that made that scan had written the wrong pair | the page uses the size of the image the browser loaded, which cannot disagree with the file |
| **100 / 100 on a pack the pipeline never read** | `score([])` is 100 by construction, and `5e0811b8` was a pre-P2 stub with zero OCR words | `run_scan` refuses to finish a scan with no words: `failed`, with a message telling the inspector how to re-shoot. Fixed in the pipeline, not on the page, so the P5 report and the P7 dashboard inherit it |
| D4 quoting "Manufactured,Marketed and" as a month and year | the `manufactured` anchor claimed a line with no date in it | a date label with no figure in it is a label — `mfg_date` joins `NEEDS_A_NUMBER`. Precision 0.56 → 0.65 |

The pen box also shows the P2 gap at full size. PP-OCR read the pack almost perfectly — `'MRP'`,
`'25.00'`, `'02/2026'`, the whole address — and the extractor still reported no MRP, no generic
name and no manufacturer, for two reasons that are not the rule engine's: one character wrong
(`'Ceneric Name Ball Pen'`, so the anchor does not match) and a value in the next table cell two
pixels outside the same-row tolerance. Two ways of widening that tolerance were measured and both
cost 1.5 points of real accuracy, so both were reverted. **A printed declarations table is the
shape the extractor cannot read, and it is a common one.**

### What the numbers say

Violation accuracy over three labelled runs on 2026-09-08, extraction untouched throughout
(field accuracy 60.0% / real 28.9% / synthetic 98.2% in all three):

| Run | Precision | Recall | Exact set |
|---|---|---|---|
| `p3-rules` | 0.67 | 0.99 | 28.3% |
| `p3-d5-marker-unverifiable` | 0.71 | 0.98 | 49.1% |
| `p3-p1-photos-are-not-panels` | 0.73 | 0.98 | 49.1% |

The remaining false positives, by rule, against that field's extraction misses:

| Rule | False positives | Extraction misses for the field it reads |
|---|---|---|
| D2 generic name | 17 | 20 |
| D6 consumer care | 10 | 11 |
| D5 MRP | 6 | 10 |
| D1 manufacturer | 6 | 17 |
| D4 month/year | 5 | 7 |
| D8 unit sale price | 5 | 9 |
| D3 net quantity | 4 | 8 |

Every rule is under its field's miss count, and the engine is exact on all 53 gold declaration
sets. **There is no rule bug left in these numbers — they are P2's extraction numbers seen from
the other end.** Three false negatives in total, all extraction artefacts.

Not built here, on purpose: F1, F2 and P2 report `unverifiable` because nothing measures
`height_mm`, `width_height_ratio` or `contrast` yet — that is P4. P3 pins what they say when the
measurement is missing.

## P4 — reference card scale + font / contrast / grouping

**Done when:** font check correct on 5 photos with a card; "not verifiable" without one.
**The second half is measured and true. The first half needs a person with a card** — that is
P0 item 10, and no photograph in the set has a scale reference in frame.

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | ArUco DICT_4X4_50 → mm/px | done | [measure.py](worker/pipeline/measure.py); recovers 0.1253 against a true 0.1250 on the marker cases |
| 2 | Credit-card rectangle → mm/px | done, gated | only when the inspector ticked the box: ungated it claimed a scale in 14 card-less frames |
| 3 | Inspector PDP mm fallback | done | panel width in mm ÷ the photo's width in px, which assumes the panel fills the frame; the upload form now says so |
| 4 | `height_mm`, `width_height_ratio`, `contrast` per declaration | done | `ink()` measures the print inside each OCR box, on the photograph as uploaded |
| 5 | F1, F2, P2 live | done | they fire on `synthetic_marker_font_small` and report `unverifiable` on all 54 photographs, costing no points |
| 6 | P1 grouping live | **not possible** | a scale does not tell two photographs apart; see the Decisions log. P1 passes or reports unverifiable, as in P3 |
| 7 | `xfail` line deleted from `tests/test_measure.py` | done | the 26 xfails are gone; 465 tests pass |
| 8 | A live case in the eval set | done | two rendered labels with a 50 mm marker, one expecting F1 |

### How a millimetre is arrived at

1. **A scale, per photograph.** ArUco marker → credit card (only if the inspector said one is
   there) → the inspector's panel width against the photo's pixel width → none. A scale is never
   borrowed from another frame: a marker in frame 3 says nothing about how far away frame 2 was
   shot, and borrowing one would be the same class of error as inventing one.
2. **The print, not the box.** A PP-OCR box is padded and spans a whole line. Inside it Otsu
   separates ink from paper, blobs shorter than 40% of the line's ink are dropped as dots and
   grain, and what is left are the glyphs. The height is their 90th percentile — the capitals and
   numerals Table I is about. The width/height ratio is the median of each glyph's own width over
   its own height, which needs no scale at all.
3. **Contrast** is the CIE Lab distance between the core of the stroke and the paper beside it,
   over 100. The same crop, so the lighting is common to both sides and largely cancels.
4. **Nothing without a reference.** No scale in that frame → all three stay `None` → F1, F2 and
   P2 report `unverifiable` with a reason and cost no points.

### Every labelled run, in order

Extraction is untouched throughout. The field numbers move only where the two marker cases joined
the set (54 → 56 cases).

| Run | Change | Field acc. (real / synth) | Violations P / R / exact |
|---|---|---|---|
| `p4-address-block-seven-lines` | the P3 baseline | 59.8 (29.8 / 98.2) | 0.74 / 0.98 / 48.1% |
| `p4-measure-wired` | scale + height + ratio + contrast, all live | 59.8 (29.8 / 98.2) | **0.64** / 0.98 / 38.9% |
| `p4-card-only-when-the-inspector-says-so` | a rectangle is not a card unless the form says one is there | 59.8 (29.8 / 98.2) | 0.65 / 0.98 / 38.9% |
| `p4-contrast-in-colour` | contrast as Lab distance, not brightness | 59.8 (29.8 / 98.2) | 0.65 / 0.98 / 38.9% |
| `p4-contrast-needs-a-shot-made-for-measuring` | P2 joins F1/F2 behind a scale reference | 59.8 (29.8 / 98.2) | **0.74** / 0.98 / 48.1% |
| `p4-marker-cases` | two rendered cases with a 50 mm marker | 62.2 (29.8 / 98.4) | 0.74 / 0.98 / **50.0%** |
| `p4-height-is-the-tall-glyphs` | height = the 90th percentile glyph, not the 75th | 62.2 (29.8 / 98.4) | 0.74 / 0.98 / 50.0% |

### Three things the measurements got wrong first

Every one of them was caught by a number, not by reading the code.

| Symptom | Cause | Fix |
|---|---|---|
| A scale on 14 frames with no card in them | any quadrilateral with 85.6 × 54 proportions counted as a card: a product photo on a listing, a carton side, a label panel | the inspector's own answer gates the card path. The marker path needs no gate — a marker's bits are error-corrected |
| **27 of 27 real photographs called low-contrast** (precision 0.74 → 0.64) | brightness alone. Red print on green is legible and almost equally bright. Lab distance fixed 1 case of 27; measuring the stroke's core instead of its anti-aliased edge moved the real median 0.38 → 0.47 and the rendered labels 0.87 → a true 0.99, and 54% were still under the floor | enlarging the worst crops settled it — a shadow across a Sprite bottle, and "500 mL" in pale blue that is perfectly legible on the carton. That is the light and the focus, not the print, so P2 now needs a photo shot to be measured, like F1 and F2 |
| A mostly lower-case line measured 2.26 mm where its capitals are 3.13 mm | the 75th percentile of glyph heights lands on the x-height | the 90th percentile. Not the tallest glyph: one OCR box that swallowed a logo would then set the height for the whole declaration |

### A P3 bug the P0 tests caught on the way

`rules_engine.TABLE_I` ended `(inf, 6.0, 6.0)`: above 2500 cm² an embossed numeral was held to
6 mm where Rule 7 and `docs/RULES.md` both say 8. `tests/test_measure.py` has asserted the right
number since P0 behind its `xfail`, and deleting that line surfaced it. There is now one Table I,
in `measure.py`, which the rule engine imports along with the ⅓ ratio and the exempt characters.

### What P4 does not do

- **P1 has no failure side.** A scale does not tell two photographs apart, and the note in the P3
  entry that said it would was wrong. It needs the inspector's answer, the way P3 already asks
  about the bottom and the seam, or photo-to-photo matching. Neither is a measurement.
- **Contrast is not stored.** `declarations` has no `contrast` column and `store()` still drops
  it. When P2 fails the value is in the violation's evidence, which is what the report will read;
  when it passes, nobody has asked for the number. Add the column if P5's PDF wants it.
- **No real photograph has ever been measured**, only rendered ones. Glare, perspective and focus
  are untested, and the eval cannot speak to them until the shot list is shot.
- Rule 8's cylinder and irregular shapes stay out of scope: `pdp_area_cm2` is the inspector's
  width × height, and without it F1 says the panel area is unknown.

## P5 — reports

**Done when:** the PDF opens on a phone and looks clean. **This is true today.**

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | One report model behind all three files | done | `Report` and friends in [models.py](worker/pipeline/models.py); built by `build_report` in [report.py](worker/pipeline/report.py). Schema `1.0`. |
| 2 | JSON report | done | `render_json`. Nine top-level keys, four disjoint finding lists, evidence as boxes not word ids. 8 tests in [test_report.py](worker/tests/test_report.py) |
| 3 | `report.html` → PDF (WeasyPrint) | done | [templates/report.html](worker/pipeline/templates/report.html); A4, 11.5 pt, one column, fonts embedded, running foot with page numbers. Verified by rendering `phone_reynolds_jetter_classic_ballpen`: **4 pages, 149 KB, PDF 1.7**, opened and read page by page |
| 4 | DOCX (python-docx) | done | `render_docx`; same hierarchy as the PDF. Tests open the bytes back with `python-docx` and assert the headings, the verdict line, each severity and the declarations |
| 5 | Evidence photographs in the report | done | `annotate` / `annotate_panels`: boxes burned in with OpenCV (blue = declaration read, red = evidence cited), downscaled to 900 px, embedded as a data URI |
| 6 | Uploaded to `scans/<id>/report.*` | done | `publish_report` in [pipeline/__init__.py](worker/pipeline/__init__.py), inside the same temp dir as the photographs. Upserts one `reports` row per scan |
| 7 | One report row per scan | done | [0002_reports_one_per_scan.sql](supabase/migrations/0002_reports_one_per_scan.sql), pushed to the hosted project; `reports_scan_key` confirmed present |
| 8 | A format that will not render loses no other format | done | per-format try/except; `reports.pdf_path` is null and the page says so. Pinned by a test that makes `render_pdf` raise |
| 9 | Download buttons on the detail page | done | [scan-reports.tsx](frontend/components/scan-reports.tsx) + [scans/[id]/page.tsx](frontend/app/scans/[id]/page.tsx). Signed URLs with a download filename; states for queued/processing, failed, no report, and partial |
| 10 | Assets vendored with licences recorded | done | [templates/assets/README.md](worker/pipeline/templates/assets/README.md) + `fetch.sh`. IBM Plex Sans (SIL OFL 1.1), 5 Lucide icons (ISC) |
| 11 | Rules refactor measured, not asserted | done | `eval/results/2026-09-08_p5-reports.json` is identical on every key to `2026-09-08_p4-marker-cases.json` |
| 12 | One real scan end to end against the hosted project | done | scan `3f5b8e1e`, 2026-09-08: queued → claimed → `done`, score 87; `scans/3f5b8e1e…/report.{pdf,docx,json}` at 149515 / 161171 / 11697 bytes with the right MIME types; one `reports` row with all three paths |
| 13 | The buttons seen and used in a browser | done | logged in as `inspector@example.com` at 375 px; all three signed URLs fetched **200** with the right content types; the pre-P5 scan `7f7eb986` shows "No report was written for this scan" |

Not covered by code, and worth saying: **who may download a report is exactly who may open the
scan.** The bucket is private, the page only mints a signed URL for a session that already read
the scan row through RLS, and `middleware.ts` sends anyone without a session to `/login`. There
is no new authorisation surface in P5, which is the reason there is no new policy in `0002`.

## P6 — repository + search + history + evidence

**Done when:** search "Parle" returns its scans and history. **True**, and still true after the
evidence work — verified on the hosted project, see the evidence column.

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | Product match on scan completion | done | [product.py](worker/pipeline/product.py), [test_product.py](worker/tests/test_product.py) (12 checks) + 5 wiring checks in [test_run_scan.py](worker/tests/test_run_scan.py). Live: scans `5e0811b8` and `3f5b8e1e` both file under `reynolds pens\|` |
| 2 | Search page + per-product history | done | `scan_search` view in `0003_product_match_and_search.sql`; [/scans](frontend/app/scans/page.tsx), [/products/[id]](frontend/app/products/[id]/page.tsx). `?q=reynolds` returns both scans; the product page shows 2 scans, average 87 |
| 3 | Evidence photos + notes on a scan | done | [evidence.ts](frontend/lib/evidence.ts) + [evidence.test.ts](frontend/lib/evidence.test.ts) (13 checks), [scan-evidence-photos.tsx](frontend/components/scan-evidence-photos.tsx), [scan-notes.tsx](frontend/components/scan-notes.tsx), `0004_evidence_on_a_scan.sql`. 13 hosted checks as a real inspector and a real viewer |
| 4 | A listing's own "Manufacturer" label (really P2's) | done | [regex_layout.py](worker/pipeline/extractors/regex_layout.py), 3 new checks in [test_extract.py](worker/tests/test_extract.py); `eval/results/2026-09-08_p6-*.json` |

### What "Parle" actually returns

A real amazon.in Parle-G 800 g listing (`eval/dataset/ecom_amazon_parle_g_800g`) was pushed
through the hosted worker as scan `cddac6b6`. It finished `done`, score 75, filed under the
product **Parle Biscuits Pvt Ltd**, and `/scans?q=Parle` returns it — through the product, not
through the note it was uploaded with.

Getting there took a fourth item that is really P2's. The listing prints
`Manufacturer : Parle Biscuits Pvt Ltd` and a bare "Manufacturer" was not an anchor, so nothing
was ever extracted to match on. That anchor had been tried once before and reverted
(`p2-real-listing-labels`: flat, three more false positives), and `p6-manufacturer-anchor`
reproduced that verdict exactly — the anchor alone is worth nothing. It pays with two rules
beside it: a screenshot's next line is the next row of the specification table and not the rest
of an address (it was finding the maker all along and swallowing `ASIN …` behind it), and a bare
noun is a label only where a label stands, at the start of the box (`From the manufacturer` and
`Is Discontinued By Manufacturer : No` both print above the real row). 62.2% → 62.5%, real
29.8% → 30.5%, violations untouched. Full accounting in `docs/EVAL.md`.

### Evidence and notes: what was reused, and what the viewer is refused

Nothing new authorises a file. The `evidence` table, its four RLS policies and the private
`scans` bucket all date from `0001_init.sql`; evidence photographs sit beside the pack photos and
the report at `<scan id>/evidence/<evidence id>.jpg` and are handed out as the same short-lived
signed URLs the report downloads use. `0004` adds only what was missing: the `scan_id` index every
other child of `scans` already had, and a check constraint saying a row must carry a photograph or
a note. The note is `scans.notes` — a column since P1, which `report.py` already prints as
"Inspector's notes", so P5 needed no change at all.

Evidence is deliberately **not** a `scan_images` row with `kind = 'evidence'`. The worker
downloads every `scan_images` row and re-reads it, so evidence filed there would change the score
of a scan that has already been reported on.

Verified on the hosted project with real sessions and the anon key, so the policies themselves are
what refuse — 13 checks, all passing:

| As | Check |
|---|---|
| inspector | two photos attached to a finished scan, each with its own object under `<scan>/evidence/` |
| inspector | rows carry the scan, the path and the author |
| inspector | the note saved and read back |
| inspector | **the scan result is untouched** — score still 75, 7 declarations, 1 violation |
| inspector | a row with neither photo nor note is refused by `evidence_carries_something` |
| inspector | both signed URLs serve `image/jpeg`, HTTP 200 |
| anyone | the same object without a token is HTTP 400 — the bucket is not public |
| viewer | can read the evidence rows and open a signed URL |
| viewer | **cannot** insert evidence — refused by RLS |
| viewer | **cannot** change the note — 0 rows updated, note unchanged |
| viewer | **cannot** upload to the bucket — `StorageApiError` |

The scan page was then opened in a browser as both roles: the inspector sees a textarea, a Save
button and an Add-evidence button; the viewer sees the note as text and neither button.

### A bug only the browser found, again

`ScanEvidencePhotos` is a client component and it formatted its dates with `toLocaleString()`.
The server rendered "2:29:18 pm" and the browser re-rendered "2:29:18 PM", and React failed
hydration over the difference — the whole page fell back to a client render, with a console error
and no test anywhere to catch it. The date is now formatted once, on the server, and passed in as
a string. Same lesson as P5's `scan-evidence.tsx` crash: typecheck, build and 534 tests all pass
either way.

### The matcher's known ceiling

Two words of the company, four of the generic name, both normalised. Two photographs of one pack
that disagree about more than punctuation, the legal form or the label will make two products
rather than one wrong one. Duplicates are visible in the repository and mergeable; a wrong merge
is not. Fuzzy matching is the upgrade if it ever becomes a nuisance.

## P7 — dashboard + roles + audit

**Done when:** viewer cannot upload; admin sees everything. **True**, and proved against the
hosted project rather than inferred from the UI code.

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | Dashboard: scans this week, compliance rate, top 5 violations, by category, recent scans | done | [dashboard/page.tsx](frontend/app/dashboard/page.tsx) over `dashboard_summary`, `top_violations`, `scans_by_category`, `dashboard_recent_scans` in `0005`; week maths in [dashboard.ts](frontend/lib/dashboard.ts) with 10 checks in [dashboard.test.ts](frontend/lib/dashboard.test.ts) |
| 2 | Roles enforced in UI, verified against RLS | done | [roles.ts](frontend/lib/roles.ts) + 6 checks in [roles.test.ts](frontend/lib/roles.test.ts), [upload/layout.tsx](frontend/app/upload/layout.tsx), [nav.tsx](frontend/components/nav.tsx). Hosted proof: [check_rls.py](supabase/check_rls.py), 53 checks, `make check-rls` |
| 3 | Audit triggers on scans / products / evidence | done | `public.audit()` and three triggers in `0005_dashboard_roles_audit.sql`; 11 hosted checks inside `check_rls.py` |
| 4 | Rule catalogue for the dashboard's rule names | done | `public.rules` in `0005`, `sync_rules` in [main.py](worker/main.py), 3 checks in [test_sync_rules.py](worker/tests/test_sync_rules.py). 23 rules synced to the hosted project |
| 5 | `security definer` functions taken off the public API | done | `0006_lock_down_definer_functions.sql`, found by Supabase's security advisor |

### The dashboard, and where each number comes from

Nothing on the page is computed from a photograph. Six queries, five of them aggregated by
Postgres, all against `security_invoker` views so the caller's RLS decides which scans are in the
totals:

| Card | Source | Definition |
|---|---|---|
| Scans this week | `scans` count, `created_at >= weekStart(now)` | Monday 00:00 Asia/Kolkata |
| Compliance rate | `dashboard_summary` | `status = 'done' and compliance_score = 100`, over `status = 'done'` |
| Average score | `dashboard_summary` | `avg(compliance_score)` over finished scans |
| Violations found | `dashboard_summary` | counts by severity; `info` is excluded everywhere, so notes and `unverifiable` checks never appear |
| Most common violations | `top_violations` | grouped by rule, left-joined to `public.rules` for the title |
| By category | `scans_by_category` | `group by products.category`, **null left as null** |
| Recent scans | `dashboard_recent_scans` | one row per scan with its violation counts already added up |
| Recent activity | `audit_log` | admin only, and the RLS policy says so too |

Read back from the hosted project on 2026-09-08 and checked against the tables by hand: 4 scans,
scores 75 / 87 / 25 / 87 → average **68.5**; none scored 100, so the compliance rate is **0%** and
not a blank; 4 scans since Monday; 8 violations that cost points (4 critical, 2 major, 2 minor);
D2 and D8 twice each, D1, D3 and D5 once. Every product in the project has `category = null`, so
the category panel shows one row reading *Category not recorded*, in italics, and no bucket is
invented for it.

**A failed scan is not a compliant scan.** `score([])` is 100 by construction, so this is the one
sum that must not be got wrong. Proved on the hosted project rather than argued: two rows are
inserted — one `done` with 100, one `failed` — and the deltas on `dashboard_summary` are
`+1 failed, +1 done, +1 compliant, +2 total`. Both rows are then deleted and every total returns
to what it was.

### Roles: what was checked, and against what

The nav hides Upload from a viewer, `app/upload/layout.tsx` redirects one who types the URL, and
neither is the security boundary. `supabase/check_rls.py` signs in as all three demo users with
the anon key and goes straight at PostgREST and Storage — **53 checks, all passing**:

| As | Checks | Result |
|---|---|---|
| inspector | insert a scan, upload to the bucket, add evidence, edit the note on their own scan | all allowed — P1 and P6 intact |
| inspector | edit somebody else's scan, delete any scan, read the audit log | all refused |
| viewer | insert a scan; insert a scan as somebody else; upload to the bucket; attach an image; add evidence; edit a note; change a compliance score; delete a scan; insert a product; rename a product; promote themselves to admin; edit somebody else's evidence; delete somebody else's evidence | **13 writes, 13 refused** — `new row violates row-level security policy` on the inserts, `0 rows affected` on the updates and deletes |
| viewer | read scans, read the dashboard | allowed — a viewer is still for something |
| viewer | the scan and its evidence afterwards | byte-identical; no audit entry anywhere has the viewer as actor |
| viewer / inspector | read `audit_log` | 0 rows, both |
| admin | all four dashboard views, every profile, the audit log, at least what a viewer sees | all allowed |

In the browser, as all three demo users, at 375 px and 1280 px: the viewer's nav has no Upload
link and `/upload` lands on `/scans`; the inspector's nav has it and the form renders; the admin
sees a *Recent activity* panel that neither other role is shown. On the scan page the viewer gets
the note as plain text with no Save button and no Add-evidence button, which is P6's behaviour
unchanged.

### Audit: written by the database, and proved by a write that skips the app

One `public.audit()` trigger function, three triggers. `security definer` so it can write a table
that has no insert policy — nobody may forge their own audit row. Verified on the hosted project:

| Check | Result |
|---|---|
| scan INSERT | recorded, whole new row stored, actor is the inspector's user id |
| scan UPDATE | recorded as `{"notes": null} → {"notes": "inspector note"}` — the changed key only, both sides |
| scan DELETE | recorded, whole old row stored, actor is the admin who deleted it |
| evidence INSERT and the cascaded DELETE | both recorded |
| product INSERT / UPDATE / DELETE **with the service-role key** | all three recorded, `actor_id` null |
| timestamp | populated on every entry |
| `audit_log` auditing itself | 0 rows, ever |
| anything the viewer attempted | 0 rows |

The product row is the important one: it is written with the service-role key, which never touches
a browser and bypasses RLS, and the trigger fires anyway. The audit does not depend on the
frontend, and a null actor is the honest record of a write by the worker.

### Two bugs the tests did not catch

**The check script edited a real inspection note.** Its "an inspector cannot edit somebody else's
scan" case picked the oldest scan in the project to fail against, and that scan belonged to the
inspector, so the update succeeded and overwrote scan `5e0811b8`'s note with "not mine". Nothing
failed loudly; one assertion further down went red for a reason that looked unrelated. `audit_log`
had the old value and the note was restored from it. The script now creates every row it touches
— including a second scan owned by the admin — and deletes them at the end.

**The new trigger function was on the public API.** Supabase's security advisor flagged
`public.audit()` as callable at `/rest/v1/rpc/audit` by anyone with the anon key, because a
`security definer` function in the `public` schema is exposed by default. Calling it raises rather
than writing anything, but `0006` revokes it, and `auth_role()` and `handle_new_user()` with it.
`auth_role()` needed care: every RLS policy calls it and a policy runs as the signed-in user, so
the blanket PUBLIC grant comes off and an explicit grant goes back to `authenticated`. Re-checked
afterwards — 53 RLS checks, a fresh auth user still getting a profile, `claim_scan` still
returning.

### Known and accepted

- **Every product has `category = null`.** Nothing on an Indian pack declares a category and the
  worker does not guess one, so the category panel has exactly one row. That row says *Category
  not recorded* and the number beside it is real. A category would have to come from the inspector
  or from a catalogue; neither is in this phase.
- **`auth_role()` is still callable by `authenticated`, on purpose.** It is the last remaining
  advisor warning of its class. It returns the caller's own role and every RLS policy depends on
  it, so it cannot be revoked from the role that needs it.
- **Leaked-password protection is off** on the hosted project. That is a switch in the Supabase
  Auth dashboard, not code, and it is the account owner's to flip.
- **Pre-existing performance findings were read and left alone.** Five unindexed foreign keys from
  `0001` and `auth.<fn>()` re-evaluated per row in seven P1 policies. Both matter at scale, neither
  matters at four scans, and rewriting seven RLS policies inside the phase whose job is to prove
  those policies work is the wrong trade. `dashboard_recent_scans` plans as a hash join in 0.65 ms.
- **`audit_log` carries the check runs.** 62 entries, mostly rows the script created and removed.
  An audit log that gets tidied is not one, and the entries are exactly what the admin panel is
  there to show.

## P8–P9

Not started. See `docs/PLAN.md` for the item list and the "done when" line of each phase.
P8's first item is already done — it landed in P3.

---

## Log

- **2026-09-08** — **P7 finished: dashboard, roles, audit.** Built on what was already there: the
  `audit_log` table, the three roles and the RLS policies all date from `0001`, and `0005` adds the
  values, the triggers and the views rather than a second permission system beside them.
  The dashboard reads back and never recomputes. Compliant means `compliance_score = 100` — the
  score the worker stored and the PDF prints — replacing P1's view, which said "no critical or
  major violation" and so disagreed with both. A failed scan is in neither half of the fraction,
  which matters because `score([])` is 100 by construction; proved on the hosted project by
  inserting one `done`/100 and one `failed` row and reading the deltas.
  "This week" is Monday 00:00 Asia/Kolkata, in one tested function rather than a `date_trunc` in a
  view: the reports print UTC because a report timestamps an event, but a week cut at 00:00 UTC
  throws an Indian inspector's Monday dawn into last week. Six boundary tests.
  Rule names on the dashboard come from `rules/pc_rules_2011.yaml` through `public.rules`, which
  the worker mirrors at start up. A migration full of titles would have been the second copy of the
  law in this repo and a TSX map the third.
  Roles: the nav hides Upload, a server layout redirects a viewer who types `/upload`, and neither
  is the boundary. `supabase/check_rls.py` signs in as all three demo users with the anon key and
  attacks PostgREST and Storage directly — 53 checks, 13 of them writes a viewer must be refused,
  all refused, with the scan and its evidence byte-identical afterwards. `make check-rls`.
  Audit is three triggers on the tables, so a write with the service-role key — no browser, no RLS
  — is recorded exactly like one from the app, with a null actor. An UPDATE stores only the keys
  that changed, both sides. Nothing audits `audit_log`.
  Two things the green suite could not have found. The first check script picked a real scan to
  attack and overwrote an inspection note; `audit_log` held the old value to restore from, before
  the phase that added it was even finished. And Supabase's security advisor found that the new
  `security definer` trigger function was callable at `/rest/v1/rpc/audit` by anyone with the anon
  key — `0006` revokes it and the two of its class that predate P7, taking care over `auth_role()`,
  which every RLS policy calls and which therefore needs an explicit grant back to `authenticated`.
  `make test` 524 + 29 passed · `make lint` clean · `make check-rls` 53/53 · `tsc --noEmit`,
  `pnpm lint`, `pnpm build` clean · browser checked as all three roles at 375, 768 and 1280 px.

- **2026-09-08** — **P6 finished: evidence photographs and the inspector's note.** Both were built
  out of what P1 already put there. The `evidence` table, its RLS and the private bucket needed no
  change; a photo goes to `<scan id>/evidence/<id>.jpg` in the same bucket as the pack photos and
  the report, and is read back through the same signed URLs, so there is no second way to
  authorise a file anywhere in the app. The note is `scans.notes`, which `report.py` has printed
  as "Inspector's notes" since P5 — nothing in the report was touched. `0004` adds an index and a
  check constraint and nothing else.
  The decision worth writing down is what evidence is **not**: a `scan_images` row with
  `kind = 'evidence'`. The worker re-reads every `scan_images` row, so evidence filed there would
  change the score of a scan already reported on. Evidence is a separate table and the upload path
  never touches the scan; the note is written as a one-key patch built by `notesPatch`, which a
  test pins, and the hosted run confirms the score, the declarations and the violations are all
  unchanged afterwards.
  All the deciding lives in `frontend/lib/evidence.ts` as plain functions, so it is testable
  without a browser — 13 checks under node's own test runner, no test framework added to the
  dependency list (`node --test --experimental-strip-types`, wired into `make test`). RLS is not
  pretended to be testable from there: it was exercised against the hosted project with a real
  inspector session and a real viewer session, 13 more checks, four of which are refusals.
  Opening the page found the one bug the suite could not: a client component formatting a date
  with `toLocaleString()` renders "pm" on the server and "PM" in the browser, and React failed
  hydration on it. Fixed by formatting on the server.
  `make test` 521 + 13 passed · `make lint` clean · `tsc --noEmit`, `pnpm lint`, `pnpm build` clean.

- **2026-09-08** — **P6: the anchor that was rejected once, and why it works now.** "Search Parle
  returns its scans" needed a Parle scan with a maker on it, and no e-commerce listing had one:
  they label the field `Manufacturer :`, and the bare noun was not an anchor. It had been tried in
  P2 and reverted for being flat with three extra false positives, and retrying it reproduced that
  almost to the number — flat, four extra. The result files did their job: they said *the anchor is
  not the missing piece*. What was missing sat either side of it. A screenshot's next line is the
  next row of the specification table, so the extractor had been finding
  `Manufacturer : Parle Biscuits Pvt Ltd` all along and then swallowing `ASIN B0754HP7X2` behind
  it — turning off the address wrap for `source = ecommerce` took the real half 29.8% → 30.5%. And
  a bare noun is a label only where a label stands, at the start of the box: `From the
  manufacturer` is an Amazon heading, `Is Discontinued By Manufacturer : No` is a different row,
  and both print above the real one. That last run moved no number at all and is kept anyway,
  because it changed the Tata Salt answer from "Is Discontinued By Manufacturer : No" to a
  company. Manufacturer precision fell 0.478 → 0.44 while recall rose 0.379 → 0.414 — three
  listings moved from finding nothing to finding the company but not the exact gold string, which
  is a trade worth making here, because `company_key` reads the first two words after the label
  and files the scan correctly on a near miss. Violations untouched on all three runs. Scan
  `cddac6b6` now sits under **Parle Biscuits Pvt Ltd** on the hosted project.

- **2026-09-08** — **P6: a scan is filed under a pack, and the repository is searchable.** The
  identity is `products.match_key`, two words of the maker and four of the generic name, and it
  is a unique index the worker upserts on, so "is this the same product" is answered by Postgres
  rather than by a similarity score. The two rules that matter are both refusals: a pack that
  declares no maker gets no product (that is D1, and inventing one puts another company's scans
  in its history), and nothing but the pack's own declarations decides the match.
  **Reading the real data changed the code twice.** Written against the gold files, `company_key`
  cut the company at the first comma — and the Reynolds pen on the hosted project prints
  "Manufactured,Marketed and Brand Owned by", a comma *inside the label*, so the key came out
  empty and the pack had no identity at all. Then the same pack, photographed twice, produced
  "…Private Limited, Plot No. C-21" and "…Private Limited Plot No. C-21": the comma that ends a
  company name is the first thing a photograph loses, which is why the key keeps two words and
  not four. Both readings now land on one product, and `/products/<id>` shows both scans and
  their average. Search is a single `scan_search` view — product, brand, maker, category,
  inspector, place, note and scan id concatenated into one column, `ilike` over it,
  `security_invoker` so RLS still applies.
  `make test` 518 passed, `make lint` clean, `tsc --noEmit` and `pnpm build` clean, and the two
  pages were opened in a browser against the hosted project rather than trusted to typecheck.

- **2026-09-08** — **P5: the report is one model rendered three ways.** `build_report` turns a
  finished scan into a `Report`, and the JSON, the PDF and the DOCX are three renderings of it —
  so the three files cannot disagree about the same pack, which is the only thing a compliance
  document must never do. The score is read, never recomputed, and a test pins that by handing the
  builder a result whose score has been overwritten. Every applied rule lands in exactly one of
  four lists: **violation** (cost points), **note** (`info` — food law, a medical-device flag, a
  Rule 26 exemption), **not verifiable** (says why, costs nothing), **passed**. That last one
  needed `applicable_rules` in the engine, because a rule that raised nothing is otherwise
  indistinguishable from one Rule 6(10) never applied; the eval run proves the refactor moved
  nothing — `2026-09-08_p5-reports.json` is identical on every key to `p4-marker-cases`.
  **Rendering it and looking at it found three bugs no test had:** Jinja's autoescape was turning
  the inlined Lucide icons into paragraphs of angle brackets, the running footer was clipped
  mid-word because a margin box only gets half the page, and a portrait phone photograph is taller
  than a page can hold under its own heading — five pages became four. The fonts and icons are
  vendored (IBM Plex Sans, SIL OFL 1.1; Lucide, ISC) so nothing is fetched while a report renders,
  and IBM Plex carries ₹, which the penalty footer needs. No emblem or crest — the masthead is a
  balance scale. `make test` 501 passed, `make lint` clean, `tsc --noEmit` and `pnpm build` clean.
  WeasyPrint needs GTK, which Windows does not ship; the runtime is installed on the dev machine
  and `WEASYPRINT_DLL_DIRECTORIES` is documented, and where it is missing the PDF is stored as
  null while the JSON and DOCX still go up.

  One real scan went through the hosted project end to end — scan `3f5b8e1e`, queued → `done`,
  score 87, three files in Storage at the right paths and MIME types — and then the detail page
  was opened in a browser for the first time in this project's life and **crashed**:
  `scan-evidence.tsx` read `e.currentTarget.naturalWidth` inside a `setState` updater, which React
  runs after it has cleared `currentTarget`. It typechecked, it built, and 500 tests said nothing.
  Fixed, and then all three signed download URLs were fetched from the page: 200, right content
  types, right byte counts. The pre-P5 scan `7f7eb986` correctly shows "No report was written for
  this scan."

- **2026-09-08** — **P4: print size and contrast are measured, or honestly refused.** A scale per
  photograph (ArUco → card → the inspector's panel width → none), the print measured inside each
  OCR box rather than the box itself, and F1/F2/P2 live. Seven labelled runs, three of them
  corrections the eval forced: the card detector was claiming a scale in **14 frames with no card
  in them**, so it is now gated on the inspector's own answer; contrast on brightness alone called
  **27 of 27 real photographs** low-contrast, and after two improvements to the estimator 54% were
  still under the floor, so P2 joined F1 and F2 behind a scale reference — the crops behind the
  worst readings are a shadow on a bottle and pale but perfectly legible print, which is the light
  and not the pack; and the glyph-height percentile was reading a lower-case line 28% short.
  Violation precision ends where it started at 0.74, exact-set accuracy 48.1% → 50.0%, extraction
  untouched. Two rendered cases with a 50 mm marker give the font path a live test, where the
  pipeline recovers 0.1253 mm/px against a true 0.1250. On the way, the P0 test suite caught a
  real bug in P3's code: Table I's last row held an embossed numeral to 6 mm where the law says 8.
  **What is still missing is a photograph with a card in it** — no amount of rendering substitutes
  for glare and perspective.

- **2026-09-08** — **The extractor can read a printed declarations table.** A real scan showed
  a pack whose declarations are a bordered two-column table, a layout no case in the web set has,
  and the extractor read none of its values. The pack went into `eval/dataset` first, then six
  labelled runs: reach into the table cell as a last resort and as a second pass, merge the label
  cell's wrapped second line, allow a centred continuation block, and one more anchor. Real
  accuracy 28.4% -> 29.8%, violation precision 0.71 -> 0.74, **7 fewer false accusations and no
  new misses** across 54 cases. Three further attempts were measured and thrown away, including
  two ways of loosening the row test that each cost 1.5 points — the second of which read a
  barcode as a net weight.

- **2026-09-08** — **First look at the detail page, three fixes.** The worst was a scan showing
  **100 / 100** for a pen box the pipeline had never read a word of — `score([])` is 100 by
  construction and a pre-P2 stub had reached `done`. A scan with no OCR words is now `failed`
  with a message about re-shooting, guarded in `run_scan` so the report and the dashboard cannot
  inherit it later. Boxes now measure against the image the browser loaded rather than a stored
  column that can be wrong. A date label with no figure in it is a label, which stopped D4
  quoting "Manufactured,Marketed and" back at the inspector as a month and year. Two attempts to
  widen the same-row tolerance so a table cell two pixels out of reach would be found were both
  measured at real 28.9% → 27.4% and both reverted.

- **2026-09-08** — **P3 done.** All 20 checks written against the tests that were waiting for
  them; the 130 `xfail`s are gone and `make test` is 407 passed / 26 xfailed (the 26 are P4).
  Two new tests: one pinning that a screenshot is judged only by Rule 6(10), and one running the
  engine over every `eval/dataset` gold file's declarations and comparing the verdict to gold.
  The second one earned its keep immediately — it disagreed with
  `obf_muuchstac_.../gold.json`, and enlarging the photograph showed the gold was wrong, not the
  engine: the pack does print "MRP ₹ (Incl. of all taxes)", with the phone's watermark over it.
  Three measured changes to the engine, each its own labelled eval run: on an e-commerce scan
  only Rule 6(10) applies; D5's rupee marker is `unverifiable` rather than a failure, because no
  OCR model can emit ₹; and P1 can pass but not fail, because two photographs are not two panels.
  Violation precision 0.67 → 0.73, exact-set accuracy 28.3% → 49.1%, extraction untouched.
  What is left in the violation error is extraction, not rules, and that is measured rather than
  asserted. The detail page draws a box round every declaration on the photo and turns a
  violation's evidence boxes red when it is picked; it builds clean but has not been looked at in
  a browser, which needs a login.

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
