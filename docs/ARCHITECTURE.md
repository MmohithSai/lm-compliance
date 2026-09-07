# ARCHITECTURE

## Data flow

```
Phone / laptop browser — Next.js PWA on Vercel
  1. login (Supabase Auth, email + password)
  2. resize photos to <= 1600 px on the client
  3. upload to Storage: scans/<scan_id>/<n>.jpg          (scan_id generated on the client)
  4. insert scans row (status = queued, source, has_reference_card, pdp_width_mm, pdp_height_mm)
     + one scan_images row per photo
  5. subscribe to Realtime on that scans row; show progress

Python worker — laptop / HF Space / Oracle VM, service-role key, talks *out* only
  loop every 3 s: rpc claim_scan()  -> one queued row flips to processing (atomic, skip locked)
    a. preprocess   OpenCV deskew + denoise
    b. scale        ArUco DICT_4X4_50 -> credit-card rectangle -> inspector PDP mm -> none
    c. ocr          PaddleOCR PP-OCRv4 -> words [text, box, confidence]      -> ocr_words
    d. extract      regex + keyword anchors + nearest-box layout -> declarations
    e. measure      height_mm, width/height ratio, contrast, same-panel grouping (only with scale)
    f. rules        rules/pc_rules_2011.yaml -> violations [rule_id, rule_ref, severity, message, evidence]
    g. score+report 100 - penalties; HTML -> PDF + DOCX + JSON -> Storage scans/<id>/report.*
    h. write back   declarations, violations, reports, scans.status = done | failed (+ error)

Supabase — Postgres + Auth + Storage + Realtime, RLS on every table
Dashboard — Next.js server components read the views directly under the caller's RLS
```

## Schema (see `supabase/migrations/0001_init.sql`)

profiles(role) · products · scans · scan_images · ocr_words · declarations · violations · reports · evidence · audit_log · model_calls.
Views: `dashboard_summary`, `top_violations` (30 days), `violations_by_category`. All `security_invoker`.
Function `claim_scan()` (service role only). Trigger: new auth user → profile with role `viewer`.

## RLS summary

| Role | profiles | products | scans / scan_images / evidence | pipeline tables | audit_log |
|---|---|---|---|---|---|
| viewer | read | read | read | read | — |
| inspector | read | read, insert, update own | read all, insert/update own | read | — |
| admin | all | all | all | read | read |
| service role (worker) | bypasses RLS | | | writes | |

Storage bucket `scans` (private): authenticated read; inspector/admin insert/update; admin delete.

## Why it is defensible

- The rule engine is deterministic and cites the rule. No AI decides compliance. No external AI API anywhere.
- Nothing is estimated: no scale reference → the font check says "not verifiable" and costs no points.
- Every part is open source and self-hostable. Rules live in a YAML file DoCA can edit without code.

## Deployment (₹0)

- Frontend: Vercel Hobby. Env: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- Supabase free tier. Pauses after 7 idle days — keep the worker polling, unpause before the demo. Photos resized to 1600 px to stay under 1 GB.
- Worker: one container from `worker/Dockerfile` on a Hugging Face Space (free CPU, Docker SDK; sleeps after ~48 h idle, first request wakes it; needs an HTTP listener on 7860 — a stdlib thread, P9) or an Oracle Always Free ARM VM. Laptop is the fallback. Env: `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.

## Scaling later

`claim_scan()` uses `for update skip locked`, so N worker containers can poll the same table safely. OCR is the only heavy step; a GPU worker would plug in at `ocr.py` with no other change. Storage and Postgres grow linearly with scans; the 1600 px cap keeps a scan under ~1 MB.
