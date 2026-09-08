# EVAL — how this project knows whether it works

`CLAUDE.md` says: *test set first, baseline first, one variable at a time, nothing is done until
measured.* This file is how that is actually done. `docs/PROGRESS.md` holds the numbers each run
produced; this file holds the method.

---

## The short version

```bash
cd worker && uv run --extra ocr python ../eval/run_eval.py --label what-i-changed
```

Prints per-field precision/recall, an accuracy split into real photographs and rendered labels,
and violation accuracy. Writes `eval/results/<date>_<label>.json`, which is **committed**. A
measurement nobody can look up is not a measurement.

One change per run. The label says what changed. If a run scores worse, the change is reverted
and the result file stays — four hypotheses have been rejected that way so far, and they are the
most useful entries in the record because they stop the next person re-trying them.

---

## What the numbers mean

| Number | Definition |
|---|---|
| per-field **precision** | of the declarations the pipeline reported for this field, how many matched gold |
| per-field **recall** | of the declarations gold says are there, how many the pipeline found |
| **field extraction accuracy** | true positives ÷ all gold declarations, over every case |
| **real / synthetic** | the same figure computed over the photographs and over the rendered labels separately |
| **violation precision / recall** | non-`info` rule codes, predicted against gold |
| **exact-set accuracy** | the fraction of cases where the predicted violation set equals gold exactly |

Read the real and synthetic lines, not the combined one. A rendered PNG and a phone photograph
are different problems, and the combined figure moves when the mix changes rather than when the
pipeline does. On 2026-09-07 the combined 60.0% was 98.2% synthetic and 28.9% real.

Violation numbers are 0 until P3: `run_local` catches `NotImplementedError` from the rule engine
and scores 100.

### Matching is deliberately loose

A prediction counts as correct when `norm(prediction) == norm(gold)`, where `norm` casefolds,
drops punctuation and **all** spacing, and folds the currency marker. Three of those are there
because the strict version was measuring something other than extraction:

- **the rupee sign** — no PP-OCR dictionary contains `₹` (all 56 checked), so no model it ships
  can emit one. Comparing on it failed every price line identically and measured the dictionary.
- **a dot that is not between digits** — `eval/dataset/README.md` says punctuation is ignored, and
  keeping the dot failed `MIDC. Pune 411019`, an address that was otherwise word for word right.
  A dot *between* digits is a decimal point and still has to match.
- **spacing** — the README said spacing was ignored, but collapsing runs of spaces is not ignoring
  them: gold `NET WEIGHT 64 g` failed a correct read of `NET WEIGHT 64g`, because PP-OCR does not
  put a space back where the print had one.

- **accents** (2026-09-08) — the English recognition model has no `ñ` or `É` to emit, so gold
  `España` against a faithful read of `Espana` measured the dictionary. NFKD, combining marks
  dropped. One field moved.

Each of those was its own labelled run with the argument written down in the `docs/PLAN.md`
Decisions log, because loosening a metric is the easiest way to fake progress and has to be
defended in public. None of them can make two different values compare equal: `1C g` and `10 g`
stay different.

---

## The dataset

56 cases in `eval/dataset/`, one folder each.

| Prefix | What | How many | Source |
|---|---|---|---|
| `off_` | Indian food packs | 26 | Open Food Facts, CC-BY-SA 3.0 |
| `obf_` | Indian cosmetics and personal care | 5 | Open Beauty Facts, CC-BY-SA 3.0 |
| `ecom_` | product listings | 6 | amazon.in, flipkart.com, headless Chrome |
| `phone_` | shot for this project through the app | 1 | ours |
| `synthetic_` | rendered labels | 18 | `eval/make_synthetic.py` |

Two of the rendered labels carry a 50 mm ArUco marker at a known 8 px per millimetre. They are
the only cases with a scale, and therefore the only ones where the font and contrast checks do
anything but report "not verifiable" — see `eval/dataset/README.md`. A rendered marker is not a
photographed one, so the shot list is still open.

The real cases are **photographs other people took**: thumbs in frame, glare, packs held
sideways, panels half out of the crop. That unevenness is the point — a rendered label is not a
phone photo, and the two accuracy figures differ by 69 points because of it.

`eval/dataset/README.md` is the contract for a case folder and for `gold.json`. The rules that
matter most:

- **Gold is written by reading the photograph.** Never by running the pipeline. Gold derived from
  OCR would measure nothing.
- **Gold describes the images in the folder, not the pack they came from.** If the MRP is printed
  on a panel nobody photographed, the MRP is absent and the expected violation is the one an
  inspector would really get from that upload.
- **A declaration that is present but cut off by the frame counts as absent.** The evidence has to
  be legible or there is nothing to cite.
- Include declarations that no keyword anchors — a bare `SPICED BUTTERMILK` as the generic name.
  The benchmark is the pack, not the extractor's reach.

### Rebuilding it

```bash
cd worker && uv run python ../eval/fetch_openfoodfacts.py --host food   --count 60
cd worker && uv run python ../eval/fetch_openfoodfacts.py --host beauty --count 12
cd worker && uv run python ../eval/fetch_ecommerce.py                      # needs Chrome or Edge
```

Both scripts only download images. Writing `gold.json` is the human part and is the reason the
set is 37 real cases and not 117: every candidate whose photos showed no legible Legal Metrology
declaration was deleted rather than given a gold file with nothing in it.

`eval/fetch_ecommerce.py` discards any capture under two tiles — a listing runs past one screen,
so one short page is a 404 or a bot block, and storing it would fix a block page as a test image.
BigBasket and JioMart refuse headless Chrome; Amazon and Flipkart do not.

### Adding a case by hand

1. `eval/dataset/<case>/` with the photos named so they sort in reading order (`0_front.jpg`, …).
2. `gold.json` written from the photographs, following `eval/dataset/README.md`.
3. `make test` — `worker/tests/test_dataset.py` checks every gold file for canonical field names,
   real rule codes, `info`-severity codes that could never be matched, duplicates, unknown
   `ScanContext` keys and a missing image. A typo in a field name is otherwise invisible: it just
   scores as a permanent miss.
4. `make eval LABEL=…`.

### What the dataset cannot test

No photograph on Open Food Facts has an ArUco marker or a credit card in frame, and its crops
rarely show two panels at once. So **F1, F2** (font size and width), **P1** (grouping), **P3**
(seam) and **D5b** (two MRPs on one pack) have no real case and never appear in gold. Without a
scale they are `unverifiable` and cost no points, which is correct behaviour but not a test of
them. Those photos still need a person with a phone and a reference card; the shot list is at the
bottom of `eval/dataset/README.md`.

---

## The OCR cache

PaddleOCR on the real set is about 15 s a case. Without a cache, one labelled run costs an hour
and "one variable at a time" stops being affordable, so the boxes are memoised under
`eval/.ocr_cache/` (gitignored) keyed on:

```
absolute path | mtime | size | languages | sha256(preprocess.py + ocr.py)[:12]
```

Editing `preprocess.py` or `ocr.py` changes the fingerprint and the cache misses by itself. There
is no `--no-cache` flag to forget, and no way to accidentally measure an old pipeline. Changing
the extractor or the rules does **not** invalidate it, which is exactly the common case: a rerun
then takes about four minutes and measures the change.

`run_local` takes the OCR step as an argument to make this possible:

```python
def run_local(images, ctx, ocr: OcrFn = ocr_words) -> PipelineResult
```

Only the eval passes anything but the default. Changing OCR settings costs a full re-read of the
set — roughly 30 minutes with two processes; more than three at once ran the machine out of memory.

---

## Diagnosing a run

Three tools, none of which OCRs anything.

```bash
cd worker
uv run python ../eval/error_report.py ../eval/results/<run>.json
uv run python ../eval/compare.py ../eval/results/<before>.json ../eval/results/<after>.json
```

`error_report.py` is the one to read first. For every real case and every field gold or the
pipeline names, it writes the gold value, the OCR line that best covers it (with PP-OCR's own
confidence on that line — no other confidence exists in this system, and none is invented), the
final extracted value, and a failure category with the rule that assigned it, to
`<run>_errors.md` and `<run>_errors.json` beside the result file. The categories are measurable
things: under half the gold words anywhere in the OCR output is *OCR did not detect it*; the
gold carrying none of the field's label words is *printed with no label*; the words present but
the best single line holding under 90% of them is *read but not grouped*; a prediction 85%
similar to gold is *misread characters*; and so on. The counts by category and by field are at
the top. That table is what decided the order of the 2026-09-08 changes.

`compare.py` is how a labelled run is judged. Every per-field precision / recall / tp / fp / fn
delta, and every case whose value or violation set moved, marked **BETTER** / **WORSE** /
neutral against gold. A change that raises the accuracy line while adding false fields shows up
as WORSE rows beside the BETTER ones, and two of the nine changes below were reworked because
of a WORSE row before they were kept.

`eval/diagnose.py` reads the cache and never OCRs, so all of it is instant.

```bash
cd worker
uv run python ../eval/diagnose.py text   kinley                       # what PP-OCR read
uv run python ../eval/diagnose.py boxes  kinley 2_nutrition           # ...with coordinates
uv run python ../eval/diagnose.py misses ../eval/results/2026-09-07_p2-final.json
uv run python ../eval/diagnose.py reach  ../eval/results/2026-09-07_p2-final.json
```

`misses` prints gold against prediction for every field a run got wrong. It is how every one of
the extractor fixes was found: the anchor glued to its value, the price label pointing at the
bottle cap, the bare anchor taking a box from the row above.

`reach` is the more important one. It splits the misses in two — the words were in the OCR output
and the extractor did not use them, or PaddleOCR never read them at all:

```
field                extractor could   ocr never read it
generic_name                      18                   1
manufacturer                      12                   5
...
TOTAL                             85                  11
```

That is what says whether the next hour belongs in the extractor or in the OCR settings. **85 of
96** on the current state, which is why the work went into the extractor and why
`det_limit_side_len` was tried, measured and reverted rather than assumed to help.

---

## The record so far

Every run below has a file in `eval/results/`. Full table with the per-field numbers in
`docs/PROGRESS.md`.

The first group ran on a 48-case set and the second on the settled 53-case set, so the two groups
are not comparable to each other. Within a group, one variable changed per run.

| Run | Change | Result |
|---|---|---|
| `p2-real-baseline` | the real set as first assembled | 55.9% |
| `p2-real-continuations` | wrapped lines merged for **every** field | 51.4% — **reverted** |
| `p2-real-wrap-address-only` | merged only where the law prints an address block | 55.9% |
| `p2-real-anchors` | wordings taken off the packs; bare `origin` dropped | 56.8% |
| `p2-real-tighter-layout` | a bare anchor takes a box on its own row, in reach, that is not a declaration itself | 57.7% |
| `p2-real-det1600` | PP-OCR detects at 1600 px instead of 960 | 54.5% — **reverted** |
| `p2-real-glued-anchors` | an anchor may end against its value | 57.7% |
| `p2-real-ignore-spacing` | the comparison ignores spacing, as the README always said | 60.8% |
| `p2-real-number-guard` | a price or quantity label with no figure looks for the figure | 61.7% |
| `p2-real-cross-reference` | "SEE BOTTLE" / "SAME AS … ADDRESS" claims nothing | 61.7%, 11 fewer wrong claims |
| `p2-real-listing-labels` | `manufacturer` / `packer` anchors for listing tables | flat, 3 more false positives — **reverted** |
| `p2-real-final-baseline` | the extractor as it was **before** all of the above, on the settled set | 52.7% (real 18.5%) |
| `p2-real-final` | after all of the above | 58.4% (real 28.9%) |
| `p2-real-wrap-stops-at-pointer` | a wrapped address stops at a cross-reference line too | flat, better report text |
| `p2-real-clahe` | CLAHE on the lightness channel in `preprocess` | 60.0% (synthetic 94.5% → **98.2%**) |
| `p2-real-sideways-pass` | a second OCR pass at 90° when the boxes look like a sideways page | 59.6% (real 28.9% → 28.1%) — **reverted** |
| `p2-final` | the pipeline as it stands | **60.0%** — synthetic 98.2%, real 28.9% |

P4 and P5 ran on a 56-case set (the two marker cases joined it), so they are a third group.

| Run | Change | Result |
|---|---|---|
| `p4-marker-cases` | the two rendered marker cases join the set; nothing in the code changed | 62.2% (real 29.8%) |
| `p5-reports` | `run_rules` reworked to go through the new `applicable_rules`, which the report needs to list what passed | **62.2% (real 29.8%) — identical on every key** |
| `p6-manufacturer-anchor` | a bare `manufacturer` anchor, for the listings that label it that way | flat 62.2%, 4 more false positives — **on its own, no** |
| `p6-ecom-no-address-wrap` | …and a screenshot's next line is the next row of the table, never the rest of an address | 62.5% (real 30.5%), manufacturer recall 0.38 → 0.41 |
| `p6-bare-noun-anchor-must-start-the-box` | …and a bare noun is only a label where a label stands: at the start of the box | 62.5% (real 30.5%) — **no number moved, the answers did** |

### The audit round, 2026-09-08

Same 56 cases, same OCR cache. One variable per run; each run's `compare.py` output was read
before the next change was started.

| Run | Change | Real | Violations P / R / exact |
|---|---|---|---|
| `audit-baseline` | reproduces `p8-consumer-care-needs-a-contact` on every key | 30.5% | 0.741 / 0.986 / 51.8% |
| `p1-images-in-upload-order` | `run_scan` orders `scan_images`; the extractor keeps that order | 30.5% — identical | identical |
| `p2-padded-boxes-may-overlap` | a third of a line of slack for PP-OCR's padded boxes | 31.9% | 0.744 / 0.979 / 50.0% — a barcode passed as a price; **not kept alone** |
| `p2-a-figure-has-a-shape` | a price looks like a price, a date like a date; a bare label claims nothing | 31.9% | 0.745 / 0.986 / 51.8% |
| `p2-a-label-may-be-two-lines` | a label grows into a two-line cell; a figure is the value of one label | 35.5% | 0.757 / 0.993 / 53.6% |
| `p2-ocr-drops-spaces` | anchors survive dropped spaces; "usp", "date of mfg", "Quantity"@start | 36.9% | 0.770 / 0.993 / 53.6% |
| `p2-an-address-block-ends-at-the-licence-number` | licence, FSSAI and storage lines are not address lines; a care block keeps "same as … address" | 37.6% | 0.770 / 0.993 / 53.6% |
| `p2-the-fullest-address-block-wins` | address fields take the fullest candidate, whichever photograph came first | 39.0% | 0.770 / 0.993 / 53.6% |
| `p2-a-unit-price-by-its-shape` | an unlabelled "<amount> per <unit>" is the unit sale price | 42.6% | 0.774 / 0.993 / 53.6% |
| `p2-best-before-wraps-one-line` | "BEST BEFORE TWELVE MONTHS" / "FROM MANUFACTURE" | 43.3% | unchanged |
| `eval-accents-are-folded-like-the-rupee-sign` | measurement: NFKD | **44.0%** | unchanged |

Baseline to final: field accuracy 62.5% → 69.7%, real **30.5% → 44.0%** (43 → 62 of 141),
synthetic 98.4% unchanged, **26 fields better and 1 worse**, spurious predictions 13 → 6.

| Field | precision | recall |
|---|---|---|
| best_before | 0.69 → 1.00 | 0.69 → 0.76 |
| consumer_care | 0.81 → 0.74 | 0.59 → 0.59 |
| country_of_origin | 0.75 → 1.00 | 0.55 → 0.73 |
| generic_name | 0.95 → 0.95 | 0.47 → 0.47 |
| importer | 0.33 → 0.67 | 0.33 → 0.67 |
| manufacturer | 0.44 → 0.58 | 0.41 → 0.52 |
| mfg_date | 0.73 → 0.83 | 0.76 → 0.76 |
| mrp | 0.71 → 0.85 | 0.67 → 0.77 |
| net_quantity | 0.88 → 0.91 | 0.80 → 0.85 |
| unit_sale_price | 1.00 → 0.96 | 0.64 → 0.88 |

The two that fell: consumer_care precision, because two care blocks that were not read at all
before (Bisleri, KitKat) are now read with OCR errors in them — both D6 verdicts went from wrong
to right, which is the number that matters for that field; and unit_sale_price precision, one
unit price taken from the related-products carousel at the foot of an Amazon tile.

### The second round, 2026-09-08

Same 56 cases. Extractor runs on the audit's cache; OCR runs re-read the set (about 25 minutes
for one detection pass, twice that for two). One variable per run.

| Run | Change | Real | Violations P / R / exact |
|---|---|---|---|
| `p2-ocr-det-v4-mobile` | the PP-OCRv4 mobile detector **replaces** the English v3 one | 38.3% (synthetic 88.1%) | 0.732 / 0.979 / 39.3% — **rejected** |
| `p2-generic-name-by-head-noun` | an unlabelled line ending in a commodity head noun is the generic name | 48.9% | 0.837 / 0.917 / 58.9% — generic precision 0.50, **reworked** |
| `p2-generic-name-two-words-on-a-pack` | two to seven words, on a pack only, nutrition words refused | 49.6% | 0.828 / 0.966 / 60.7% |
| `p2-generic-name-is-not-a-list` | a comma makes it a list | 49.6% | 0.83 / 0.97 / 62.5% |
| `p2-best-before-wraps-two-lines` | a best-before sentence takes two digit-less lines | 49.6% | identical — **reverted** |
| `p2-sideways-geometry` | a box taller than wide is read with x and y swapped | **50.4%** | 0.83 / 0.97 / 62.5% |
| `p2-ocr-rec-server` | the PP-OCRv4 server recogniser | 42.6% (synthetic 78.6%) | 0.77 / 0.93 / 35.7% — **rejected** |
| `p2-generic-name-capitalises-every-word` | every word capitalised, no dot in the body | 50.4% | 0.827 / 0.986 / **64.3%** |
| `p2-ocr-full-res-pass-merged` | a second detection pass at 1600 px, merged: a box is added only if under 30% of its area lies under first-pass boxes | 50.4% | 0.84 / 0.97 / 64.3% — 1 better (Sprite "MADE IN INDIA"), 1 worse (Kinley's best-before lost its wrapped line to an added duplicate), 1 more spurious; 2× OCR time — **rejected** |
| `p2-ocr-v4-det-pass-merged` | the PP-OCRv4 mobile detector as a second pass, merged the same way | 51.1% | 0.83 / 0.98 / 64.3% — 1 better (the same Sprite "MADE IN INDIA"), 2 worse ("NET QUANTITY 45L" on a can whose gold expects D3, "MKT.BY PEDCIr"); 2× OCR time — **rejected** |

`p2-ocr-rec-server` started while the extractor file was mid-change (the first head-noun
version, with a regex bug), so its real-photo figure is confounded; its synthetic figure is the
recogniser's alone — it reads "I" as "l" and "0" as "o" on rendered text, "lnclusive", "MlDC" —
and that is disqualifying by itself. Its process also took 4.7 GB against the 3 GB worker budget.

Baseline to final: field accuracy 69.7% → 73.0%, real **44.0% → 50.4%** (62 → 71 of 141),
synthetic 98.4% unchanged, **9 fields better and 1 worse**, spurious predictions 6 → 7.
generic_name precision 0.95 → 0.77, recall 0.47 → 0.68; best_before recall 0.76 → 0.79; every
other field identical. The one worse is `off_coca_cola_sprite_8901764032707`, which prints
"CARBONATED WATER" on its own line above the ingredients and whose gold omits it.

The one field that got worse: the Ching's soy sauce use-by date. Its second photograph is
sideways, the label boxes are 60–90 px wide and 130–270 px tall, and in that geometry the
mfg-date label reaches the use-by's date first; once a figure could be the value of one label
only, the use-by lost it. A rotated page needs transposed geometry, which is a separate
experiment.

### P6: the same change, rejected in P2 and kept here

`p2-real-listing-labels` above is this same `manufacturer` anchor, tried in P2 and reverted for
being flat with three more false positives. `p6-manufacturer-anchor` retried it and reproduced
that result almost exactly — flat, four more false positives — so the P2 verdict was right about
the anchor **on its own**. What it was missing is the two things that make the anchor usable, and
neither is about wording:

1. On a listing the line under a declaration is the next row of the specification table, not the
   rest of an address. The anchor was finding `Manufacturer : Parle Biscuits Pvt Ltd` all along
   and then swallowing `ASIN B0754HP7X2` and `Item part number : 8901719102820` behind it.
2. `Manufacturer` is a noun, not a phrase, and a noun is only a label where a label stands — at
   the start of the box. Amazon prints `From the manufacturer` as a heading and
   `Is Discontinued By Manufacturer : No` as a row, both *above* the real one, and first box in
   reading order wins. The last run moved no number and changed the Tata Salt answer from
   "Is Discontinued By Manufacturer : No" to "Manufacturer : Tata Sampann"; it is kept for that,
   not for the score.

The three runs together buy 0.3 points overall and 0.7 on the real half, and they cost manufacturer
precision (0.478 → 0.44) while raising its recall (0.379 → 0.414): three listings moved from
"found nothing" to "found the company, not the exact gold string". Violations are untouched —
precision 0.74, recall 0.97, exact-set 46.4% on all three runs. The reason to keep a trade like
that is P6: `company_key` reads the first two words after the label, so a near-miss string still
files the scan under the right maker, and all four listings with a manufacturer now have one.

`p5-reports` is the only run in this file that was expected to change nothing, and that is what
it is for. The report has to say which checks *passed*, and a rule that raised nothing is
indistinguishable from a rule Rule 26 or Rule 6(10) never applied — so the applicability test had
to become a function the report could call. Deriving it a second time inside the report would put
two copies of Rule 6(10) in the repo. The run proves the extraction, the violations and the
per-case verdicts all came out byte for byte the same:

```python
a = json.load(open("eval/results/2026-09-08_p4-marker-cases.json"))
b = json.load(open("eval/results/2026-09-08_p5-reports.json"))
[k for k in a if k not in ("label", "date") and a[k] != b[k]]   # []
```

### The PP-OCRv5 experiment, 2026-09-08 — REJECTED

One controlled experiment, approved by the owner, to see whether the newer OCR stack moves the
OCR bottleneck (23 lines never detected, 10 misread). Everything else was held fixed: the same
56 cases and gold, the same harness, the same extractor and rules (commit `b1e05d8`), the same
`preprocess`. Only `worker/pipeline/ocr.py` changed, on branch `exp/pp-ocrv5`, in a separate
virtual environment so the committed 2.x worker and its `.venv` were never touched.

**Stack.** `paddleocr==3.7.0` (PaddleX 3.7.2) on `paddlepaddle==3.0.0`, Python 3.12, CPU.
`PaddleOCR(lang="en", ocr_version="PP-OCRv5", use_textline_orientation=True)`, which selects
`PP-OCRv5_server_det` + `en_PP-OCRv5_mobile_rec`; `lang="hi"` selects the same detector with
`devanagari_PP-OCRv5_mobile_rec`. Two configurations: the library's own defaults (detection at
full size — `limit_side_len 64 / min`), and detection shrunk to 960 px on the long side as the
2.x baseline does, so that only the models differ. Install:
`uv venv --python 3.12 <dir> && uv pip install -e worker paddlepaddle==3.0.0 paddleocr==3.7.0 setuptools`.

| Metric | Baseline (PaddleOCR 2.10, PP-OCRv4) | PP-OCRv5, defaults | PP-OCRv5, 960 px |
|---|---:|---:|---:|
| Real-photo field accuracy | **50.4%** (71/141) | **33.3%** (47/141) | **34.8%** (49/141) |
| Synthetic field accuracy | 98.4% (124/126) | 77.0% (97/126) | 77.0% (97/126) |
| Violation precision | 0.83 | 0.77 | 0.77 |
| Violation recall | 0.99 | 0.97 | 0.94 |
| Exact-set accuracy | 64.3% | 48.2% | 53.6% |
| Peak working set (152 images, one process) | 7.7 GB | 2.95 GB | 2.03 GB |
| OCR time per image, mean (real photographs) | 1.29 s (1.35 s) | 4.29 s (4.58 s) | 2.50 s (2.62 s) |
| First image incl. model load | 7.5 s | 14.6 s | 12.7 s |
| Lines detected, real photographs | 4,385 | 6,722 | 5,581 |
| Boxes taller than wide (sideways print), real | 70 | 100 | 100 |
| Baseline OCR misses recovered | — | 1 of 33 | 3 of 33 |
| Fields correct before, wrong after / newly correct | — | 55 / 4 | 54 / 5 |
| New false violations / true violations lost | — | 19 / 3 | 19 / 6 |

The 960 px configuration trades a little of each: fewer lines and less time, two more misses
recovered, six true violations lost, and two false physical violations (F2, P2) on the rendered
marker cases, whose measured glyph widths and contrast now come off different boxes. Neither
configuration is close to the baseline.

Result files: `2026-09-08_p2-ocr-pp-ocrv5-default.json`, `2026-09-08_p2-ocr-pp-ocrv5-det960.json`,
their `_errors.md`, and `2026-09-08_ocr-timing.json` (per-image seconds, lines, peak memory).

**Per field, baseline → PP-OCRv5 defaults (precision / recall):** best_before 1.00/0.79 →
0.84/0.72 · consumer_care 0.74/0.59 → 0.77/0.59 · country_of_origin 1.00/0.73 → 1.00/0.36 ·
generic_name 0.77/0.68 → 0.71/0.60 · importer 0.67/0.67 → 1.00/1.00 · manufacturer 0.58/0.52 →
0.57/0.55 · mfg_date 0.83/0.76 unchanged · **mrp 0.85/0.77 → 0.14/0.13** · net_quantity
0.91/0.85 → 0.79/0.72 · **unit_sale_price 0.96/0.88 → 0.12/0.12**.

**What PP-OCRv5 does read.** More: 53% more lines and 25% more characters on the real
photographs. The Bru sachet's marketer block and care block come back as whole lines
("MKTD. BY: HINDUSTAN UNILEVER LTD.", "PO BOX 14760, MUMBAI 400 099"), the Bisleri "MKT BY"
block is found, "Net Wt. 10 g" is read right. Of the 33 baseline OCR misses, 1 scores as
recovered (the Figaro manufacturer, "N-IV" for "N-1V"); for 18 more the words are now in the
OCR output but the extractor does not convert them (the error category moves from *never
detected* to *read but not grouped* 9, *wrong neighbour* 5, *unlabelled* 3, *wrapped* 1); 11
are still never detected (KitKat's "₹ 10/-", the Sprite and Thums Up quantities, the Kinley and
Maaza addresses, the soy sauce unit price) and 2 still misread.

**Why it scores worse.** Two things, and they are the model's, not the harness's.

1. **The rupee sign.** `en_PP-OCRv5_mobile_rec`'s dictionary contains ₹ (460 characters,
   checked in its `inference.yml`) and the model does not emit it: "MRP ₹20.00" reads
   "MRP 220.00", "₹11.25 /100 g" reads "211.25/100 g", "₹649" reads "7649", elsewhere "$", "&",
   "{". A digit glued to the amount is not a deletion the extractor can make safely, and it is
   not one this experiment was allowed to make. 42 price fields are wrong; 29 of them (25
   rendered labels, 4 photographs) would match gold with that one character removed. This is
   the whole of the synthetic collapse and almost none of the real-photo one.
2. **Boxes.** `PP-OCRv5_server_det` boxes single words wherever the print is large or widely
   spaced — "OZONISED | WATER | DRINKING", "Net | Wt. | 10 | 9" at full size; still "WATER |
   OZONISED | DRINKING" at 960 px — and merges label rows on tables differently. The extractor
   was built, and measured nine times, on "one box is one printed line"; 55 fields that were
   right under the 2.x boxes are wrong under these, and 19 false violations appear (D3 ×6,
   D2 ×4, D1 ×3, D5 ×3, D6 ×3) on 20 cases, against 3 true violations lost. That is the
   `det_limit_side_len=1600` rejection of 2026-09-07 again, now as the detector's own behaviour.

**Sideways print.** The transposed-geometry rule still works on PP-OCRv5's boxes: the soy
sauce use-by date is found under both stacks, and PP-OCRv5 returns more tall boxes (100 vs
70). Its date-of-manufacture on that pack absorbs "(incl. of all taxes)" as a label line, and
the Kinley best-before is lost to a split. **Bilingual packs:** `devanagari_PP-OCRv5_mobile_rec`
ran without error on both Devanagari cases; neither gained a field.

**Memory and time.** PP-OCRv5's process peaked at 2.95 GB over 152 images, inside the 3 GB
worker budget but with no headroom; the 2.x baseline process peaked at **7.7 GB** on the same
run — the 2.x predictor grows with every new image size it sees, which the worker will also do
over its lifetime and which P9 should measure. PP-OCRv5 is 3.3× slower per image on this CPU
(4.3 s against 1.3 s), so a four-photograph scan is about 18 s of OCR against 5 s.

**Compatibility, documented rather than fixed.** `paddleocr` 3.x is a different API: `ocr()`
is gone, `predict()` returns result objects (`rec_polys`, `rec_texts`, `rec_scores`);
`det_model_dir`, `det_limit_side_len`, `use_angle_cls` are renamed; models live under
`~/.paddlex/official_models`, not `~/.paddleocr` (P9's baking would move); a model-source
connectivity check runs at start unless `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK` is set;
PaddleOCR 3.7 defaults to **PP-OCRv6** when no version is given, so the version has to be
pinned; PaddleX pins `opencv-contrib-python`, which collides with the worker's `opencv-python`
until one is uninstalled (a broken `cv2` import until then); `paddlepaddle==3.0.0` worked, so
the 3.3 oneDNN failure that pinned it is not in the way. None of it is hard; all of it is a
migration, not a swap.

**Decision: REJECTED.** As shipped, PP-OCRv5 reads more of the print and scores 17 points
lower on the photographs and 21 on the rendered labels, because its recogniser writes a digit
for ₹ and its detector returns boxes the extractor was not built on. What an ADOPT path would
need, none of it done here: a rupee stand-in rule for a digit before an amount (a guess, not a
deletion — it needs measuring on its own), a box-to-line assembly step before the extractor
(the row merge that the 2.x server detector also needed), then the extractor re-measured
against the new boxes with its "one box, one line" assumptions revisited. That is the P2 work
again on a new footing, for a detector that does reach the small print. The 2.x implementation
stays as committed.

### The rejected hypotheses

Worth more than the accepted ones, because each closes off a plausible idea. Two more joined the
list on 2026-09-08, both PaddleOCR model swaps, numbers in the second-round table above: the
**PP-OCRv4 mobile detector as a replacement** boxes the clean labels differently and drops the
care line on nine of them, though it does find lines the v3 detector never returns (which is why
it was re-run as a merged second pass); and the **PP-OCRv4 server recogniser** reads "I" as "l"
and "0" as "o" on rendered print and takes 4.7 GB. The server *detector* was spot-checked on
five photographs and boxes single words on the bottles ("DRINI | NKING | WATER"), the same
line-splitting as hypothesis 1 below, so it was not run. The first four:

1. **Detect at full resolution** (`det_limit_side_len=1600`). PP-OCR shrinks a 1600 px photo to
   960 before detection, so raising it looks obviously right. It scored 54.5% against 57.7%:
   detecting at full size splits lines into more, smaller boxes, and "one box is one printed
   line" is the assumption the whole anchor extractor is built on.
2. **Merge continuation lines everywhere.** A wrapped address is one declaration, so merging looks
   obviously right — for addresses. `Net Qty: 200 g` and `MADE IN INDIA` are one line by
   construction and swallowed whatever was printed under them, costing 4.5 points. The rule now
   follows the law: an address block for `manufacturer` / `importer` / `consumer_care`, one line
   for everything else.
3. **Listing-table anchors** (`manufacturer`, `packer`). Amazon and Flipkart label the row
   `Manufacturer :`, which the anchor list did not cover. Adding it found nothing new and added
   three false positives.
4. **A second OCR pass at 90°.** Several packs in the set were photographed sideways and PP-OCR's
   `use_angle_cls` only fixes 180°. The trigger was "most boxes are taller than wide", which fires
   on panels that merely *contain* vertical text — a Coke bottle prints `MADE IN INDIA` sideways
   among horizontal lines — where rotating the page loses everything else. Real accuracy fell to
   28.1% and it doubles OCR time. Doing this properly means deciding orientation per box.

### The one that corrected an earlier conclusion

CLAHE. A 2026-09-07 decision had recorded the six remaining synthetic misses (`Bjscuits`,
`400o59`, `Net Qtv`) as "character-level recognition errors, nothing the extractor can reach; the
lever is a heavier recognition model". Equalising the lightness channel locally fixed four of
them. It was contrast, not the model. It moved the photographs by exactly zero, which also rules
out contrast as the reason PP-OCR misses whole lines on a curved bottle.

---

## Where the remaining gap is

Real photographs sit at 50.4% against a 70% target. The 70 misses, from
`eval/results/2026-09-08_p2-generic-name-capitalises-every-word_errors.md`, every one looked at:

| Cause | Misses | Reachable by the extractor? |
|---|---|---|
| **OCR did not detect the print** — under half the gold words are anywhere in the output | 23 (33%) | **No.** Small white print on the curve of a Bisleri, Kinley or Maaza bottle; the tilted Ching's jar, where the address lines under "MKT BY" were never detected; the Bru sachet, whose print is a dozen pixels high; KitKat's "₹ 10/-" read as "R10F"; sideways text. Legible to a person in every case. Only the OCR step can reach these, and the four OCR experiments of the second round did not (table above). |
| the words were read but the extractor did not group them | 15 (21%) | Partly. Half are consumer care blocks where the phone or e-mail line was not detected, so the block never carries the contact D6 needs; the rest are label and value columns that do not line up (Quaker's "79/-" sits a row above its "MRP"), a Flipkart pack shot read as garbage, and a date pair printed as one box under two labels (Bru). |
| the common name is printed with **no label to anchor on** | 12 (17%) | Was 20. The head noun reaches a printed line; what is left is a name PP-OCR glued or split (`PACKAGEDDRINKING WATERJOZONISED`, `TONED MILK` for `PASTEURISED HOMOGENISED TONED MILK`), never read (Jim Jam, Tata Salt), or read by the Devanagari model (Patanjali). OCR misses under a generic-name label. |
| character errors on the line used | 10 (14%) | **No.** `Net Wt.1 g` for `10 g`, `SlPCOT`, `PHASE-` for `PHASE-1`, `DELH-100`. Same class as `Bjscuits` on the rendered labels; the lever is the recognition model, and the one heavier recogniser PaddleOCR 2.x ships was measured and rejected. |
| the anchor took the wrong neighbour | 8 (11%) | Some. Two are the Amazon MRP convention (the listing's own "M.R.P" row against the displayed price gold chose); two are packs printing both a manufacturer and a marketer; the rest are sideways or tilted panels. |
| a wrapped value cut short or over-merged | 2 (3%) | Some. |

Spurious predictions are 7: the same two Amazon tiles as before (a price and a unit price from
the related-products carousel, a "Mfg. Date" the listing prints and gold omits), the Sprite's
printed "CARBONATED WATER", and a care block and two maker's addresses read off cut-off cans.

Two things follow. First, the extractor's remaining reach is now small in fact, not only in
the count: of the 70 misses, 33 are OCR failures, 12 more are OCR failures under a generic-name
label, and of the 25 left most are layouts that no rule short of a table reader resolves. The
transposed-geometry experiment has been run (+1). Second, the OCR bucket did not move under any
of the four experiments this project can make inside PaddleOCR 2.x: two model swaps (rejected on
the rendered labels), and two merged second passes (results in the table). What that bucket
wants is a recogniser that reads twelve-pixel Latin print better than `en_PP-OCRv4_rec`, which
is a model, not a setting — PP-OCRv5 under PaddleOCR 3.x is the candidate, and it is a
dependency change the owner decides. The Stretch item's VLM is still justified for the generic
name, for a bucket of 12 rather than 20, and still not for the OCR bucket: a VLM reading the same
1600 px photograph faces the same twelve-pixel print.
