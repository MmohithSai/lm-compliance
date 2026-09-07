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

## Supabase MCP (optional, for Claude Code)

`.mcp.json` adds the Supabase MCP server **read-only**, so Claude can inspect the schema, run
`select`s and read logs, but cannot write or migrate. It needs a personal access token in your
OS environment (see `.env.example`), not in `.env`.

The server version is **pinned**. It runs with your Supabase personal access token, so a silent
`@latest` bump would be a supply-chain hole. Bump it deliberately, as its own commit.

It is scoped to one project with `--project-ref`, which caps the blast radius even though the
token itself is account-wide. Tools are narrowed to `database,debugging,docs` (project scope
disables the account tools anyway). Add `storage`, `functions`, `branching` or `development` to
`--features` if you need them. To allow writes, drop `"--read-only"`, and only against a
throwaway project.

Claude Code reads `SUPABASE_ACCESS_TOKEN` from the OS environment at start-up. After `setx`,
**restart Claude Code** or the MCP server comes up unauthorized.

## Without `make` (Windows)

Every Makefile target is one shell line. `scoop install make` if you want it. Otherwise copy the line.

## Eval

```bash
cd worker && uv run python ../eval/run_eval.py --label baseline-v1
```
Prints per-field precision/recall and violation accuracy; writes `eval/results/<date>_<label>.json`.
