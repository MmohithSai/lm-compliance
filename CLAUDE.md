# lm-compliance

Legal Metrology (Packaged Commodities) Rules, 2011 compliance checker for inspectors in India. SIH problem 26034 (Dept. of Consumer Affairs).
Inspector photographs a package (or uploads an e-commerce screenshot) → OCR → deterministic extraction → rule engine → report (PDF/DOCX/JSON) citing the rule for every violation. Scans saved in a searchable repository. Roles: admin, inspector, viewer. Cost ₹0. No external AI APIs anywhere.

## Stack (decided — do not propose alternatives)

- `frontend/` Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui, TanStack Query, supabase-js via `@supabase/ssr`. PWA (manifest + camera capture). Client resizes images to max 1600 px before upload. Deploy: Vercel Hobby.
- Supabase free tier: Postgres, Auth (email/password), Storage bucket `scans`, Realtime on `scans`, RLS. No custom API server. Postgres views for dashboard stats.
- `worker/` Python 3.12 + uv. One process, supabase-py with the service-role key. Polls every 3 s: claim one `queued` scan → `processing` → pipeline → `done` / `failed`. PaddleOCR (PP-OCRv4), OpenCV (deskew, ArUco/card scale), Pydantic models, Jinja2 → WeasyPrint (PDF), python-docx. Docker linux/amd64 + arm64, RAM < 3 GB.
- `rules/pc_rules_2011.yaml` is the law. The rule engine is pure Python. No AI in the rule engine.
- Tooling: uv, ruff, mypy --strict, pytest · pnpm, eslint, prettier · supabase CLI.

## Folder map

```
docs/            PLAN.md (phases + Decisions log), PROGRESS.md (per-item status + evidence),
                 ARCHITECTURE.md, EVAL.md (how accuracy is measured), RULES.md (law digest),
                 law/ (PDFs), KICKOFF_PLAN.md
rules/           pc_rules_2011.yaml
supabase/        config.toml, migrations/, seed_users.py
frontend/        Next.js app: app/{login,upload,scans,scans/[id],dashboard}, lib/supabase, lib/database.types.ts
worker/          main.py (loop), pipeline/{models,preprocess,ocr,extractors/,measure,rules_engine,report}.py, templates/, tests/
eval/            dataset/<case>/{*.jpg,gold.json,source.json}, run_eval.py, results/,
                 make_synthetic.py, fetch_openfoodfacts.py, fetch_ecommerce.py, diagnose.py
```

## Commands

`make dev` · `make worker` · `make test` · `make eval LABEL=<what-changed>` · `make lint` · `make db-push` · `make db-types` · `make seed`
No `make` on Windows? The Makefile is 1 line per target; run the line directly (see README).

## Engineering rules

- Test set first. `eval/dataset/` holds images + gold JSON. `eval/run_eval.py` prints per-field precision/recall and violation accuracy and writes `eval/results/<date>_<label>.json`. Nothing is "done" until measured.
- Baseline first: OCR + regex/layout + rules, no model. Record the score before changing anything.
- One variable at a time. Every eval run has a label saying what changed.
- Never invent measurements. Scale priority: ArUco/card → inspector-entered PDP mm → none. With none, font checks return status `unverifiable` with a reason.
- Every violation has `rule_id, rule_ref, severity, message, evidence (word_ids, values, status), confidence`.
- Never call any AI inside the rule engine. No external AI APIs in this project.
- Plain, simple language in UI and docs. Short sentences.
- Small commits, conventional messages. Tests with every change. Run `make test` before saying done.
- Keep `docs/PLAN.md` checkboxes and its dated Decisions log current.
- Secrets only via `.env` (`.env.example` is the contract). Never commit keys.
- Ask before adding any dependency not listed above and before any destructive git action.

## Conventions

- Worker: every cross-module value is a Pydantic model from `pipeline/models.py`. No bare dicts across module boundaries. mypy strict, ruff clean.
- Frontend: `Database` type from `lib/database.types.ts` on every Supabase client. Server components read; client components own forms.
- Canonical declaration fields: `manufacturer, importer, generic_name, net_quantity, mfg_date, mrp, consumer_care, country_of_origin, unit_sale_price, best_before`.
- Rule codes: D1–D9 declarations, F1–F3 font, P1–P4 placement, E1–E2 e-commerce, X1–X4 exemptions. See `docs/RULES.md`.
- Score: 100 − 25·critical − 10·major − 3·minor, floor 0. Info never costs points.

## How I want you to work

Plan first, then small steps. Tests before code. One change per eval run, labelled. Say what you are unsure about instead of guessing. Run the tests before saying done.
