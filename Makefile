LABEL ?= dev
.PHONY: dev worker test eval lint db-push db-types seed

dev:
	cd frontend && pnpm dev

worker:
	cd worker && uv run --extra ocr --env-file ../.env python main.py

test:
	cd worker && uv run pytest -q

eval:
	cd worker && uv run --extra ocr python ../eval/run_eval.py --label $(LABEL)

lint:
	cd worker && uv run ruff check . ../eval && uv run ruff format --check . ../eval && uv run mypy .
	cd frontend && pnpm lint

db-push:
	supabase db push

db-types:
	supabase gen types typescript --linked > frontend/lib/database.types.ts

seed:
	cd worker && uv run --env-file ../.env python ../supabase/seed_users.py
