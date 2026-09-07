# PLAN

Phases in order. A phase is done when its "done when" line is true and `make test` is green. Move items, don't drop the order.

Per-item status and evidence live in `docs/PROGRESS.md`. Update both together.

## P0 — dataset + eval harness
- [x] `eval/run_eval.py` runs on an empty dataset and writes `eval/results/<date>_<label>.json`
- [ ] 40–60 real package photos + 5 e-commerce screenshots in `eval/dataset/<case>/` — needs a camera; shot list in `eval/dataset/README.md`
- [ ] gold JSON per case (declarations + expected violation codes) — format and validator ready, follows the photos
- [x] 16 synthetic PIL labels covering D1–D8, D7 imported, E1 and the X1/X2/X3 exemptions — `eval/make_synthetic.py`
- [x] every `gold.json` checked by `worker/tests/test_dataset.py` (canonical fields, real rule codes, valid context keys, image present)
- Done when: `make eval LABEL=empty` prints a per-field table (0% is fine). **True since 2026-09-07** (`eval/results/2026-09-07_p0-synthetic-16.json`).

## P1 — Supabase schema + auth + upload + worker loop
- [x] `supabase/migrations/0001_init.sql` (tables, RLS, bucket, views, realtime, `claim_scan()`)
- [x] `supabase link` + `supabase db push` on the hosted project — project `jcjxukjgrbmkuydpsnuc`
- [x] `make seed` creates admin / inspector / viewer
- [x] login, upload form (camera, PDP mm, reference-card checkbox, source toggle), scans list
- [x] realtime status on the scan detail page
- [x] worker: `run_scan` downloads images, marks a fake scan `done`
- Done when: a scan goes queued → processing → done end to end from a phone.
  **The loop is proven** (2026-09-07, scripted: queue → claim → done, score 100). The phone run
  is still to do — it needs `make dev`, `make worker` and a device on the same network.

## P2 — OCR + regex/layout extractor (baseline)
- [ ] `preprocess.py` deskew + denoise
- [ ] `ocr.py` PaddleOCR PP-OCRv4 → words with boxes + confidence, stored in `ocr_words`
- [ ] `extractors/regex_layout.py` anchors + nearest-box layout rule
- [ ] `run_local` wired: preprocess → ocr → extract → (measure: none) → rules → score
- Done when: `make eval LABEL=baseline-v1` ≥ 70% field extraction on clean photos. Save the result file.

## P3 — rule engine + scan detail page
- [ ] fill `CHECKS` in `rules_engine.py`; delete the `xfail` line in `tests/test_rules.py`
- [ ] exemption downgrades (X1 → info, X2/X3 → skip)
- [ ] violations stored; detail page: image with boxes, declarations table, violations with rule refs, score
- Done when: `test_rules.py` green; one real scan shown start to finish.

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
- [ ] source = ecommerce → E1/E2 rules, no font checks
- [ ] error handling: blurry photo / OCR empty → clear message on the scan
- Done when: a listing screenshot gives a Rule 6(10) report.

## P9 — deploy worker + docs
- [ ] Dockerfile builds on amd64 + arm64; HF Space (add a stdlib HTTP health thread on port 7860) or Oracle ARM
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
