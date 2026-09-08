# AUDIT — P0 to P8 against the implementation, 2026-09-08

What this is: every requirement of phases P0–P8 checked against the code, the migrations, the
tests, the eval data and the hosted project, not against `docs/PROGRESS.md`. Then the P2
real-photo number taken apart miss by miss and improved where the evidence supported it.

Statuses: **PASS** · **PARTIAL** · **FAIL** · **UNVERIFIED** (needs a person or a run this audit
could not make).

Hosted verification was done two ways: read-only SQL against project `jcjxukjgrbmkuydpsnuc`
through the Supabase MCP server, and `make check-rls` (three real signed-in sessions at PostgREST
and Storage), re-run at the end of the audit.

---

## The short version

- **Strong:** the rule engine (reproduces all 56 gold verdicts from gold declarations), the RLS
  and audit layer (53 of 53 hosted checks, inspected one by one), the report path (one model,
  three files, score never recomputed), the unreadable-scan gate, and the measurement discipline
  (every claim has a result file; the baseline reproduced byte for byte).
- **Weak:** real-photo extraction. It was **30.5%** and is **44.0%** after nine measured changes
  in this audit; the 70% target is not met and the remaining 79 misses are mostly the OCR step
  (23 never detected, 9 misread) and a structural gap (20 unlabelled generic names).
- **Fixed:** one genuine P1 defect — the worker read photographs in whatever order Postgres
  returned them, which the reversed-image experiment showed changes 7 of 37 multi-image cases
  and flips a D5 verdict. Plus the extractor changes below.
- **Left as findings:** D5b is unreachable from the extractor; product matching merges every
  unnamed pack of one company into one product; a crashed worker leaves a scan `processing`
  forever; three gold files are questionable; a VLM is justified for one field only.

---

## Audit matrix

### P0 — dataset + eval harness

| # | Requirement | Implementation | Tests | Hosted | Status | Evidence |
|---|---|---|---|---|---|---|
| 1 | Harness runs, writes a result file | `eval/run_eval.py` | — | n/a | PASS | `2026-09-08_audit-baseline.json` |
| 2 | Real photographs + listing screenshots | 31 OFF/OBF + 6 listings + 1 phone = 38 real cases, 141 gold declarations | `test_dataset.py` (image present) | n/a | PASS | `eval/dataset/` |
| 3 | Gold per case, written from the photograph | 56 `gold.json` | 5 checks × 56, engine reproduces all 56 verdicts | n/a | PARTIAL | three files questionable, see Gold below |
| 4 | Photos with a reference card, two panels, two MRPs | none | — | n/a | FAIL (blocked) | needs a person; unchanged since P0 |
| 5 | Synthetic labels | 16 + 2 marker cases | dataset tests | n/a | PASS | `make_synthetic.py` |
| 6 | Gold validated automatically | `test_dataset.py` | 280 checks | n/a | PASS | |
| 7 | OCR memoised so a rerun measures the change | `eval/.ocr_cache`, fingerprint of `preprocess.py`+`ocr.py` | — | n/a | PASS | 913 entries, one eval ≈ 60 s |
| 8 | Synthetic and real reported apart | `field_accuracy_by_source` | — | n/a | PASS | |
| 9 | Reported numbers reproducible | `audit-baseline` | — | n/a | PASS | identical to `p8-consumer-care-needs-a-contact` on every key except label/date |
| 10 | Eval distinguishes extraction errors from physically missing information | by convention gold omits what the frame cut off; `eval/error_report.py` now splits misses into OCR-never-detected / unlabelled / not-grouped / misread / wrong-neighbour | — | n/a | PARTIAL | the convention is applied unevenly (Haldiram), and "physically cropped" cannot be told from "OCR missed" without a person; the report names the OCR-missed bucket honestly rather than calling it cropped |

### P1 — schema, auth, upload, worker loop

| # | Requirement | Implementation | Tests | Hosted | Status | Evidence |
|---|---|---|---|---|---|---|
| 1 | Tables, RLS, bucket, views, realtime, `claim_scan()` | `0001`–`0006` | — | all six migrations applied | PASS | `list_migrations` |
| 2 | Auth, three roles | `profiles.role`, `auth_role()`, `handle_new_user` | `roles.test.ts` | `check_rls.py` | PASS | 53/53 |
| 3 | Storage policies | private bucket; inspector/admin insert | — | viewer upload refused, anon URL 400 | PASS | check-rls |
| 4 | Upload form, camera, resize ≤ 1600 px | `app/upload` | — | phone run 2026-09-07 | PASS | not re-run in a browser this audit |
| 5 | Realtime status | `scan-realtime.tsx` | — | 2026-09-07 | UNVERIFIED this audit | code present; not exercised today |
| 6 | Worker polls, claims one, `processing` → `done`/`failed` | `main.py`, `claim_scan` skip-locked | `test_run_scan.py`, `test_unreadable.py` | scans on the project | PASS | |
| 7 | **Deterministic image order** | `run_scan` had no `order by`; extractor sorted by `image_id` (a uuid on a real scan) | new regression tests (fake rows seeded back to front; cross-image order) | not re-run on hosted | **FAIL → FIXED** `290070d` | reversed-image experiment: 7/37 cases change, 9 declarations, 1 D5 verdict flips |
| 8 | Failure handling | exception → `failed` + message; `UnreadableScan` verbatim | 15 tests | `916562a7` | PASS | |
| 9 | Idempotency / retry | none | — | — | PARTIAL | a worker crash after `claim_scan` leaves the scan `processing` forever; no `started_at`, no requeue; `store()` is not idempotent, but no re-run path exists. Proposed: a `started_at` column and a requeue of `processing` rows older than 10 min at claim time (migration, P9) |
| 10 | Scan ↔ image relationship | `scan_images.scan_id`, paths `<scan>/<n>.jpg` | | 15 rows / 6 scans | PASS | |

### P2 — OCR + extractor

| # | Requirement | Implementation | Tests | Hosted | Status | Evidence |
|---|---|---|---|---|---|---|
| 1 | Preprocess | bilateral + CLAHE | — | | PASS | measured (`p2-real-clahe`) |
| 2 | OCR → line boxes | PP-OCRv4 | — | 812 `ocr_words` rows | PASS | |
| 3 | Extractor | `regex_layout.py` | 58 tests | | PASS | |
| 4 | `run_local` wired | | | | PASS | |
| 5 | Measured on real photographs, one variable per run | 11 labelled runs this audit | | | PASS | `docs/EVAL.md` |
| 6 | ≥ 70% field extraction | **44.0% real**, 98.4% synthetic | | | **FAIL** | was 30.5%; see below |

### P3 — rule engine + detail page

| # | Requirement | Implementation | Tests | Hosted | Status | Evidence |
|---|---|---|---|---|---|---|
| 1 | All 20 checks | `CHECKS` | 115 rule tests | | PASS | |
| 2 | Applicability, Rule 6(10) on a listing, physical rules excluded | `_applies` | `test_rules_applicability.py` | `eedd5753`: E1 only, no F/P finding | PASS | |
| 3 | Exemptions X1–X4 | `EXEMPT_WHEN`, `SKIPS_THE_RULE` | | | PASS | |
| 4 | Evidence boxes | `word_ids` remapped to Postgres ids | `test_store_remaps_word_ids…` | | PASS | |
| 5 | Scoring | 100 − 25/10/3, floor 0; `unverifiable` and `info` cost nothing | | | PASS | |
| 6 | Pass / fail / unverifiable semantics | | | | PASS | |
| 7 | Gold verdicts reproduced from gold declarations | | 56/56 | | PASS | |
| 8 | Extraction failures do not create violations | — | | | PARTIAL, by design | a field the extractor misses is reported missing: D1–D8 fire on absence. Violation precision 0.77 means about a quarter of scored violations are extraction misses. The unreadable gate covers the extreme case; nothing covers the middle. This is the honest shape of the system and it is now written down |
| 9 | D5b one MRP only | `_single_mrp` | unit-tested | | PARTIAL | **unreachable**: the extractor emits at most one declaration per field, so the engine never sees two MRPs. Fix when two-MRP photographs exist |
| 10 | Detail page: boxes, declarations, violations, score | `scans/[id]/page.tsx` | build + tsc | browser-checked in P5–P8 | PASS | panels now in upload order (`5eaffbe`) |

### P4 — scale, font, contrast, grouping

| # | Requirement | Implementation | Tests | Hosted | Status | Evidence |
|---|---|---|---|---|---|---|
| 1 | ArUco → mm/px | `measure.py` | marker cases: 0.1253 vs true 0.1250 | | PASS | |
| 2 | Card → mm/px | gated on the inspector's checkbox | | | PASS | ungated it claimed 14 card-less frames |
| 3 | Inspector PDP mm fallback | | | | PASS | assumes the panel fills the frame; the form says so |
| 4 | Height, width ratio, contrast per declaration | `ink()` on the raw image | `test_measure.py` | | PASS | |
| 5 | Unknown scale → `unverifiable`, never a failure | | eval: 54 photographs all unverifiable, 0 points | | PASS | |
| 6 | Scale per photograph, never borrowed | | | | PASS | |
| 7 | Grouping P1 | passes or unverifiable; no failure side | | | PARTIAL, by design | a scale cannot tell two photographs apart |
| 8 | Font check correct on 5 real photos with a card | — | — | — | UNVERIFIED | needs a person with a card; glare, focus and perspective untested |
| 9 | Contrast stored | not stored (`store()` drops it) | | | PARTIAL | in the violation's evidence when P2 fails; add the column if a report wants it |

### P5 — reports

| # | Requirement | Implementation | Tests | Hosted | Status | Evidence |
|---|---|---|---|---|---|---|
| 1 | PDF, DOCX, JSON from one model | `build_report` → three renderers | `test_report.py`, PDF test runs with GTK (577 passed, 0 skipped) | 3 `reports` rows | PASS | |
| 2 | One report per scan, overwritten in place | `0002` unique index, upsert | | `reports_scan_key` | PASS | |
| 3 | Signed URLs, download names | `scan-reports.tsx` | tsc | fetched 200 in P5 | PASS | not re-fetched today |
| 4 | Report reflects the stored result | built from the same in-memory result `store()` wrote; score read, never recomputed | test pins a forged score | | PASS | |
| 5 | Evidence images | boxes burned in, 900 px | | | PASS | |
| 6 | Notes | `scans.notes` printed | | | PASS | |
| 7 | Failure behaviour | per-format try/except; null path | test | | PARTIAL | if the `reports` upsert itself raises after `store()`, the scan is marked `failed` with its rows already written — no transaction across the two. Rare; noted |
| 8 | Fonts, assets, licences | IBM Plex Sans (OFL), Lucide (ISC), vendored, README | | | PASS | |
| 9 | No forbidden or random imagery | no emblem; a balance-scale icon | | | PASS | |

### P6 — repository, search, history, evidence

| # | Requirement | Implementation | Tests | Hosted | Status | Evidence |
|---|---|---|---|---|---|---|
| 1 | Product matching | `match_key` = 2 company words \| 4 name words, unique upsert | `test_product.py` | 3 products | **PARTIAL** | **wrong-merge risk:** a pack with no generic name (printed none, or OCR missed it — 21 of 41 gold generic names are missed today) gets key `company\|`, so every unnamed pack of a company files under one product. Not yet triggered on the hosted project. Proposed: no product row without a generic name, or company + net quantity as the key; the owner's call |
| 2 | Normalisation | label words, legal forms, commas | 12 tests | | PASS | |
| 3 | Search | `scan_search` view, `ilike` | | viewer reads it | PASS | |
| 4 | Date filters, history, average score | `/scans`, `/products/[id]` | | | PASS | code + build; not opened today |
| 5 | Evidence photos, notes, RLS | `evidence`, `0004` | `evidence.test.ts` | 13 refusals/allowances | PASS | |
| 6 | Evidence never reprocessed as a scan image | separate table; worker reads `scan_images` only | | | PASS | |

### P7 — dashboard, roles, audit

| # | Requirement | Implementation | Tests | Hosted | Status | Evidence |
|---|---|---|---|---|---|---|
| 1 | Summary, compliance rate, top violations, categories, recent | four `security_invoker` views | `dashboard.test.ts` | admin reads all four; failed-is-not-compliant delta test | PASS | |
| 2 | Compliance = score 100; failed in neither half | `dashboard_summary` | | +1 failed/+1 done/+1 compliant/+2 total | PASS | |
| 3 | Viewer restrictions | nav + server layout + RLS | | 13 writes, 13 refused; scan and evidence byte-identical | PASS | |
| 4 | Inspector / admin behaviour | | | inspector cannot edit another's scan, delete, or read audit; admin reads everything | PASS | |
| 5 | Audit triggers, actor, old/new, no recursion | `audit()` definer, three triggers, none on `audit_log` | | INSERT whole row, UPDATE changed keys only, DELETE whole row; service-role write recorded with null actor; `audit_log` never audits itself | PASS | |
| 6 | Definer functions off the public API | `0006` | | security advisor: only `auth_role()` executable by `authenticated`, by design | PASS | leaked-password protection is a dashboard switch — UNVERIFIED, owner's |
| 7 | Performance advisories | read | | 5 unindexed FKs, 7 `auth.<fn>()` initplan policies, 1 multiple-permissive on `profiles` | known, accepted | not real at six scans |

### P8 — e-commerce mode, unreadable scans

| # | Requirement | Implementation | Tests | Hosted | Status | Evidence |
|---|---|---|---|---|---|---|
| 1 | Empty / weak OCR refused before anything is written | `unreadable()`, `MIN_READABLE_CHARS = 80` | 15 tests | `916562a7`: `failed`, the sentence in `error`, 0 rows in `ocr_words`, `declarations`, `violations`, `reports` | PASS | |
| 2 | No false compliance, no report for a failed scan | | | as above | PASS | |
| 3 | Source-aware: Rule 6(10) only, physical rules never applied | `_applies` | | `eedd5753`: `done`, 75, one `E1 / Rule 6(10) / critical`, three report files | PASS | |
| 4 | Consumer-care false positive | `CONTACT` | | all six listings give gold's E1 | PASS | |
| 5 | Blurred screenshot | | | `916562a7` | PASS | |
| 6 | Image-order note left by P8 | | | | FIXED | see P1 item 7 |

---

## The P1 ordering investigation

`run_scan` selected `scan_images` with no `order by`, and the extractor sorted words by
`(image_id, y, x)`. In the eval `image_id` is the file stem and sorts like the upload; on a real
scan it is a uuid. So "first box in reading order wins" was decided across photographs by row
order on the hosted worker and by chance of uuid everywhere else — and the eval could not see it.

Measured before fixing: every multi-image real case run with its images forward and reversed.

| | |
|---|---|
| multi-image real cases | 37 |
| cases whose declarations or verdict change with order | 7 |
| declarations that differ | 9 |
| violation sets that differ | 1 — the Ching's soy sauce, D5 (critical, 25 points) |

Fix (`290070d`): `order("storage_path")` in `run_scan`, and the extractor keeps images in the
order it was handed. Regression tests seed the fake rows back to front and hand the extractor two
images whose ids sort against their order. Eval byte-identical. Then `3e43979` made the three
address fields take the fullest candidate, so those fields no longer depend on order at all.

---

## P2 — where the 30.5% came from, and what moved

### Baseline (reproduced)

Field accuracy 62.5%; real 30.5% (43 of 141); synthetic 98.4%; violations precision 0.741,
recall 0.986, exact-set 51.8%.

### Failure taxonomy, baseline, 98 misses over 38 real cases

| Category | Misses | Share |
|---|---|---|
| 7. Printed with no label to anchor on | 26 | 27% |
| 1. OCR did not detect the text | 23 | 23% |
| 2. Read, but spread over boxes the extractor did not group | 18 | 18% |
| 11. Anchor took the wrong neighbouring box | 15 | 15% |
| 6. Wrapped value cut short or over-merged | 9 | 9% |
| 4. Character errors on the line used | 7 | 7% |
| spurious predictions (gold has no such field) | 13 | — |

Category 12 (physically cropped) is empty by construction: gold omits what the frame cut off.
Where a declaration is legible to a person and PP-OCR did not return its words, it is counted as
1, not 12. Category 13 (image order) affected 7 cases, measured above. Category 15 (genuinely
ambiguous) covers about 6 rows: two Amazon MRP conventions, three packs printing both a
manufacturer and a marketer, one Muuchstac block.

### What the bottleneck is

Not one thing. Of 98 misses, 30 were the OCR step (23 never detected + 7 misread), 26 were
structural (no label), and 42 were the extractor's — layout, neighbour, wrap. The 42 were
attacked first because they were reachable without re-OCRing the set.

### Changes made, one labelled run each

| Run | Change | Real | Better / worse |
|---|---|---|---|
| `p2-padded-boxes-may-overlap` | slack for PP-OCR's padded boxes | 31.9% | 2 / 1 — kept only with the next |
| `p2-a-figure-has-a-shape` | a price looks like a price, a date like a date; a bare label claims nothing | 31.9% | 10 / 1 |
| `p2-a-label-may-be-two-lines` | two-line label cells; below-right after the cell test; a figure is one label's value | 35.5% | 7 / 1 |
| `p2-ocr-drops-spaces` | anchors survive dropped spaces; "usp", "date of mfg", "Quantity"@start; fuller label beats a bare noun | 36.9% | 2 / 0 |
| `p2-an-address-block-ends-at-the-licence-number` | licence / FSSAI / storage lines skipped; care block keeps "same as … address" | 37.6% | 1 / 0 |
| `p2-the-fullest-address-block-wins` | address fields take the fullest candidate; an anchor box already read is done | 39.0% | 3 / 1 |
| `p2-a-unit-price-by-its-shape` | unlabelled "<amount> per <unit>" | 42.6% | 5 / 1 |
| `p2-best-before-wraps-one-line` | one digit-less line under "best before" | 43.3% | 1 / 0 |
| `eval-accents-are-folded-like-the-rupee-sign` | measurement: NFKD | 44.0% | 1 / 0 |

### Per-field, baseline → final

| Field | precision | recall | tp | fp | fn |
|---|---|---|---|---|---|
| best_before | 0.69 → 1.00 | 0.69 → 0.76 | 20→22 | 9→0 | 9→7 |
| consumer_care | 0.81 → 0.74 | 0.59 → 0.59 | 17→17 | 4→6 | 12→12 |
| country_of_origin | 0.75 → 1.00 | 0.55 → 0.73 | 6→8 | 2→0 | 5→3 |
| generic_name | 0.95 → 0.95 | 0.47 → 0.47 | 19→19 | 1→1 | 21→21 |
| importer | 0.33 → 0.67 | 0.33 → 0.67 | 1→2 | 2→1 | 2→1 |
| manufacturer | 0.44 → 0.58 | 0.41 → 0.52 | 12→15 | 15→11 | 17→14 |
| mfg_date | 0.73 → 0.83 | 0.76 → 0.76 | 19→19 | 7→4 | 6→6 |
| mrp | 0.71 → 0.85 | 0.67 → 0.77 | 20→23 | 8→4 | 10→7 |
| net_quantity | 0.88 → 0.91 | 0.80 → 0.85 | 37→39 | 5→4 | 9→7 |
| unit_sale_price | 1.00 → 0.96 | 0.64 → 0.88 | 16→22 | 0→1 | 9→3 |

Totals: field accuracy 62.5% → 69.7%; real **30.5% → 44.0%**; synthetic 98.4% → 98.4%;
violations precision 0.741 → 0.774, recall 0.986 → 0.993, exact-set 51.8% → 53.6%; 26 fields
better, 1 worse (the sideways Ching's use-by), 16 changed but still wrong; spurious 13 → 6.

### Taxonomy after, 79 misses

| Category | Misses | Share |
|---|---|---|
| 1. OCR did not detect the text | 23 | 29% |
| 7. Printed with no label | 20 | 25% |
| 2. Read but not grouped | 17 | 22% |
| 4. Character errors | 9 | 11% |
| 11. Wrong neighbour | 8 | 10% |
| 6. Wrapped | 2 | 3% |

The extractor's own buckets fell from 42 to 27; the OCR buckets are unchanged at 32 because no
OCR setting was touched (a change there invalidates the cache and costs a 30-minute re-read).

### Is a VLM justified?

For **one field, yes**: 20 of the 79 misses are a generic name printed with no label, which no
anchor extractor can reach, and D2 is a major violation. The Stretch item as planned — a local
Qwen2.5-VL behind `EXTRACTOR=local_vlm`, measured against this baseline, logged in
`model_calls` — is the right experiment for that bucket, and this baseline is the bar.

For the rest, **no, not yet**. 32 misses are the OCR step: print PP-OCRv4's detector never
returned (small white print on curved bottles, a tilted jar, sachet print a dozen pixels high,
sideways text) or misread. A VLM reading the same 1600 px photograph faces the same twelve-pixel
print. The next experiments there are OCR-side and deterministic: a second detection pass at 90°
*merged* with the upright pass (the earlier rejection replaced the page and lost the rest), and
`det_limit_side_len=1600` re-measured now that the extractor tolerates split lines. Both need a
full re-OCR of the set; neither was run in this audit. Recommendation: run those two before the
VLM, each as its own labelled run.

---

## Gold files to review (not changed)

- `off_haldiram_phalhari_chiwda_8904004402261`: the photograph prints "MRP: ₹ 10.00 (Incl. of
  all taxes)", "USP: ₹ 0.25 per g", a consumer care block with phone and e-mail, and "Marketed
  By: HALDIRAM FOODS INTERNATIONAL PVT. LTD., Plot No. 145/146, …", each with its first letter
  under a fold. Gold records none of them and expects D5, D6, D8 (and D1). An inspector would not
  cite D5 on that pack. If corrected, four violations move.
- Amazon MRP convention: `ecom_amazon_parle_g_800g` and `ecom_amazon_parle_krackjack` take the
  displayed price (₹90, ₹128) as the MRP while the listing's own struck-through "M.R.P" row is
  what the extractor finds; `ecom_amazon_britannia_tiger` has no MRP in gold though the tile
  prints one. One convention should be chosen and applied to all six.
- Manufacturer vs marketer: `obf_cetaphil_moisturising_lotion`, `obf_muuchstac…` and
  `off_pepsi_cola_pepsi` print both; gold takes the marketer on two and the manufacturer on
  one. The extractor now takes whichever carries an address, else the longer. Both are valid
  D1 subjects; the field-level match is a coin toss until gold says which.
- `ecom_amazon_parle_g_800g` prints "Mfg. Date: 21/12/17" and "Exp. Date: 5 months" in its
  details table; gold omits both, so they count as spurious.

---

## Remaining issues, in priority order

1. Real-photo extraction 44.0% against 70%. OCR-side experiments above; VLM for generic names.
2. Product matching merges unnamed packs of one company (P6). Needs a decision.
3. A crashed worker leaves a scan `processing` forever (P1). Needs `started_at` + requeue (P9).
4. D5b unreachable until two-MRP photographs exist and the extractor emits a second MRP.
5. Sideways photographs: label/value geometry transposed; a per-box orientation rule is the
   extractor-side experiment.
6. Five real photographs with a reference card are still owed to P4; F1/F2/P2 have never run on
   a photograph.
7. Leaked-password protection is off on the hosted Auth (dashboard switch).
8. `reports` upsert after `store()` is not transactional (P5); rare.

## Ready for P9

The pipeline is deterministic end to end and the same on the hosted worker as in the eval, the
security layer is proved against the real database, every number in the docs has a result file,
and nothing invents a measurement or a verdict. The Docker image, model baking and a health
thread are P9's own work. What P9 should not promise is 70% on real photographs.

Final validation, 2026-09-08: worker 577 passed (PDF tests running), frontend 29 passed;
ruff, ruff format, mypy, tsc, eslint, `pnpm build` clean; `make check-rls` 53 of 53.
