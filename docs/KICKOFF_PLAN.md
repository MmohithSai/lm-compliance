# Plan: lm-compliance kickoff scaffold (SIH 26034)

## Context

Greenfield repo at `C:\Users\mmohi\Desktop\SIH` (empty, not yet git). The user wants the Day-1 kickoff from their MVP doc: docs + rules YAML + Supabase schema/RLS + repo skeleton + tests and eval harness **before any pipeline code**, then stop and report. No OCR pipeline yet. Stack is fixed (Next 15, Supabase, one Python worker, PaddleOCR later). Cost ₹0.

## Environment facts (checked, read-only)

| Item | Found | Consequence |
|---|---|---|
| Dir | empty, no git, no `docs/law/` | `git init` here (treat SIH as the repo root, not a subfolder). Law PDFs absent → RULES.md from the digest; add `docs/law/README.md` saying where to drop PDFs; cross-check deferred. |
| Next.js | latest is 16.3; 15.5.25 exists | Use `create-next-app@15` (stack says 15; Next 15 still uses `middleware.ts`). |
| Python | 3.13 system; uv 0.7.5 | `uv python install 3.12`, `requires-python = "==3.12.*"` (paddlepaddle wheels). |
| make | missing | Write the Makefile anyway (Linux/HF/CI). README lists raw commands; suggest `scoop install make`. |
| docker | missing | No local Supabase. `db-push`/`gen types` target the **linked hosted project**. Hand-write `database.types.ts` now, regenerate later. |
| supabase CLI | 2.51 | `supabase init` layout; `supabase link` + `db push` are the user's step in Phase 1. |

## Files to create (tree)

```
.
├── CLAUDE.md
├── README.md                       # run in 5 commands (raw commands, no make needed)
├── Makefile                        # dev, worker, test, eval, lint, db-push, db-types, seed
├── .env.example                    # NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
├── .gitignore                      # node, python, .env*, eval/results/*.json keep dir
├── docs/
│   ├── PLAN.md                     # P0–P9 + stretch checkboxes, DoD, Decisions log (dated)
│   ├── ARCHITECTURE.md             # data flow, schema, RLS, deploy, scaling
│   ├── RULES.md                    # D1–D9, F1–F3, P1–P4, E1–E2, X1–X4 tables + penalty footer + score formula
│   └── law/README.md               # "drop consolidated PC Rules PDF + amendments here"
├── rules/pc_rules_2011.yaml        # one entry per code: rule_id, rule_ref, title, severity, check, message_template, applies_to, exemptions
├── supabase/
│   ├── config.toml                 # from `supabase init` (trimmed)
│   ├── migrations/0001_init.sql
│   └── seed_users.py               # 3 demo users via supabase-py admin API (service role), sets roles
├── frontend/                       # create-next-app@15 --ts --tailwind --app --src-dir=no --eslint
│   ├── app/{layout,page,manifest}.ts(x)
│   ├── app/login/page.tsx          # email+password, functional
│   ├── app/upload/page.tsx         # camera input, resize→1600px, PDP mm fields, reference-card checkbox, source toggle; upload + insert scan
│   ├── app/scans/page.tsx          # list (query scans)
│   ├── app/scans/[id]/page.tsx     # placeholder
│   ├── app/dashboard/page.tsx      # placeholder
│   ├── middleware.ts               # redirect to /login when signed out
│   ├── lib/supabase/{client,server}.ts   # @supabase/ssr
│   ├── lib/database.types.ts       # hand-written now, `make db-types` later
│   ├── lib/image.ts                # canvas resize to max 1600px
│   └── components/ui/*             # shadcn: button input label card checkbox badge table
├── worker/
│   ├── pyproject.toml              # uv; deps: supabase, pydantic, pyyaml, opencv-python, numpy, paddleocr, paddlepaddle, jinja2, weasyprint, python-docx; dev: pytest, ruff, mypy
│   ├── main.py                     # poll loop: claim queued → processing → run → done/failed
│   ├── Dockerfile                  # python:3.12-slim, apt libs for cv2+weasyprint, multi-arch
│   ├── pipeline/
│   │   ├── models.py               # Pydantic: Word, Declaration, Violation, ScanContext, PipelineResult
│   │   ├── preprocess.py           # stub
│   │   ├── ocr.py                  # stub
│   │   ├── extractors/base.py      # Extractor Protocol
│   │   ├── extractors/regex_layout.py  # stub
│   │   ├── measure.py              # stubs: mm_per_px_from_aruco, mm_per_px_from_card, min_height_mm, width_ratio_ok
│   │   ├── rules_engine.py         # load_rules(yaml) + run_rules(decls, ctx) — check registry, stubs raise NotImplementedError
│   │   ├── report.py               # stub
│   │   └── templates/report.html   # Jinja2 skeleton
│   └── tests/
│       ├── conftest.py             # decl()/ctx() fixture helpers
│       ├── test_rules.py           # ≥3 cases per rule (pass/fail/edge), module-level strict xfail until P3
│       ├── test_measure.py         # synthetic ArUco → mm/px; Table-I boundaries; ratio; strict xfail until P4
│       └── test_yaml.py            # YAML loads, every `check` name exists in registry, codes unique  (passes now)
└── eval/
    ├── dataset/README.md           # <case>/image.jpg + gold.json format
    ├── run_eval.py                 # per-field P/R, violation accuracy → eval/results/<date>_<label>.json; works on empty dataset
    └── results/.gitkeep
```

## Key design decisions (baked into files)

**Declaration field names (canonical, used by YAML, tests, DB):**
`manufacturer` (name+address), `importer`, `generic_name`, `net_quantity`, `mfg_date`, `mrp`, `consumer_care`, `country_of_origin`, `unit_sale_price`, `best_before`.

**ScanContext:** `source` (package|ecommerce), `is_imported` (importer decl present or inspector flag), `pdp_area_cm2 | None`, `mm_per_px | None`, `scale_source` (aruco|card|inspector|none), `embossed: bool`, `is_medical_device`, `net_qty_grams_or_ml | None` (for X1).

**Rule codes → check functions (rules YAML):**
- D1 `field_present(manufacturer)` critical · D2 `field_present(generic_name)` major · D3 `net_quantity_valid` critical (number + unit in g/kg/ml/L/cm/m/N/pcs; reject approx/about) · D4 `date_valid_not_future` major · D5 `mrp_valid` critical (MRP wording + ₹/Rs amount + "inclusive of all taxes") and `single_mrp` critical · D6 `consumer_care_valid` major (phone + email) · D7 `origin_required_if_imported` critical, applies_to imported · D8 `field_present(unit_sale_price)` minor · D9 `field_present(best_before)` info
- F1 `font_height_table1` major (uses `height_mm` on decls; status `unverifiable` when no scale) · F2 `font_width_ratio` minor · F3 `medical_device_flag` info (skip F1/F2)
- P1 `grouped_on_one_panel` major · P2 `contrast_ok` major · P3 `not_on_bottom_or_seam` major (unverifiable unless inspector marks) · P4 `language_ok` major
- E1 `ecommerce_all_declarations` critical, applies_to ecommerce (all except mfg_date) · E2 `ecommerce_origin_filter` info
- X1 `exemption_small_pack` (≤10 g/ml → downgrades D-rules to info) · X2 restaurant fast food · X3 DPCO drugs · X4 pan masala — all info, driven by ctx flags

**Score:** 100 − 25·critical − 10·major − 3·minor, floor 0. Documented in RULES.md.

**Tests-first without pipeline code:** tests are written against the real API; `test_rules.py` and `test_measure.py` each carry one line `pytestmark = pytest.mark.xfail(strict=True, reason="P3/P4 not built")`. `make test` is green today; when the engine lands the strict xfail turns XPASS → fail, forcing the line to be deleted. `test_yaml.py` passes for real now (registry names ↔ YAML).

**Worker claim:** `update scans set status='processing' where id=(select id from scans where status='queued' order by created_at limit 1) returning *` via one RPC `claim_scan()` in the migration (atomic, safe for >1 worker later).

**Migration 0001_init.sql outline:**
- tables exactly per spec (profiles, products, scans, scan_images, ocr_words, declarations, violations, reports, evidence, audit_log, model_calls) with the check constraints listed; `evidence(id, scan_id, storage_path, note, created_by, created_at)`.
- `auth_role()` security-definer helper reading `profiles.role`.
- trigger `on_auth_user_created` → profiles row, role `viewer`.
- RLS: all tables `select` for authenticated; `insert/update` on scans/scan_images/evidence/products for inspector where `inspector_id = auth.uid()` (products: `created_by`); admin `all`; pipeline tables (ocr_words, declarations, violations, reports, model_calls) written only by service role (bypasses RLS).
- storage bucket `scans` (private) + policies: authenticated read, inspector/admin insert.
- views with `security_invoker = true`: `dashboard_summary`, `top_violations` (30 d), `violations_by_category` (join products.category).
- `alter publication supabase_realtime add table scans`.
- `claim_scan()` RPC.

**Frontend:** Supabase clients via `@supabase/ssr`; TanStack Query provider in layout; upload page resizes on client, uploads to `scans/<scan_id>/<n>.jpg`, inserts `scans` + `scan_images`. Realtime subscription is Phase 1 (not now). PWA = `app/manifest.ts` only; service worker skipped (add if the install prompt doesn't appear on Android Chrome).

**Dockerfile:** `python:3.12-slim`, apt `libgl1 libglib2.0-0 libpango-1.0-0 libpangoft2-1.0-0 libcairo2 fonts-dejavu`, `uv sync --frozen`, `CMD ["python","main.py"]`. HF Spaces health check on port 7860 → add a 5-line stdlib `http.server` thread in P9, noted in ARCHITECTURE.md.

## Execution order

1. `git init`; write CLAUDE.md, .gitignore, .env.example, README.md, Makefile.
2. docs/PLAN.md, ARCHITECTURE.md, RULES.md, law/README.md; rules YAML.
3. `supabase init` (accept defaults, no docker needed for init) → migration + seed_users.py.
4. `pnpm create next-app@15 frontend --ts --tailwind --eslint --app --no-src-dir --import-alias "@/*" --use-pnpm`; `pnpm add @supabase/supabase-js @supabase/ssr @tanstack/react-query`; `pnpm dlx shadcn@latest init -d` + add components; write pages/lib.
5. `uv init worker` (py 3.12), pyproject deps, models, stubs, main.py, Dockerfile, tests, templates.
6. eval/run_eval.py + dataset README.
7. Run checks (below), then print tree, make commands, and the "unsure" list. Stop.

## Verification

```bash
cd worker && uv sync && uv run pytest -q          # green: test_yaml passes, rules/measure xfail
cd worker && uv run ruff check . && uv run mypy .  # clean under strict
cd frontend && pnpm lint && pnpm build             # builds without env (clients read env lazily)
cd worker && uv run python ../eval/run_eval.py --label empty   # prints 0 cases / 0%, writes eval/results/<date>_empty.json
```
Migration SQL cannot be applied locally (no docker); syntax-check with `uvx --from pglast python -c "..."` (no project dep), real apply is the user's Phase 1 `supabase link && supabase db push`.

## Known "unsure" items to report at the end

- Next 15 vs 16 (pinned 15 per spec; 16 would rename middleware→proxy).
- WeasyPrint on Windows needs GTK; dev on Windows may need the MSYS2 GTK runtime — only matters in P5.
- PaddleOCR/paddlepaddle pins: `paddleocr` 2.x for PP-OCRv4; 3.x defaults to v5. Decide in P2; pinned as `paddleocr>=2.9,<3` for now.
- P3 "not on bottom/crimp/seam" is unverifiable from a flat photo without inspector input — modeled as `unverifiable` with an inspector checkbox later.
- Storage bucket policies in SQL migrations vs dashboard: written in SQL (works with `db push`).
