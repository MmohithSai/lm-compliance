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

### The four rejected hypotheses

Worth more than the accepted ones, because each closes off a plausible idea:

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

Real photographs sit at 44.0% against a 70% target. The 79 misses, from
`eval/results/2026-09-08_eval-accents-are-folded-like-the-rupee-sign_errors.md`, every one
looked at:

| Cause | Misses | Reachable by the extractor? |
|---|---|---|
| **OCR did not detect the print** — under half the gold words are anywhere in the output | 23 (29%) | **No.** Small white print on the curve of a Bisleri, Kinley or Maaza bottle; the tilted Ching's jar, where the address lines under "MKT BY" were never detected; the Bru sachet, whose print is a dozen pixels high; KitKat's "₹ 10/-" read as "R10F"; sideways text. Legible to a person in every case. Only the OCR step can reach these. |
| the common name is printed with **no label to anchor on** | 20 (25%) | **No.** `SPICED BUTTERMILK`, `CARBONATED WATER`, `Lip Balm`, `Coated Wafer`, `AYURVEDIC PROPRIETARY MEDICINE`. 17 of the 21 generic_name misses. This is the case for the Stretch item. |
| the words were read but the extractor did not group them | 17 (22%) | Partly. Half are consumer care blocks where the phone or e-mail line was not detected, so the block never carries the contact D6 needs; the rest are sideways photographs, where the label / value geometry is transposed, and a Flipkart pack shot read as garbage. |
| character errors on the line used | 9 (11%) | **No.** `Net Wt.1 g` for `10 g`, `SlPCOT`, `PHASE-` for `PHASE-1`, `DELH-100`. Same class as `Bjscuits` on the rendered labels; the lever is the recognition model, not the extractor. |
| the anchor took the wrong neighbour | 8 (10%) | Some. Two are the Amazon MRP convention (the listing's own "M.R.P" row against the displayed price gold chose); two are packs printing both a manufacturer and a marketer; the rest are sideways or tilted panels. |
| a wrapped value cut short or over-merged | 2 (3%) | Some. |

Spurious predictions are down to 6, and four of those are the same two Amazon tiles: a price and
a unit price from the related-products carousel, and a "Mfg. Date" / "Exp. Date" pair the listing
really does print in its details table and gold omits.

Two things follow. First, the extractor's remaining reach is small: of the 79 misses, 32 are
OCR failures of one kind or another and 20 are structural, leaving about 27 the extractor could
in principle touch, most of them on sideways or tilted photographs. The next extractor-side
experiment is transposed geometry for a box that is taller than it is wide; the next OCR-side
experiment is a second detection pass at 90° merged with the upright one rather than replacing
it (the earlier rejection replaced), and a re-measurement of `det_limit_side_len=1600` now that
the extractor tolerates split lines better. Both cost a full re-OCR of the set.

Second, the structural bucket is the case for the Stretch item in `docs/PLAN.md` — a local VLM
extractor behind `EXTRACTOR=local_vlm`, measured against this same baseline and logged in
`model_calls`. `rules/pc_rules_2011.yaml` D2 requires the *common or generic name*, Indian packs
print it as a bare line, no amount of regex reaches that, and a hand-written list of product
categories would be fitted to this dataset rather than to the law. It is justified for that one
field. It is not justified for the OCR bucket: a VLM reading the same 1600 px photograph faces
the same twelve-pixel print, and that bucket wants a better detector, not a different reader.
