# lm-compliance

Legal Metrology (Packaged Commodities) Rules, 2011 checker. Photo of a package → report with rule citations in under 30 s. SIH 26034. Runs for ₹0.

See `CLAUDE.md` (how the repo works), `docs/PLAN.md` (phases), `docs/ARCHITECTURE.md`, `docs/RULES.md` (the law).

## Run in 5 commands

```bash
cp .env.example .env && cp .env.example frontend/.env.local   # then fill in the Supabase keys
supabase link --project-ref <your-ref> && supabase db push     # schema + RLS + bucket + views
cd frontend && pnpm install && pnpm dev                        # http://localhost:3000
cd worker && uv sync && uv run --env-file ../.env python main.py
cd worker && uv run pytest -q
```

Demo users: `cd worker && uv run --env-file ../.env python ../supabase/seed_users.py` (admin / inspector / viewer, see the script for passwords).

## Without `make` (Windows)

Every Makefile target is one shell line. `scoop install make` if you want it. Otherwise copy the line.

## Eval

```bash
cd worker && uv run python ../eval/run_eval.py --label baseline-v1
```
Prints per-field precision/recall and violation accuracy; writes `eval/results/<date>_<label>.json`.
