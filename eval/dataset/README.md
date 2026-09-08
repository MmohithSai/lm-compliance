# eval/dataset

One folder per case:

```
eval/dataset/off_parle_parle_g_biscuit_8901719134845/
  0_front.jpg          # any *.jpg / *.png / *.webp; sorted by name; first = front
  1_ingredients.jpg
  gold.json
  source.json          # where the photo came from and under what licence
```

`gold.json`:

```json
{
  "context": { "source": "package", "is_imported": false, "pdp_area_cm2": 180, "net_qty_g_or_ml": 200 },
  "declarations": {
    "manufacturer": "Mfd by: Parle Products Pvt Ltd, Vile Parle (East), Mumbai 400057",
    "generic_name": "Biscuits",
    "net_quantity": "Net Wt. 200 g",
    "mfg_date": "Mfd: 03/2026",
    "mrp": "MRP ₹20.00 Inclusive of all taxes",
    "consumer_care": "consumercare@parleproducts.com 1800-123-4567"
  },
  "violations": ["D8"]
}
```

## Writing gold

- `context` fields are `ScanContext` fields (`worker/pipeline/models.py`). Only what the inspector would know.
- `declarations` use the canonical field names from `CLAUDE.md`.
- **Gold describes the images in the folder, not the pack the images came from.** If the pack
  prints the MRP on a panel nobody photographed, the MRP is absent, and the expected violation
  is the one an inspector would get from that upload. That is the system's real input.
- **Gold is written by reading the photograph, never by running the pipeline.** Gold that came
  from OCR would measure nothing.
- **A value is the declaration as printed, with printed line breaks collapsed to one space.**
  A wrapped address is one declaration, not three. The extractor has to put the lines back
  together; that is a real part of the job, not a scoring convenience.
- Values are matched loosely: case, punctuation, spacing and the currency marker are ignored, so
  `₹20.00`, `Rs 20.00` and `20.00` are the same value (no PP-OCR dictionary contains a `₹`). A dot
  between digits is a decimal point and still has to match.
- If a declaration is genuinely absent, leave the field out — do not write an empty string.
- Include a declaration even when no keyword anchors it (a bare `SPICED BUTTERMILK` as the generic
  name). The benchmark is the pack, not the extractor's reach.

### How the expected `violations` were derived

Read off the declarations above plus the context, by the rules in `rules/pc_rules_2011.yaml`:

| Code | In gold when |
|---|---|
| D1 | no manufacturer / importer, or one without an address |
| D2 | no generic or common name |
| D3 | no net quantity, a non-standard unit, or a qualifier such as "approx" |
| D4 | no month and year of manufacture / packing / import, or a future one |
| D5 | the price line does not read MRP / Maximum Retail Price with an amount and "inclusive of all taxes" |
| D6 | consumer care details missing a name, a phone number or an e-mail |
| D7 | `is_imported` and no country of origin |
| D8 | no unit sale price |
| E1 | `source: ecommerce` and the listing is missing any Rule 6(10) declaration |

- `violations` lists non-`info` codes only; `worker/tests/test_dataset.py` rejects `info` codes,
  duplicates, unknown codes, unknown field names and a missing image.
- **F1, F2, P1–P4, D5b and E2 are never in gold for these cases.** F1/F2 need a scale, and no
  photo here has an ArUco marker or a card, so those checks are `unverifiable` and cost no points
  (see `docs/PLAN.md`). P1/P3 need to know which panel is which, P2 needs a calibrated contrast,
  D5b needs two MRP boxes in one frame, E2 is `info`. They come from photos shot to order, with a
  reference card — the shot list below.

## Where these images came from

| Prefix | Source | Licence |
|---|---|---|
| `off_` | [Open Food Facts](https://world.openfoodfacts.org), Indian products | photos CC-BY-SA 3.0, data ODbL |
| `obf_` | [Open Beauty Facts](https://world.openbeautyfacts.org) | same |
| `ecom_` | public product listings on amazon.in / flipkart.com, rendered by headless Chrome | screenshots of public pages, kept as fixtures |
| `phone_` | shot for this project and uploaded through the app | ours |
| `synthetic_` | `eval/make_synthetic.py` (clean print, one panel) | ours |

Rebuild with `eval/fetch_openfoodfacts.py` and `eval/fetch_ecommerce.py`; each case's
`source.json` carries the product URL, the capture date and the licence.

`phone_` cases are ours: a photograph taken with the app, kept as a fixture because it covers a
layout the web set does not. `phone_reynolds_jetter_classic_ballpen` is the first pack in the set
whose declarations are a **bordered two-column table** — label cell left, value cell right, and
two of the labels wrapping onto a second line. Open Food Facts is almost all paragraph labels, so
until this case arrived nothing measured the table path at all and the extractor read none of its
values. Add a `phone_` case whenever a real scan turns up a layout the set is blind to.

These are real phone photographs taken by other people, so they are uneven on purpose: thumbs in
frame, glare, packs held sideways, panels half out of the crop. That is the point — a rendered
label is not a phone photo. Cases whose photos showed no Legal Metrology declaration at all
(an ingredients close-up, a nutrition table on its own) were deleted rather than given a gold
file with nothing in it.

`synthetic_*` cases stay: they are a smoke test for the rule engine, not the benchmark.

## Shot list for the photos still missing (a person with a phone and a reference card)

The web set above cannot test the font, contrast, grouping and seam rules — no photo of it has a
scale reference in frame, and OFF crops rarely show two panels at once. Those need shooting:

| How many | What | Tests |
|---|---|---|
| 15 | Everyday kitchen packs, clean labels, credit card or printed ArUco (`DICT_4X4_50`) flat in frame | F1, F2 |
| 6 | Declarations split across two panels, or printed on a seam / bottom | P1, P3 |
| 5 | Low contrast, glossy, embossed or curved surfaces | P2, unverifiable paths |
| 5 | Non-English or bilingual labels | P4 |
| 3 | Packs printing two different MRPs (a repriced sticker over the printed one) | D5b |

Photograph the declaration panel straight on, fill the frame, no flash glare. Write `gold.json`
from the printed pack. Run `make test` after adding cases — the dataset tests catch typos in
field names and rule codes.
