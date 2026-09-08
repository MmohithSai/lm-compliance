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

Real photographs sit at 28.9% against a 70% target. Counting the 96 misses:

| Cause | Misses | Reachable by the extractor? |
|---|---|---|
| the common name is printed with **no label to anchor on** | 23 | **No.** `SPICED BUTTERMILK`, `CARBONATED WATER`, `Lip Balm`, `Flavoured Sandwich Biscuits`. An anchor extractor has nothing to key on. |
| a wrapped address where PP-OCRv4 dropped a line | ~28 | Partly. The merge works; on a curved bottle one line of the address is never detected, so the block is never word for word. |
| the photograph itself lost it | ~14 | No. Thumb over the panel, pack held sideways, value column cropped out of frame. |
| recognition slips and wrong neighbours | ~31 | Some. |

The largest bucket is structural. `rules/pc_rules_2011.yaml` D2 requires the *common or generic
name*, and Indian packs routinely print it as a bare line with no `Generic name:` label. No amount
of regex reaches that, and a hand-written list of product categories would be fitted to this
dataset rather than to the law. This is the case for the Stretch item in `docs/PLAN.md` — a local
VLM extractor behind `EXTRACTOR=local_vlm`, measured against this same baseline and logged in
`model_calls`. It is the next thing to try, and the numbers above are the bar it has to clear.
