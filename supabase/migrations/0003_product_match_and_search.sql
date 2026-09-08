-- P6. Two things the repository needs: an identity for a pack, and one place to search from.
--
-- `products.match_key` is that identity: the company that made the pack plus what the pack says
-- it is, both normalised (see worker/pipeline/product.py). The worker upserts on it, so a second
-- photograph of the same product lands on the row the first one made instead of beside it.
-- Unique, and nullable for the rows a person creates by hand, which Postgres leaves alone.
--
-- `scan_search` is the search page's only query: one flattened row per scan with a `search`
-- column holding every word a person would type — product, brand, maker, inspector, place, note,
-- scan id. `ilike '%parle%'` over that beats five joined filters in the client, and the view is
-- security_invoker so the caller's RLS still decides which scans they are.

alter table public.products add column if not exists match_key text;
create unique index if not exists products_match_key on public.products (match_key);

create view public.scan_search
with (security_invoker = true) as
select
  s.id,
  s.created_at,
  s.finished_at,
  s.status,
  s.source,
  s.compliance_score,
  s.location,
  s.inspector_id,
  s.product_id,
  p.name as product_name,
  p.brand as product_brand,
  p.manufacturer as product_manufacturer,
  pr.full_name as inspector_name,
  concat_ws(
    ' ',
    p.name, p.brand, p.manufacturer, p.category,
    pr.full_name,
    s.location, s.notes,
    s.id::text
  ) as search
from public.scans s
left join public.products p on p.id = s.product_id
left join public.profiles pr on pr.id = s.inspector_id;
