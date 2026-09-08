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
- [x] ArUco (DICT_4X4_50) and credit-card rectangle detection → mm/px; inspector PDP mm fallback
      — `measure.py`. The card is only looked for when the inspector ticked the box: measured on
      the eval set, the rectangle detector claimed a scale in **14 frames with no card in them**.
- [x] `height_mm`, `width_height_ratio`, `contrast` per declaration; F1/F2/P2 live
      — measured off the print inside each OCR box, on the photograph as uploaded, and only on a
      frame that carries a scale reference. **P1 is not live and cannot be** — see the Decisions
      log: a scale does not tell two photographs apart, so P1 still passes or says unverifiable.
- [x] delete the `xfail` line in `tests/test_measure.py` — 26 xfails gone, 465 tests pass
- [x] two rendered cases with a 50 mm marker in `eval/dataset`, so the chain has a live path:
      `synthetic_marker_font_ok` (30 cm² panel, 1 mm required, 3.13 mm printed → passes) and
      `synthetic_marker_font_small` (3000 cm² panel, 6 mm required, same print → F1)
- Done when: font check correct on 5 photos with a card; "not verifiable" without one.
  **The second half is true and measured** (`eval/results/2026-09-08_p4-height-is-the-tall-glyphs.json`:
  every check that needs a scale reports `unverifiable` on all 54 photographs and screenshots,
  costing no points; violation precision is unchanged at 0.74).
  **The first half still needs a person.** No photograph in the set has a card or a marker in
  frame — the same blocked P0 item — so the measuring chain is verified two other ways instead:
  unit tests on generated markers and cards, and the two rendered marker cases, where the true
  scale is known by construction. On those the pipeline recovers **0.1253 mm/px against a true
  0.1250** (0.2% out) and reads 3.13 mm print as 3.13 mm. What that does not prove is glare,
  focus and perspective on a real pack, which is exactly what the shot list is for.

## P5 — reports
- [x] `report.html` → PDF (WeasyPrint), DOCX (python-docx), JSON; uploaded to `scans/<id>/report.*`
- [x] download buttons on the detail page
- Done when: the PDF opens on a phone and looks clean. **True since 2026-09-08** — four A4 pages
      from `eval/dataset/phone_reynolds_jetter_classic_ballpen`, single column, 11.5 pt, fonts
      embedded, nothing fetched at render time.

## P6 — repository + search + history + evidence
- [x] product match by name + manufacturer on scan completion — `worker/pipeline/product.py`,
      keyed on `products.match_key` (unique), upserted so the second photograph of a pack joins
      the first one's row. No maker declared → no product, and the scan says so.
- [x] search page (name, brand, manufacturer, inspector, date); per-product history — one
      `scan_search` view carrying every searchable word, `/scans?q=`, and `/products/<id>`
- [x] evidence photos + notes on a scan — the `evidence` table, its RLS and the private bucket
      all date from P1 and are reused as they stand; photos live at `<scan id>/evidence/<id>.jpg`
      and are read through the same signed URLs as the reports. The note is `scans.notes`, which
      the report already prints, so P5 is untouched.
- Done when: search "Parle" returns its scans and history.
  **True.** Verified on the hosted project: a real amazon.in Parle-G 800 g listing pushed through
  the worker (`cddac6b6`) files under the product **Parle Biscuits Pvt Ltd**, and `?q=Parle`
  returns it. The two Reynolds pen scans (`5e0811b8`, `3f5b8e1e`), read with different OCR noise,
  file under one product and `/products/<id>` shows both with an average score. Evidence and notes
  were smoke tested against the hosted project with real inspector and viewer sessions — 13 checks,
  including the four the viewer must be refused. **P6 is done.**
- [x] the listings' own label. "Manufacturer :" was not an anchor — "manufactured by" was,
      "importer" was, the bare noun was not — so no e-commerce listing had a maker to match on.
      Three measured runs, `docs/EVAL.md`: the anchor alone is flat (and was already rejected once
      in P2), and it pays only with two rules beside it — a screenshot's next line is the next row
      of the table, and a bare noun is a label only at the start of a box. 62.2% → 62.5%
      (real 29.8% → 30.5%), violations untouched.

## P7 — dashboard + roles + audit
- [x] dashboard: scans this week, compliance rate, top 5 violations, by category, recent scans
      — `frontend/app/dashboard/page.tsx` over four `security_invoker` views and one count query.
      Every figure is read back from what the worker stored; nothing is recomputed on the page.
      Compliant means `compliance_score = 100` — the score the PDF prints, and the only definition
      in the repo. A failed scan is neither done nor compliant, proved by deltas on the hosted
      project. "This week" is Monday 00:00 Asia/Kolkata, decided in `frontend/lib/dashboard.ts`
      and pinned by 6 boundary tests, never taken from the browser's clock.
- [x] roles enforced in UI (viewer cannot upload) and verified against RLS
      — the nav hides Upload, `app/upload/layout.tsx` turns a viewer away on the server, and
      `supabase/check_rls.py` proves the same refusals at PostgREST and Storage with three real
      signed-in sessions: **53 checks, all passing**, 13 of them writes the viewer must be refused.
      Nothing the viewer tried left a row or an audit entry behind.
- [x] audit triggers on scans / products / evidence → `audit_log`
      — one `public.audit()` trigger function in `0005`, on the tables, so a write by the frontend,
      by the worker's service-role key or by psql is recorded the same way. An INSERT stores the
      new row, a DELETE the old one, an UPDATE only the keys that changed with both sides. Actor is
      `auth.uid()`; null means the service role, which is the worker. No trigger on `audit_log`.
- Done when: viewer cannot upload; admin sees everything.
  **True since 2026-09-08.** Verified against the hosted project (`jcjxukjgrbmkuydpsnuc`) and in a
  browser as all three demo users: the viewer has no Upload link, is redirected off `/upload`, and
  is refused by Postgres on every one of 13 direct writes; the inspector keeps everything P1 and P6
  gave them; the admin reads all four dashboard views, every profile, and the audit log, which no
  other role can read at all. Supabase's own security advisor found one thing this phase
  introduced — the new trigger function was callable at `/rest/v1/rpc/audit` — fixed in `0006`
  along with two of the same class that predate it.

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
- 2026-09-08 — P7. **Compliant means the stored score is 100, and that is the only definition.**
  The `dashboard_summary` view written in P1 said "no critical or major violation", which lets a
  minor one through and disagrees with both the score on the scan page and the score in the PDF.
  Three definitions of compliance in one product is how a report says 87 and a dashboard says
  "compliant" about the same pack. The view now reads `compliance_score = 100` off the column the
  worker wrote, which is the same rule P5 set for the report: the dashboard consumes the result,
  it never recomputes it. A `failed` scan has no score and is counted in neither half of the
  fraction — `score([])` is 100 by construction, so a failed scan admitted to the numerator would
  be a perfect mark for a photograph nothing was read from.
- 2026-09-08 — P7. **The week is Asia/Kolkata, and it is decided in one function that has tests.**
  The reports print UTC because a report timestamps one event, and that stays. A dashboard does
  something else: it buckets events into a human week, and the human is an inspector in India. A
  week cut at 00:00 UTC throws every scan taken between midnight and 05:30 on Monday morning into
  last week — a whole working dawn on the wrong side of the line. So `weekStart()` lives in
  `frontend/lib/dashboard.ts`, takes its zone explicitly rather than from the machine it runs on,
  and is pinned by six tests: the exact boundary, one millisecond before it, late Sunday night,
  three days inside, the end instant, and the label. Deliberately **not** a `date_trunc('week',…)`
  inside the view: the count is a filter the page passes in, so there is one implementation of the
  boundary in the repo and it is the one that can be tested without a database.
- 2026-09-08 — P7. **The rule titles come from the YAML by way of Postgres, not by way of a copy.**
  The dashboard has to print "D1 — Name and address of manufacturer / packer / importer", and that
  title exists in exactly one place: `rules/pc_rules_2011.yaml`. Writing the titles into a
  migration would be a second copy of the law in the repo; writing them into a TSX map would be a
  third. So `public.rules` is a mirror the worker refreshes from the YAML at start up
  (`sync_rules`, 23 rows, three tests that compare the written rows to `load_rules()` field by
  field), and `top_violations` left-joins it. If the worker has never run, the title is null and
  the page falls back to the rule ref — a missing name, not a wrong one.
- 2026-09-08 — P7. **The upload guard is a server layout, and it is still not the security
  boundary.** Hiding the nav link stops nobody: `/upload` typed into the address bar rendered the
  form for a viewer. `app/upload/layout.tsx` reads the role on the server and redirects, which is
  ten lines and no file moved. What actually refuses the viewer is the `scans insert`,
  `scan_images insert`, `evidence insert` and `scans bucket insert` policies, and
  `supabase/check_rls.py` proves it with a real viewer JWT at PostgREST and Storage: 13 writes
  attempted, 13 refused, the scan and its evidence byte-identical afterwards, and not one audit
  entry with the viewer as actor.
- 2026-09-08 — P7. **A check that proves nothing may not change anything, and the audit log is
  what caught it.** The first `check_rls.py` picked the oldest real scan as the row to attack — and
  its "an inspector cannot edit somebody else's scan" case then edited a real inspection note,
  because that scan happened to be the inspector's own. It was found by reading `audit_log`, which
  had the old value (`{"notes": null}`) to restore from. The script now creates every row it
  touches, including a second scan owned by the admin to fail against, and deletes them at the
  end. The audit log earned its place before the phase that added it was finished.
- 2026-09-08 — P7. **An UPDATE audit stores what changed, not what the row is.** Both whole rows
  on every update would be the largest table in the database within a week, and reading it would
  still mean diffing two blobs to answer "who changed the score". `audit()` diffs in the trigger
  with `jsonb_each`, stores the changed keys only, old and new side by side, and writes nothing at
  all for an update that changed nothing. INSERT keeps the whole new row and DELETE the whole old
  one, because there the whole row is the change.
- 2026-09-08 — P7. **The audit triggers are on the tables, so nothing can write behind their
  back.** Frontend logging would record what the frontend did, which is the one thing already
  visible; the writes worth recording are the ones that skip it. Proved rather than asserted: the
  check script makes a product with the service-role key — no browser, no RLS — and the INSERT,
  UPDATE and DELETE all appear with a null actor, which is what a write by the worker looks like.
  There is no trigger on `audit_log` itself, and a check asserts the table has never audited
  itself.
- 2026-09-08 — P7. **The security advisor found the hole this phase opened, one migration after
  it opened it.** `public.audit()` is `security definer` so it can write a table nobody has an
  insert policy on, and Supabase exposes every public function at `/rest/v1/rpc/<name>` — so the
  new trigger function was callable by anyone holding the anon key. Calling it raises (there is no
  NEW record outside a trigger) so nothing could be written through it, but a door that should
  never have been in the wall is still a door. `0006` revokes it, and the two functions of the
  same class that predate P7 with it. `auth_role()` is the one that cannot simply be revoked from
  PUBLIC: every RLS policy in `0001` calls it and a policy is evaluated as the signed-in user, so
  the blanket grant comes off and an explicit one goes back to `authenticated` — get that wrong
  and every write in the app starts failing. Verified after pushing: 53 RLS checks still pass, a
  fresh auth user still gets a profile from `handle_new_user`, and `claim_scan` still returns.
- 2026-09-08 — P7. **No new indexes, because the plans were read first.** `dashboard_recent_scans`
  is a hash join over four rows in 0.65 ms, and Supabase's performance advisor lists only
  pre-existing findings — unindexed foreign keys from `0001` and `auth.<fn>()` re-evaluated per row
  in seven P1 policies. Both are real at scale and neither is real at four scans; rewriting seven
  RLS policies during the phase whose job is to prove those policies work is the wrong trade.
  `audit_log` gets two indexes because it is the one table here that grows with every write.
- 2026-09-08 — P6. **A pack's identity is the maker plus the generic name, and nothing else.**
  `products.match_key` is `"<two words of the company>|<four words of the name>"`, both
  normalised, and it is a unique index the worker upserts on — so matching is Postgres's job and
  not a similarity function's. The company is cut to two words on purpose: what ends a company
  name inside an address block is a comma, and the comma is the first thing a photograph loses.
  The same Reynolds pen reads "…Private Limited, Plot No. C-21" in one shot and
  "…Private Limited Plot No. C-21" in the next; two words survive both, four do not.
- 2026-09-08 — P6. **A pack that declares no maker gets no product row.** That is D1, and the
  honest answer is "not identified" on the scan. Filing it under a name derived from anything
  else would put one company's scans in another company's history, which is the one thing a
  repository must not do. The scan stays searchable by inspector, place, note and id.
- 2026-09-08 — P6. **Search is one view, not five filters.** `scan_search` concatenates product,
  brand, maker, category, inspector, place, note and scan id into a `search` column and the page
  does `ilike '%q%'` over it. `security_invoker`, so the caller's RLS still decides which rows
  they are. The alternative — the client `or`-ing filters across two embedded tables — is not
  expressible in one PostgREST query and would have needed two round trips to say less.
- 2026-09-08 — P5. **The scan detail page had never been loaded, and it crashed on the first
  try.** `scan-evidence.tsx` read `e.currentTarget.naturalWidth` *inside* the `setSize` updater;
  React clears `currentTarget` when the handler returns and the updater runs after that, so every
  image load threw and took the whole page down with a client-side exception. It typechecked, it
  built, and 500 tests said nothing — P3 and P4 both shipped with the note "seeing it on screen
  needs a login". Same lesson as the P1 phone run: the bugs that survive a green suite are the
  ones only a browser can find. The download buttons could not have been checked without fixing
  it, so it is fixed here.
- 2026-09-08 — P5. **One `Report` model, three files.** The PDF, the DOCX and the JSON are three
  renderings of the same `pipeline.models.Report`, built once by `build_report`. Three renderers
  each reaching into `PipelineResult` themselves is three chances for the PDF to say 87 and the
  JSON to say 100 about the same pack, and a compliance document that contradicts itself is worse
  than one that does not exist. `report.schema_version` ("1.0") is what an API consumer pins.
- 2026-09-08 — P5. **The report never recomputes the score.** It reads `compliance_score` off the
  result the pipeline stored, and a test pins that: hand it a result whose score has been
  overwritten with 42 and the report says 42. `score()` is one function in `rules_engine`; a
  second implementation living in the report is how the PDF and the dashboard start disagreeing.
- 2026-09-08 — P5. **Every rule appears in exactly one of four lists.** `violations` (a failure
  that cost points), `notes` (`info` severity — D9 best-before is food law, X1..X4 are Rule 26
  exemption notes, F3 flags a medical device), `unverifiable` (status `unverifiable`, costs
  nothing, says why), and `passed`. That last one needed `rules_engine.applicable_rules`: a rule
  that raised nothing is indistinguishable from a rule Rule 26 or Rule 6(10) never applied, and
  deriving applicability a second time inside the report is how the law drifts between two files.
  Measured: `eval/results/2026-09-08_p5-reports.json` is byte-identical to
  `2026-09-08_p4-marker-cases.json` on every key, which is what a behaviour-neutral refactor of
  `run_rules` should look like.
- 2026-09-08 — P5. **An `info` rule can never be "passed".** The first render put
  "F3 · Medical Devices Rules, 2017 — Medical device pack, font rules of the Medical Devices Rules
  apply" under *Checks that passed*, which is a sentence with no meaning in it. A rule whose
  severity is `info` says something when it fires and nothing when it does not, so it is a note or
  it is absent — never a pass.
- 2026-09-08 — P5. **Evidence in the report is a box, not a word id.** `violations.evidence`
  stores `word_ids`, which are Postgres identity values and mean nothing outside this database.
  The report carries `{image_id, x, y, w, h, text}` instead, so a JSON report handed to another
  system still points at the print. A word id the result no longer carries drops its box rather
  than raising in the middle of a report — pinned by a test.
- 2026-09-08 — P5. **Evidence boxes are burned into the photograph, not overlaid.** The scan page
  positions `<span>`s over an `<img>`; a Word document cannot do that, and the same JPEG has to
  serve the PDF and the DOCX. So `annotate()` draws them with OpenCV — blue for a declaration the
  checker read, red for evidence a violation cites — and downscales to 900 px first. A report an
  inspector opens on a phone should not carry three 1600 px photographs.
- 2026-09-08 — P5. **A format that will not render is stored as null; it does not fail the scan.**
  WeasyPrint binds to Pango and Cairo at import, which the Windows dev machine did not have. The
  analysis is the result and the files are a rendering of it, so `publish_report` catches per
  format, logs, and writes `reports.pdf_path = null`. The detail page then offers the two that
  exist and says in one line which one is missing. `render_pdf` imports WeasyPrint inside the
  function for the same reason.
- 2026-09-08 — P5. **A4, one column, 11.5 pt — not a phone-shaped page.** "Opens on a phone and
  looks clean" is a legibility problem, not a page-size problem: an inspection report gets printed
  and filed, and a 105 mm page is wrong on both counts. What makes it readable on a phone is a
  single column with no wide tables, type at 11.5 pt with 1.55 line height, and every finding in
  its own card so scrolling never loses the thread.
- 2026-09-08 — P5. **Looking at the real PDF found three things the tests could not.** The Lucide
  icons were being HTML-escaped by Jinja's autoescape and rendered as paragraphs of angle brackets
  (now `Markup`, and a test pins `<svg` present and `&lt;svg` absent); the running footer was
  longer than its margin box gets — half the page width — and was clipped mid-word; and a portrait
  phone photograph at 180 mm wide is 240 mm tall, so it could not share a page with its own
  heading and threw away most of a page each time (`max-height: 175mm`, five pages down to four).
- 2026-09-08 — P5. **The report's fonts and icons are vendored, not linked.** IBM Plex Sans
  (SIL OFL 1.1) and five Lucide icons (ISC), in `worker/pipeline/templates/assets/`, with their
  licence files, a `fetch.sh` that re-downloads them and a README saying why each was chosen. A
  report generated on a worker with no network must still look like the report; and IBM Plex
  carries ₹ (U+20B9), which the Section 36 penalty footer needs. No emblem, seal or crest: the
  State Emblem of India is protected by the 2005 Act, and a report that looks like a government
  issue when it is not is worse than one with no mark. The masthead is a balance scale.
- 2026-09-08 — P5. `reports` gets a unique index on `scan_id` (`0002_reports_one_per_scan.sql`,
  pushed) and the worker upserts on it. Without it a re-run stacks a second row beside the first
  and the detail page has to guess which is current; the files at `scans/<id>/report.*` are
  overwritten in place anyway.
- 2026-09-08 — P5. `make test` now runs `--extra pdf`. WeasyPrint is a handful of pure-Python
  packages, and without the extra a plain `uv run pytest` syncs it back out of the venv and the
  PDF test skips forever on every machine, including the ones that could run it.
- 2026-09-08 — P4. **Table I's last row was wrong in the code, and the test written in P0 caught
  it.** `rules_engine.TABLE_I` had `(inf, 6.0, 6.0)`: above 2500 cm² an embossed numeral was held
  to 6 mm where Rule 7 and `docs/RULES.md` both say 8. There is now one table, in `measure.py`,
  which the rule engine imports along with the width ratio and the exempt characters. Two copies
  of the law in one repo is how they drift.
- 2026-09-08 — P4. **A card is only a card when the inspector says one is in the frame.** An
  ArUco marker identifies itself — the bits are error-corrected — but a card is a shape, and
  measured over the eval set the rectangle detector claimed a scale in **14 frames that contain
  no card**: product photos on a listing, a flat carton side, a label panel. A wrong scale is
  worse than no scale, because it turns "not verifiable" into a confident millimetre. The upload
  form has asked "is a reference card in the photo" since P1 and the answer was going unused.
- 2026-09-08 — P4. **Contrast is measured in colour, and only on a photo shot to be measured.**
  Three labelled runs. Measuring it on brightness alone called **27 of the 27 real photographs**
  low-contrast (`p4-measure-wired`, violation precision 0.74 → 0.64): red print on a green pack
  is perfectly legible and has almost no difference in brightness. Measuring CIE Lab distance
  instead fixed one case out of 27 (`p4-contrast-in-colour`). Measuring the core of the stroke
  rather than its anti-aliased edge moved the real median from 0.38 to 0.47 and the rendered
  labels from 0.87 to a true 0.99 — a better estimator, kept — and still left **54% of real
  declaration lines under the 0.5 floor**. Enlarging the worst of them settles it: a shadow
  across a Sprite bottle, and "500 mL" in pale blue that is perfectly legible on the carton. That
  number is the light and the focus, not the print, so P2 now joins F1 and F2 behind a scale
  reference and says so in its reason. Precision back to 0.74, exact-set 48.1% → 50.0%.
- 2026-09-08 — P4. **The height is the print, not the OCR box.** A PP-OCR box is padded and spans
  a whole line, so its height is ascender-to-descender at best; Table I measures the numerals. So
  the glyphs are found inside the box (connected components, dropping anything under 40% of the
  line's ink) and their 90th-percentile height is the reading. The 75th percentile was tried
  first and read a mostly lower-case line as 2.26 mm where its capitals are 3.13 mm — 28% short,
  in the direction that accuses a compliant pack. Not the tallest glyph either: one OCR box that
  swallowed a logo would then set the height for the whole declaration.
- 2026-09-08 — P4. **A scale belongs to the photograph it was measured in.** Each frame gets its
  own mm/px, and a declaration is measured with the scale of the frame it was read from. A marker
  in frame 3 says nothing about how far away frame 2 was shot, and borrowing it would be the same
  class of error as inventing one. The consequence for the inspector is on the upload form: the
  card goes beside the declarations, not in a photo of its own.
- 2026-09-08 — P4. Measurements are taken from the photograph as uploaded, never from the
  preprocessed copy. `preprocess` runs CLAHE, and reporting the contrast of an equalised crop
  measures the equalisation. It moves no pixel, so the OCR boxes index both images.
- 2026-09-08 — P4. **P1 (grouping) is still not live, and the P3 entry below that said P4's scale
  would make its failure side real was wrong.** A scale says how big a pixel is; it does not say
  whether two photographs show one panel or two. What would settle it is either the inspector's
  answer, the way P3 already asks about the bottom and the seam, or matching one photo against
  another — neither is a measurement, and neither is P4. P1 keeps passing when everything is in
  one frame and saying `unverifiable` otherwise.
- 2026-09-08 — P4. Two rendered cases with a 50 mm marker joined `eval/dataset` so the font path
  has a live test at all: same print, two panel areas, one expected F1. Their gold carries **F1**,
  which no other case does, and `test_engine_reproduces_gold_from_gold_declarations` now excludes
  F1/F2/P2 — gold holds the declarations as printed, and no amount of text stands in for a
  measurement. A rendered marker is not a photograph of one: it has no glare, no perspective and
  no focus, so `eval/dataset/README.md`'s shot list still asks for real packs with a card.
- 2026-09-08 — The extractor can read a printed declarations table. A pack that sets its
  declarations in a bordered table centres the value against the whole label cell, so a two line
  label ("MRP" over "(incl. of all taxes)") puts its value half a line below the anchor's own
  centre and the row test misses by two pixels. Three parts, each measured on its own:
  `nearest` gets a last resort that reaches into the cell, taking the **best aligned** box rather
  than the nearest — the two earlier attempts failed because they loosened the row test itself
  and then still took the leftmost box, which on one pack was the barcode; the reach runs as a
  **second pass** over the panel, so a weak cell match can never shut out a strong match printed
  further down (it did, and cost a date that was right beside its anchor); and `wrapped_label`
  merges the label cell's second line, followed one line at a time and stopping when the chain
  leaves the value's row. Net on the whole set: field accuracy 59.0% → 59.8%, real 28.4% → 29.8%,
  **7 fewer false accusations and no new misses**, 3 fields better and 1 worse.
- 2026-09-08 — A continuation line may be centred under its heading, not only left aligned.
  Packs set an address as a centred block under "Consumer Care Officer", and the left-edge test
  dropped it at the first line whose indent moved — losing the phone and the e-mail, which is
  exactly what D6 asks for. Two false D6s gone, no field moved either way.
- 2026-09-08 — `MAX_LINES` 6 → 7 and a "manufactured, marketed" anchor. Indian packs write
  "Manufactured, Marketed and Brand Owned by" over two lines before the address even starts, so
  six lines stops short of the PIN code and no anchor claimed the heading at all. The anchor
  costs 0.02 of manufacturer precision — the block it now reads is right but carries two OCR
  character errors, so it can never match gold word for word — and buys a correct verdict on a
  pack that prints a full address and was being told it had none. Violation precision 0.71 → 0.74.
- 2026-09-08 — `eval/dataset/phone_reynolds_jetter_classic_ballpen`: the first pack in the set
  whose declarations are a printed table, added from a real scan before anything was changed to
  read it. The web set is almost all paragraph labels, so the table path had never been measured.
  Gold was written from the photograph, and the case immediately showed the extractor reading
  none of the table's values. It is the reason a `phone_` prefix exists.
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
