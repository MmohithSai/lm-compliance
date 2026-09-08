# lm-compliance

Legal Metrology (Packaged Commodities) Rules, 2011 checker. Photo of a package → report with rule citations in under 30 s. SIH 26034. Runs for ₹0.

See `CLAUDE.md` (how the repo works), `docs/PLAN.md` (phases + decisions), `docs/PROGRESS.md`
(what is built and how it was checked), `docs/ARCHITECTURE.md`, `docs/EVAL.md` (how accuracy is
measured), `docs/RULES.md` (the law).

## Run in 5 commands

```bash
cp .env.example .env && cp .env.example frontend/.env.local   # then fill in the Supabase keys
supabase link --project-ref <your-ref> && supabase db push     # schema + RLS + bucket + views
cd frontend && pnpm install && pnpm dev                        # http://localhost:3000
cd worker && uv sync && uv run --env-file ../.env python main.py
cd worker && uv run --extra pdf pytest -q && cd ../frontend && pnpm test
```

**Windows, for the PDF report only:** WeasyPrint binds to GTK's native libraries, which Windows
does not ship. Install the
[GTK3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer) and set
`WEASYPRINT_DLL_DIRECTORIES` to the folder holding `libgobject-2.0-0.dll` (see `.env.example`).
Without it the PDF test skips, and a scan still gets its JSON and DOCX reports. Linux and macOS
need nothing; the Docker image installs the libraries with `apt`.

Demo users: `cd worker && uv run --env-file ../.env python ../supabase/seed_users.py` (admin / inspector / viewer, see the script for passwords).

## The two kinds of scan, and the one answer that is neither

Pick **Package photo** or **E-commerce screenshot** on the upload form; it sets `scans.source` and
that decides which law applies. A screenshot is not the package, so a listing is judged by **Rule
6(10)** — what the listing must declare — and nothing else. Print size, character width, contrast
and placement are not applied to it at all, because none of them is in the frame, and a reference
card or panel width would be measuring the screen.

A photograph or screenshot the OCR cannot read gets **no verdict**. The scan ends `failed`, with
no score, no declarations, no violations and no report file, and the scan page says so:

> **This scan could not be assessed.**
> Only 36 characters of text could be read from this screenshot, so this listing was not checked
> against the Rules. The screenshot may be blurry, cropped, or too low-resolution. Upload a
> clearer, full-size screenshot of the listing that includes the product details table.
>
> No verdict was reached. This is not a pass and not a failure.

The gate is the amount of text PP-OCR returned (`MIN_READABLE_CHARS` in
`worker/pipeline/__init__.py`), and the numbers behind the threshold are in the comment beside it.
It exists because an empty result scores 100 out of 100 by construction: without it a blurred
listing is reported as a compliant pack, or worse, accused of a Rule 6(10) breach it was never
read well enough to have.

## Checking the roles against the real database

`make test` proves what the app *draws* for each role. It cannot prove what Postgres *allows*, and
the UI is not the security boundary. This does:

```bash
make check-rls
```

`supabase/check_rls.py` signs in as all three demo users with the anon key and goes straight at
PostgREST and Storage — 53 checks, including every write a viewer must be refused and every audit
entry the triggers must write. It creates the rows it touches and deletes them at the end, so it
is safe to run against the project you are demoing. Exit code 1 if anything passes that should
not. Needs `NEXT_PUBLIC_SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`.

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

## Where the test images come from, and under what licence

`eval/dataset/` is 25 MB of images committed to this repo. They are not ours, and the terms
differ by prefix. Every case folder carries a `source.json` with its own URL, capture date and
licence line.

| Prefix | What | Source | Terms |
|---|---|---|---|
| `off_`, `obf_` | 31 cases, 102 photographs of Indian packaging | [Open Food Facts](https://world.openfoodfacts.org), [Open Beauty Facts](https://world.openbeautyfacts.org) | photographs **CC-BY-SA 3.0**, data ODbL. Redistributing them — which this repo does — carries the attribution and share-alike obligations that go with it. |
| `ecom_` | 6 product-listing screenshots | amazon.in, flipkart.com | **Not openly licensed.** Screenshots of public pages, kept as fixed test images. Fine for testing a compliance checker; if this repo is ever published or redistributed, look at these first — they are the ones with no licence behind them. |
| `synthetic_` | 18 rendered labels | `eval/make_synthetic.py` | ours |
| `phone_` | packs shot on a phone | ours | ours |

The report's own assets — the typeface and the five icons in the PDF — are a separate matter and
are listed with their licences in
[`worker/pipeline/templates/assets/README.md`](worker/pipeline/templates/assets/README.md). Both
are permissive (SIL OFL 1.1 and ISC), both are vendored so the report never fetches anything while
it renders, and `assets/fetch.sh` re-downloads them.

Nothing here is legal advice. The point is that the provenance is recorded per file rather than
assumed, so the decision is available to whoever has to make it. `eval/fetch_openfoodfacts.py`
and `eval/fetch_ecommerce.py` rebuild the whole set in a few minutes, so dropping the images from
git is a real option if that is the call.

## Without `make` (Windows)

Every Makefile target is one shell line. `scoop install make` if you want it. Otherwise copy the line.

## Eval

```bash
cd worker && uv run --extra ocr python ../eval/run_eval.py --label baseline-v1
```
Prints per-field precision/recall and violation accuracy; writes `eval/results/<date>_<label>.json`.
Every labelled run is kept in git — a measurement nobody can look up is not a measurement.
**`docs/EVAL.md` explains what the numbers mean, what the dataset can and cannot test, and every
run so far including the four changes that were measured and rejected.**

Diagnose a run without re-OCRing anything:

```bash
cd worker && uv run python ../eval/diagnose.py misses ../eval/results/2026-09-07_p2-final.json
cd worker && uv run python ../eval/diagnose.py reach  ../eval/results/2026-09-07_p2-final.json
cd worker && uv run python ../eval/error_report.py ../eval/results/<run>.json   # per-miss report, .md + .json
cd worker && uv run python ../eval/compare.py ../eval/results/<before>.json ../eval/results/<after>.json
```

`error_report.py` writes, for every real-photo miss, the gold value, the OCR line that best
covers it, the final value and the stage that lost it (OCR never detected it, printed with no
label, read but not grouped, misread, wrong neighbour). `compare.py` is how a labelled run is
judged: every changed field and violation set, marked better or worse against gold.

On Windows, run the worker's tests and the eval as `uv run --all-extras --no-sync …`: `--extra
pdf` and `--extra ocr` each re-sync the venv and uninstall the other's packages. Set
`PYTHONIOENCODING=utf-8` before printing gold values, or `₹` raises on the cp1252 console.

OCR is memoised under `eval/.ocr_cache/` on (image, languages, hash of `preprocess.py` + `ocr.py`),
so a rerun measures the change you made, not PaddleOCR reading 260 photos again. Edit either file
and the cache misses by itself; there is no flag to remember.

### Rebuilding the dataset

```bash
cd worker && uv run python ../eval/fetch_openfoodfacts.py --host food --count 60
cd worker && uv run python ../eval/fetch_ecommerce.py       # needs Chrome or Edge
```

The first pulls Indian package photographs from Open Food / Beauty Facts (CC-BY-SA 3.0); the
second screenshots public product listings with headless Chrome. Both only download images —
`gold.json` is written by reading the photograph, never by running the pipeline. See
`eval/dataset/README.md` for the conventions and for the shot list of the photos that still need
a camera and a reference card.
