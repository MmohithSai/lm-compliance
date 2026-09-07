# PROGRESS

Reference tracker. What is built, what is not, and what is blocked on a human.

`docs/PLAN.md` holds the order and the "done when" line for each phase. This file holds the
detail: per item status, where the code is, and how it was checked. Update both in the same
commit.

Status words: **done** · **partial** · **todo** · **blocked** (needs a person, not code).

Last updated: 2026-09-07.

---

## Summary

| Phase | State | Blocking item |
|---|---|---|
| P0 dataset + eval harness | partial | 40–60 real photos (needs a camera) |
| P1 schema + auth + upload + worker loop | partial | the phone run (code side is done) |
| P2 OCR + extractor baseline | todo | starts after P0 has real photos |
| P3 rule engine + detail page | todo | tests written, 130 `xfail` waiting |
| P4 scale + font / contrast / grouping | todo | — |
| P5 reports | todo | — |
| P6 repository + search + history | todo | — |
| P7 dashboard + roles + audit | todo | — |
| P8 e-commerce mode | todo | — |
| P9 deploy + docs | todo | — |

---

## P0 — dataset + eval harness

**Done when:** `make eval LABEL=empty` prints a per-field table. **This is true today.**

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | Eval harness runs and writes a result file | done | [run_eval.py](eval/run_eval.py) → `eval/results/2026-09-07_p0-synthetic-16.json` |
| 2 | Synthetic label generator | done | [make_synthetic.py](eval/make_synthetic.py), 16 cases |
| 3 | Gold format written down | done | [eval/dataset/README.md](eval/dataset/README.md) |
| 4 | Gold files validated automatically | done | [test_dataset.py](worker/tests/test_dataset.py), 5 checks × 16 cases |
| 5 | Shot list for the real set | done | [eval/dataset/README.md](eval/dataset/README.md) |
| 6 | 40–60 real package photos | **blocked** | needs a person with a phone and a shelf |
| 7 | 5 e-commerce screenshots | **blocked** | same — synthetic stand-ins exist |
| 8 | gold.json for each real case | **blocked** | follows item 6 |

### What the 16 synthetic cases cover

| Case | Context | Expected codes |
|---|---|---|
| `synthetic_compliant` | — | none |
| `synthetic_no_manufacturer` | — | D1 |
| `synthetic_no_generic_name` | — | D2 |
| `synthetic_no_tax_wording` | — | D5 |
| `synthetic_approx_no_email` | — | D3, D6 |
| `synthetic_no_date` | — | D4 |
| `synthetic_future_date` | — | D4 |
| `synthetic_no_unit_price` | — | D8 |
| `synthetic_missing_three` | — | D1, D3, D5 |
| `synthetic_imported_no_origin` | `is_imported` | D7 |
| `synthetic_imported_ok` | `is_imported` | none |
| `synthetic_small_sachet` | `net_qty_g_or_ml: 8` | none (X1 downgrades to info) |
| `synthetic_restaurant_food` | `is_restaurant_food` | none (X2 skips) |
| `synthetic_dpco_drug` | `is_dpco_drug` | none (X3 skips) |
| `synthetic_ecom_missing_qty` | `source: ecommerce` | E1 |
| `synthetic_ecom_complete` | `source: ecommerce` | none |

**Not covered by synthetics, on purpose:** F1, F2 (need a real scale), P1 (needs two panels),
P2 contrast, P3 seam, P4 language, D5b (needs two MRP boxes on one pack), E2. These come from
the real photos. The unit tests in `worker/tests/test_rules.py` already pin their behaviour.

### Latest eval run

`2026-09-07_p0-synthetic-16` — 16 cases, pipeline ran on 0, field accuracy 0.0%.
That is correct: `run_local` raises `NotImplementedError("P2")`. The number is the baseline to
beat. The table lists all 10 canonical fields, so nothing is silently missing from the gold.

### To finish P0

1. Shoot the packs from the shot list into `eval/dataset/<case>/`.
2. Write `gold.json` for each from the printed pack.
3. `make test` — the dataset tests catch typos in field names and rule codes.
4. `make eval LABEL=real-set-v1` and keep the result file.

---

## P1 — Supabase schema + auth + upload + worker loop

| # | Item | Status | Where / evidence |
|---|---|---|---|
| 1 | `0001_init.sql`: tables, RLS, bucket, views, realtime, `claim_scan()` | done | `supabase/migrations/0001_init.sql` |
| 2 | `supabase link` + `db push` on the hosted project | done | project `jcjxukjgrbmkuydpsnuc`; `supabase migration list` shows 0001 local **and** remote |
| 3 | `make seed` creates admin / inspector / viewer | done | 3 rows in `profiles` with the right roles |
| 4 | Login, upload form, scans list | done | `frontend/app/{login,upload,scans}` |
| 5 | Realtime status on the scan detail page | done | [scan-realtime.tsx](frontend/components/scan-realtime.tsx), mounted only while the scan is queued/processing |
| 6 | Worker marks a fake scan `done` | done | [pipeline/__init__.py](worker/pipeline/__init__.py), [test_run_scan.py](worker/tests/test_run_scan.py) |
| 7 | One scan end to end from a phone | **blocked** | needs a person, a laptop running `make dev` + `make worker`, and a device |

### How the loop was checked

A throwaway script queued a scan with one 1×1 JPEG in the `scans` bucket and called
`process_one` once:

```
queued d5e24bf4-…
scan d5e24bf4-…: no pipeline yet (P2), storing an empty result
after worker: {'status': 'done', 'compliance_score': 100, 'error': None}
```

`claim_scan()` is callable by the service role and refused to `anon`/`authenticated`; the `scans`
bucket exists. `run_local` still raises `NotImplementedError("P2")` — `run_scan` catches it and
stores an empty result so the queue works before the pipeline does. That `try/except` is deleted
in P2.

### Verified on the hosted project

| Thing | Result |
|---|---|
| `supabase db push` | 0001 applied, no errors |
| `profiles` after `make seed` | Demo Admin/admin, Demo Inspector/inspector, Demo Viewer/viewer |
| `claim_scan()` as service role | returns `[]` on an empty queue |
| storage buckets | `['scans']` |
| `make db-types` | regenerated `frontend/lib/database.types.ts`; `tsc --noEmit` clean |

---

## P2–P9

Not started. See `docs/PLAN.md` for the item list and the "done when" line of each phase.
The tests for P3 and P4 are already written and carry a strict
`xfail(raises=NotImplementedError)`; 130 of them are waiting. Deleting the `xfail` line is how
those phases get marked done.

---

## Log

- **2026-09-07** — P1 code complete. Hosted project linked and `0001_init.sql` pushed; `make seed`
  created the three demo users; `.env` and `frontend/.env.local` written from the project's API
  keys (both gitignored). `run_scan` downloads the scan's images, runs the pipeline and writes
  words/declarations/violations back, remapping word ids onto the ones Postgres assigns; until P2
  lands it catches `NotImplementedError` and stores an empty result. Scan detail page refreshes on
  realtime updates while the scan is queued or processing. `database.types.ts` is generated now,
  with the check-constraint unions moved to `frontend/lib/db.ts`. `make test` green
  (80 passed, 130 xfailed), `make lint` clean, `tsc --noEmit` clean. Remaining: the phone run.

- **2026-09-07** — P0: synthetic set grown 3 → 16 cases (D1–D8, D7 imported, E1, X1/X2/X3);
  gold files now validated by `worker/tests/test_dataset.py`; shot list added to the dataset
  README. `make test` green (76 passed, 130 xfailed). Baseline eval recorded at 0.0%.
  Remaining P0 work is the real photo set, which needs a person.
  Also: `eval/results/*.json` un-ignored (a gitignored measurement is not a record), and
  `make lint` extended to cover `eval/`.
- **2026-09-06** — P0 harness, 3 synthetic cases, rules YAML, P3/P4 tests, schema, frontend
  shell. See the Decisions log in `docs/PLAN.md`.
