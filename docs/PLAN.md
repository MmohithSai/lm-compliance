# PLAN

Phases in order. A phase is done when its "done when" line is true and `make test` is green. Move items, don't drop the order.

Per-item status and evidence live in `docs/PROGRESS.md`. Update both together.

## P0 — dataset + eval harness
- [x] `eval/run_eval.py` runs on an empty dataset and writes `eval/results/<date>_<label>.json`
- [x] real package photos + 6 e-commerce screenshots in `eval/dataset/<case>/` — 31 package cases
      (102 photographs) pulled from Open Food / Beauty Facts by `eval/fetch_openfoodfacts.py`, and
      6 listing screenshots by `eval/fetch_ecommerce.py`. No camera needed after all.
- [x] gold JSON per case (declarations + expected violation codes) — 37 written by reading the
      photographs; conventions in `eval/dataset/README.md`
- [ ] photos with a reference card in frame, two panels in one shot, or a second MRP — the only
      photos the web cannot supply, and the only ones that can test F1/F2/P1/P3/D5b. Shot list in
      `eval/dataset/README.md`; this is what still needs a person with a phone.
- [x] 16 synthetic PIL labels covering D1–D8, D7 imported, E1 and the X1/X2/X3 exemptions — `eval/make_synthetic.py`
- [x] every `gold.json` checked by `worker/tests/test_dataset.py` (canonical fields, real rule codes, valid context keys, image present)
- [x] OCR memoised per image so a rerun measures the change, not PaddleOCR
- Done when: `make eval LABEL=empty` prints a per-field table (0% is fine). **True since 2026-09-07** (`eval/results/2026-09-07_p0-synthetic-16.json`).

## P1 — Supabase schema + auth + upload + worker loop
- [x] `supabase/migrations/0001_init.sql` (tables, RLS, bucket, views, realtime, `claim_scan()`)
- [x] `supabase link` + `supabase db push` on the hosted project — project `jcjxukjgrbmkuydpsnuc`
- [x] `make seed` creates admin / inspector / viewer
- [x] login, upload form (camera, PDP mm, reference-card checkbox, source toggle), scans list
- [x] realtime status on the scan detail page
- [x] worker: `run_scan` downloads images, marks a fake scan `done`
- Done when: a scan goes queued → processing → done end to end from a phone.
  **True since 2026-09-07** — scan `5e0811b8`, shot on a phone at `192.168.1.10:3000`, resized to
  1205×1600, claimed by the worker, `done` on screen without a reload. Score 100 is the P2 stub.

## P2 — OCR + regex/layout extractor (baseline)
- [x] `preprocess.py` denoise (deskew dropped on purpose, see the Decisions log)
- [x] `ocr.py` PaddleOCR PP-OCRv4 → line boxes with confidence, stored in `ocr_words`
- [x] `extractors/regex_layout.py` anchors + nearest-box layout rule
- [x] `run_local` wired: preprocess → ocr → extract → (measure: none) → rules → score
- [x] measured on real photographs, one variable per run, every result file kept
- Done when: `make eval LABEL=baseline-v1` ≥ 70% field extraction on clean photos. Save the result file.
  **98.2% on the 16 synthetic labels. 28.9% on the 37 real cases** (2026-09-07,
  `eval/results/2026-09-07_p2-final.json`; the harness prints the two apart).
  **The 70% line is met on clean labels and not on real photographs.** Seven measured changes took
  the real half from 18.5% to 28.9%; the remaining gap is not one bug. It is three things, in
  order of size:
  1. **generic_name** — 23 of 37 misses. Indian packs print the common name with no label at all
     ("SPICED BUTTERMILK", "CARBONATED WATER", "Lip Balm"). An anchor extractor structurally
     cannot find it. This is the case for the Stretch item, not for more regex.
  2. **manufacturer / consumer_care** — the address wraps over four printed lines and PP-OCRv4
     drops one or two of them on a curved bottle, so the merged block is never word for word.
  3. Everything the photograph itself loses: thumbs over the panel, packs held sideways, the
     value column cropped out of frame.
  Four hypotheses were measured and rejected, result files kept: `det_limit_side_len=1600`
  (54.5%), merging continuation lines for short fields (51.4%), `manufacturer`/`packer` as
  listing-table anchors (flat, more false positives), and a second OCR pass at 90° for packs held
  sideways (real 28.9% → 28.1%, and it doubles OCR time). CLAHE was measured and kept: it took the
  rendered labels 94.5% → 98.2% and left the photographs where they were.
  Nothing named in this plan is untried now. The next lever is the Stretch item.

## P3 — rule engine + scan detail page
- [x] fill `CHECKS` in `rules_engine.py`; delete the `xfail` line in `tests/test_rules.py`
- [x] exemption downgrades (X1 → info, X2/X3 → skip)
- [x] violations stored; detail page: image with boxes, declarations table, violations with rule refs, score
- [x] the engine reproduces every gold verdict from gold declarations — 53/53 cases,
      `tests/test_dataset.py::test_engine_reproduces_gold_from_gold_declarations`. This separates
      the rules from the OCR: without it a rule bug hides behind an extraction miss.
- Done when: `test_rules.py` green; one real scan shown start to finish.
  **Green since 2026-09-08** (407 passed, 26 xfailed — the 26 left are P4's `measure`).
  A real scan ran queued → processing → done against the hosted project on 2026-09-08:
  `7f7eb986`, score 25, three critical violations with rule refs, four `unverifiable` info rows
  with reasons, rows written to `declarations`, `violations` and `ocr_words`. The detail page
  builds and typechecks; **seeing it on screen needs a login, which is yours to do.**

  Violation accuracy, measured (`eval/results/2026-09-08_*.json`): precision 0.73, recall 0.98,
  exact-set 49.1% — up from 0.67 / 0.99 / 28.3% over two labelled changes. **Every remaining
  violation error is an extraction miss, not a rule bug**: for each rule the false positives are
  fewer than that field's extraction misses, and the engine is exact on all 53 gold declaration
  sets. The violation number is therefore P2's number wearing a different hat, and it will move
  when extraction does.

## P4 — reference card scale + font / contrast / grouping
- [ ] ArUco (DICT_4X4_50) and credit-card rectangle detection → mm/px; inspector PDP mm fallback
- [ ] `height_mm`, `width_height_ratio`, `contrast` per declaration; F1/F2/P1/P2 live
- [ ] delete the `xfail` line in `tests/test_measure.py`
- Done when: font check correct on 5 photos with a card; "not verifiable" without one.

## P5 — reports
- [ ] `report.html` → PDF (WeasyPrint), DOCX (python-docx), JSON; uploaded to `scans/<id>/report.*`
- [ ] download buttons on the detail page
- Done when: the PDF opens on a phone and looks clean.

## P6 — repository + search + history + evidence
- [ ] product match by name + manufacturer on scan completion
- [ ] search page (name, brand, manufacturer, inspector, date); per-product history
- [ ] evidence photos + notes on a scan
- Done when: search "Parle" returns its scans and history.

## P7 — dashboard + roles + audit
- [ ] dashboard: scans this week, compliance rate, top 5 violations, by category, recent scans
- [ ] roles enforced in UI (viewer cannot upload) and verified against RLS
- [ ] audit triggers on scans / products / evidence → `audit_log`
- Done when: viewer cannot upload; admin sees everything.

## P8 — e-commerce screenshot mode
- [x] source = ecommerce → E1/E2 rules, no font checks — landed in P3 (`_applies` in
      `rules_engine.py`): a screenshot is not the package, so only Rule 6(10) can be judged
- [ ] error handling: blurry photo / OCR empty → clear message on the scan
- Done when: a listing screenshot gives a Rule 6(10) report.

## P9 — deploy worker + docs
- [ ] Dockerfile builds on amd64 + arm64; HF Space (add a stdlib HTTP health thread on port 7860) or Oracle ARM
- [ ] bake the PP-OCR models into the image — PaddleOCR downloads them on first use,
      which on a cold container is a download per start
- [ ] `docs/DEPLOY.md`; README verified; dry run on a phone over mobile data
- Done when: the demo works away from the laptop.

## Stretch (only if P2/P8 eval < 85% and time remains)
- [ ] Ollama + Qwen2.5-VL-3B extractor behind `EXTRACTOR=local_vlm`, measured against the baseline, logged in `model_calls`.

## Definition of done for the demo
- Photo → report in < 30 s on the deployed worker.
- Eval ≥ 85% field extraction; every violation links to a rule ref and to boxes on the image.
- PDF/DOCX/JSON download, search, history, dashboard, 3 roles — all working on a phone.
- Nothing invented: unknown scale → "not verifiable".
- Total monthly cost: ₹0.

## Decisions log
- 2026-09-08 — A scan the OCR read nothing from is `failed`, not `done`. `score([])` is 100 by
  construction, so an unreadable photograph finished with a perfect score: scan `5e0811b8` sat at
  **100 / 100** for a pen box the pipeline had never read a word of, which is the one wrong
  answer this project must never give. The guard is in `run_scan`, not on the page, because the
  PDF (P5) and the dashboard views (P7) read the same score and would each have inherited it.
  `run_local` is left alone: the eval needs "predicted nothing" to stay scoreable.
- 2026-09-08 — The scan page draws its boxes against the size of the image the browser loaded,
  not `scan_images.width` / `height`. Those columns are written by whatever uploaded the scan,
  and a wrong pair put every box in the wrong place with nothing on the page to say so.
- 2026-09-08 — A date label with no figure in it is a label, same rule as a price or a quantity.
  `mfg_date` joins `NEEDS_A_NUMBER`: on a pack whose declarations are a printed table the
  "manufactured" anchor claimed "Manufactured, Marketed and Brand Owned by", and the report then
  quoted that line back as an unreadable month and year. mfg_date precision 0.56 -> 0.65, four
  fewer false claims, recall and field accuracy unchanged.
- 2026-09-08 — Two ways of loosening "same row" in `nearest`, both measured, both reverted, both
  result files kept. A real pen box prints "MRP" 31 px tall beside "25.00" at 42 px, and their
  centres are 17.5 px apart against a 15.5 px tolerance - the value is two pixels out of reach
  and the pack reads as having no MRP. Requiring the boxes to overlap vertically by half a line
  (`p3-same-row-is-vertical-overlap`) and requiring the anchor's middle to fall inside the value
  (`p3-same-row-anchor-middle`) both scored real 28.9% -> 27.4%, losing more on net quantity than
  they won on price. The tight test is doing real work; the table-cell case needs the column
  found, not the tolerance widened.
- 2026-09-08 — P3. D5's rupee marker is reported `unverifiable`, not failed. Rule 2(m) wants the
  amount marked ₹ or Rs, and that is the one part of the rule a photograph cannot settle: no
  PP-OCR dictionary contains ₹ (all 56 checked in an earlier entry), so the extractor never
  delivers one. Requiring the glyph failed eleven cases whose price line was read word for word
  right, ten of them the rendered labels. Wording, amount and "inclusive of all taxes" are still
  enforced and still critical. Third time this argument has been made in this file, and it is the
  same one each time: holding a pack to a character no model can emit measures the dictionary.
  Violation precision 0.67 → 0.71, exact-set accuracy 28.3% → 49.1%.
- 2026-09-08 — P3. P1 (declarations grouped on one panel) can pass but not fail. One photograph
  holding every declaration is proof they are grouped; two photographs are not proof of the
  opposite, because nothing places one photo relative to another and two shots of one back panel
  look exactly like a split pack. As a `major` failure it accused five eval cases whose extra
  frames were overlapping crops — `1_ingredients.jpg` and `2_nutrition.jpg` are usually the same
  panel. It now reports `unverifiable` with the reason. `eval/dataset/README.md` already said P1
  was not measurable from this data; the engine now agrees with it. Precision 0.71 → 0.73.
  P4's scale reference is what makes the failure side real.
- 2026-09-08 — P3. A screenshot is not the package: on an `ecommerce` scan only Rule 6(10) rules
  run. What is printed on the pack is not in the frame, so D1–D9, F1–F3 and P1–P4 have no
  evidence to judge. This is what `eval/dataset/*/gold.json` has said since P0 — every listing
  case expects `["E1"]` and nothing else — so the engine was disagreeing with the gold, not with
  the law. One branch in `_applies`, pinned by a test.
- 2026-09-08 — P3. `run_rules` fills `net_qty_g_or_ml` from the net quantity declaration when the
  inspector did not enter it, the same way it already fills `is_imported` from an importer
  declaration. Without it the Rule 26(a) ten gram exemption could never fire on a real scan and
  X1 was dead code. The inspector's answer still wins; gold that sets the field explicitly is
  unaffected.
- 2026-09-08 — P3. `eval/dataset/obf_muuchstac_.../gold.json` had the MRP transcribed as
  "MRP 299.00" and expected D5. The new gold-versus-engine test flagged it; enlarging the photo
  shows the pack prints "MRP ₹ (Incl. of all taxes)" down the left of the batch sticker, with the
  amount on the sticker — the phone's own watermark sits over it. Gold was wrong and the engine
  was right, which is exactly what that test is for. The unit sale price is on the same sticker
  with its leading digit under the watermark, so D8 stays: illegible is absent, as the dataset
  README says.
- 2026-09-08 — P3. The contrast floor for P2 lives in the YAML (`params.min_contrast: "0.5"`),
  not in the code. The Rules say "in contrast with the background" and give no number, so unlike
  Table I's heights or Rule 7's one-third width, this threshold is ours and has to be visible and
  editable where the law is.
- 2026-09-07 — CLAHE on the LAB lightness channel, after the denoise, kept. It took the rendered
  labels from 94.5% to 98.2%, fixing four of the six character-level misses that an earlier entry
  here had written off as "nothing the extractor can reach; the lever is a heavier recognition
  model". It was contrast, not the model — that entry was wrong and this one corrects it. The real
  photographs did not move at all, which also rules out contrast as the reason PP-OCR misses whole
  lines on a curved bottle.
- 2026-09-07 — A second OCR pass at 90° for packs held sideways: measured, worse, reverted
  (real 28.9% → 28.1%, and it doubles OCR time on any page that triggers it). The trigger was
  "most boxes are taller than wide", and it fires on panels that merely *contain* vertical text —
  a Coke bottle prints "MADE IN INDIA" sideways among horizontal lines — where rotating the page
  loses everything else. Doing this properly means deciding orientation per box, not per page.
- 2026-09-07 — `make worker` and `make eval` pass `--extra ocr`. PaddleOCR was an optional extra
  while the pipeline was a stub; since P2 it is the pipeline, and plain `uv run` syncs the venv
  back down to the default dependencies and uninstalls it. Both targets failed on a clean machine.
- 2026-09-07 — P0's "needs a camera" was wrong. Open Food Facts and Open Beauty Facts are public
  databases of phone photographs of packaging, Indian products included, and their
  ingredients / nutrition / packaging shots are the back panel — which is where the Legal Metrology
  declarations are printed. `eval/fetch_openfoodfacts.py` pulls them at 1600 px, the size the
  frontend uploads. Photos are CC-BY-SA 3.0 and every case keeps a `source.json` with the product
  URL and the licence. What the web cannot supply is a photo with a reference card in frame, so
  F1/F2 (and P1/P3/D5b) still need a person; that is all the shot list is for now.
- 2026-09-07 — E-commerce cases are headless-Chrome screenshots of public listings
  (`eval/fetch_ecommerce.py`), sliced into 1600 px tiles because that is what an inspector
  uploads: two or three phone screenshots, not one 9000 px strip. A capture under two tiles is a
  404 or a bot block and is discarded rather than stored as a fixture. BigBasket and JioMart both
  refuse headless Chrome; Amazon and Flipkart do not.
- 2026-09-07 — Gold describes **the images in the case folder**, not the pack they came from. If
  the MRP is printed on a panel nobody photographed, the MRP is absent and the expected violation
  is the one the inspector would actually get from that upload. A declaration that is present but
  cut off by the frame counts as absent: the evidence has to be legible or there is nothing to
  cite. 81 candidate products were fetched and deleted for having no legible declaration at all.
- 2026-09-07 — The eval memoises OCR under `eval/.ocr_cache/`, keyed on the image plus a hash of
  `preprocess.py` and `ocr.py`. Without it a labelled run costs an hour and "one variable per run"
  stops being affordable. Keying on the source means there is no stale-cache footgun and no flag
  to remember. `run_local` grew one defaulted argument to make this possible; nothing else passes it.
- 2026-09-07 — The eval prints real and synthetic accuracy apart. A rendered label and a phone
  photo are different problems and one number hides which half moved: the combined 58.4% is
  94.5% synthetic and 28.9% real.
- 2026-09-07 — Two P2 changes measured and reverted, both result files kept.
  `det_limit_side_len=1600` (PP-OCR shrinks a 1600 px photo to 960 before detection) scored 54.5%
  against 57.7%: detecting at full size splits lines into more, smaller boxes, and the extractor's
  "one box is one printed line" assumption is what pays for the anchors. Adding "manufacturer" and
  "packer" as manufacturer anchors for listing tables scored flat with three more false positives.
- 2026-09-07 — Continuation-line merging is limited to `manufacturer`, `importer`, `consumer_care`.
  Merging every field cost 4.5 points: "Net Qty: 200 g" and "MADE IN INDIA" are one line by
  construction and swallowed the line below them. The law prints an address block for those three
  fields and a single line for the rest, so the rule follows the law, not the layout.
- 2026-09-07 — The eval drops spacing entirely instead of collapsing it. `eval/dataset/README.md`
  has said spacing is ignored since P0, but collapsing runs of spaces is not ignoring them: gold
  "NET WEIGHT 64 g" failed a correct read of "NET WEIGHT 64g", because PP-OCR does not put a space
  back where the print had one. Third measurement fix of this kind, same argument as the currency
  marker and the sentence dot: the comparison was measuring the OCR's spacing, not the extraction.
- 2026-09-07 — An anchor may end against its value (`(?![a-z])`, not `\b`). PP-OCR reads
  "UNIT SALE PRICE : ₹ 0.20 PER g" as "UNIT SALE PRICE0.20PER g", and a word boundary refused it.
  A following letter is still another word, so "exp" still does not claim "export".
- 2026-09-07 — A price or quantity label with no figure in it is a label: look for the figure
  beside or under it, and report nothing if the panel has none. Indian packs print
  "MRP ₹ (INCL. OF ALL TAXES): SEE BOTTLE" constantly. Same reason for the cross-reference guard
  ("same as", "see neck/cap/bottom", "scan barcode"): the line names a declaration without carrying
  it, and claiming it hides the real one printed further down.
- 2026-09-07 — P2. `paddlepaddle` pinned to `==3.0.0`. On 3.3.1 every PP-OCRv4 model dies in
  `NotFoundError: OneDnnContext does not have the input Filter` at the first conv, with
  `enable_mkldnn` off and with `FLAGS_use_mkldnn=0`. `setuptools` joins the `ocr` extra because
  paddle 3.0 imports `distutils`, which Python 3.12 dropped.
- 2026-09-07 — One `Word` = one PP-OCR line box. PP-OCR detects lines, not words, and splitting a
  line into per-word boxes means inventing the split coordinates, which this project does not do.
  A declaration is printed as one line anyway, so the extractor and the P4 font checks both want
  the line. `ocr_words` keeps its name; the table is still `ocr_words`.
- 2026-09-07 — No deskew in `preprocess`. PP-OCRv4 detects rotated quads by itself, and rotating
  the page would put every box in a space the detail page cannot draw in — the axis-aligned box of
  a line rotated 15° grows by its own length. `preprocess` is denoise only, and the bilateral
  sigmas are the knob for the real photo set.
- 2026-09-07 — Baseline eval, one variable per run: 57.3% → 69.1% (strip the stray terminator OCR
  adds to a line) → 91.8% (currency) → 94.5% (dots). Two of those were measurement fixes, not
  extraction work, and both are alignments with what `eval/dataset/README.md` already promised:
  no PP-OCR dictionary contains `₹` (checked all 56), so holding gold to a glyph no model can emit
  measured the dictionary and nothing else; and a dot that is not between digits is punctuation,
  which the README says is ignored — keeping it failed "MIDC. Pune 411019", an address that is
  otherwise word for word right. The extractor drops the `<` PP-OCR prints where `₹` should be:
  a deletion, not a guess. Every run's result file is in `eval/results/`.
- 2026-09-07 — The 6 remaining misses are recognition errors on rendered text, nothing the
  extractor can reach: `Bjscuits` ×4, `400o59`, `Net Qtv`. The upgrade path if the real set shows
  the same is a heavier rec model, not more regex.
- 2026-09-07 — `run_scan` no longer catches `NotImplementedError`; `run_local` now catches it
  around `run_rules` instead, so a scan still completes while P3's checks are stubs. Delete that
  `try/except` when `CHECKS` is filled.
- 2026-09-07 — `lib/env.ts` must reference `process.env.NEXT_PUBLIC_*` literally. With a computed
  key (`process.env[name]`) Next.js inlines nothing, so the browser bundle had no Supabase URL or
  key and every client call threw. Server code was fine, which made it look like an auth problem.
- 2026-09-07 — `crypto.randomUUID()` is secure-context only and the demo runs over
  `http://<lan-ip>:3000`. `lib/uuid.ts` builds the v4 id from `getRandomValues`, which is not
  gated. Anything else needing a secure context (`getUserMedia`, `crypto.subtle`) will need HTTPS.
- 2026-09-07 — Photo input split in two: `capture="environment"` and `multiple` cannot share an
  element (capture wins and caps the pick at one file). A camera button and a gallery button feed
  one list that appends instead of replacing.
- 2026-09-07 — Hosted project linked: `jcjxukjgrbmkuydpsnuc` (name "SIH", Mumbai). `supabase link`
  and `db push` needed no database password — CLI 2.51 provisions a login role from the personal
  access token. `.env` and `frontend/.env.local` written from `supabase projects api-keys`.
- 2026-09-07 — `.mcp.json` now carries `--project-ref`, so `account` dropped from `--features`
  (project-scoped mode disables the account tools anyway).
- 2026-09-07 — `database.types.ts` is generated from now on (`make db-types`). `gen types` only
  sees `text` for the check-constrained columns, so the unions (`Role`, `ScanSource`, `ScanStatus`,
  `ImageKind`, `Severity`) moved to a hand-written `frontend/lib/db.ts` that the generator cannot
  overwrite. Keep it in step with `0001_init.sql`.
- 2026-09-07 — `run_scan` catches `NotImplementedError` from `run_local` and stores an empty result
  with score 100. The queue has to work before P2 exists; delete the `try/except` when it does.
- 2026-09-07 — `ocr_words.id` is a Postgres identity column, so `store()` inserts the words first
  and remaps `declarations.word_ids` and `violations.evidence.word_ids` onto the returned ids. The
  pipeline's own word ids never reach the database.
- 2026-09-06 — Repo root is `SIH/` itself, not a subfolder.
- 2026-09-06 — Next.js pinned to 15.5 (latest is 16; spec says 15; 15 keeps `middleware.ts`).
- 2026-09-06 — Worker on Python 3.12 via uv (paddlepaddle wheels); OCR and PDF deps are optional extras (`--extra ocr --extra pdf`) so `uv sync` stays fast on dev machines.
- 2026-09-06 — Tests for P3/P4 are written now and carry a strict `xfail(raises=NotImplementedError)`; the line is deleted when the code lands.
- 2026-09-06 — Unverifiable checks are stored as `info` violations with `evidence.status = unverifiable`; they never cost score points. One shape for the report, no second result type.
- 2026-09-06 — Score = 100 − 25·critical − 10·major − 3·minor, floor 0.
- 2026-09-06 — No docker on the dev machine: schema goes straight to the hosted project with `supabase db push`; `database.types.ts` is hand-written until `make db-types` can run against the linked project.
- 2026-09-07 — Supabase MCP added read-only in `.mcp.json`, version pinned and `--features` narrowed. It holds an account-wide personal access token, so `@latest` + `-y` was a real supply-chain hole. Add `--project-ref` the moment the hosted project exists.
- 2026-09-07 — `eval/results/*.json` un-ignored. The plan says "save the result file" and "nothing is done until measured"; a gitignored result is neither. Every labelled run is now in history.
- 2026-09-07 — `make lint` also covers `eval/` (it never did, and `run_eval.py` had two lines over the limit).
- 2026-09-07 — `docs/PROGRESS.md` is the per-item tracker; `PLAN.md` keeps the phase order and the "done when" lines. Two files, one commit.
- 2026-09-07 — Synthetics grown to 16 cases so the rule engine has something to fail against before real photos exist. Font (F1/F2), grouping (P1), contrast (P2), seam (P3), language (P4), D5b and E2 are deliberately left to the real photos — a flat rendered image cannot test them honestly.
- 2026-09-06 — Rule refs checked against the Rules text on Indian Kanoon: 6(1)(a) manufacturer, 6(1)(aa) country of origin, 6(1)(b) generic name, 6(1)(c) net quantity, 6(1)(d) month/year, 6(1)(e) MRP, 6(2) consumer care. Refs still marked `verify: true` in the YAML need the PDFs in `docs/law/`.
