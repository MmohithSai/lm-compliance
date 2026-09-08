-- P7. Dashboard, roles, audit.
--
-- Three things, and none of them recomputes an answer the pipeline already gave.
--
-- 1. `rules` is a mirror of rules/pc_rules_2011.yaml, written by the worker at start up
--    (`sync_rules` in worker/main.py). The dashboard needs a human name beside "D1", and the
--    only place that name exists is the YAML. Copying the titles into a migration would put a
--    second copy of the law in the repo, which this project has refused twice already; copying
--    them into the frontend would put a third. So the YAML stays the source and Postgres holds
--    a projection of it that the worker refreshes.
--
-- 2. The dashboard views. `dashboard_summary` and `top_violations` are rewritten and
--    `violations_by_category` is replaced by `scans_by_category`, because the dashboard counts
--    scans, not violations, when it asks how a category is doing. Every one is
--    `security_invoker`, so the caller's RLS still decides which scans they can see.
--
--    Compliant means `compliance_score = 100`: the score the worker stored, and the score the
--    PDF prints. The old view said "no critical or major violation", which let a minor one
--    through and disagreed with both. One definition, read off the stored column, never
--    recomputed here — the same rule P5 set for the report.
--
--    No view knows what "this week" means. That boundary depends on a timezone, it is the one
--    piece of dashboard arithmetic with an edge case worth testing, and it is tested in
--    frontend/lib/dashboard.ts. A `date_trunc('week', ...)` in here would be a second copy of it.
--
-- 3. Audit. `audit_log` has existed since 0001 with nowhere to put the values; it gets them
--    here, and three triggers that fill it. The triggers are on the tables, so a row written by
--    psql, by the worker or by a curl at the REST API is audited exactly like one written by the
--    frontend. There is deliberately no trigger on `audit_log` itself.

-- ---------------------------------------------------------------- the rule catalogue

create table if not exists public.rules (
  rule_id text primary key,
  rule_ref text not null,
  title text not null,
  severity text not null check (severity in ('critical', 'major', 'minor', 'info')),
  synced_at timestamptz not null default now()
);

alter table public.rules enable row level security;
-- Read by anyone signed in. No write policy at all: the worker writes it with the service role,
-- which bypasses RLS, and nobody else has any business editing the law from a browser.
drop policy if exists "rules read" on public.rules;
create policy "rules read" on public.rules for select to authenticated using (true);

-- ---------------------------------------------------------------- audit log

alter table public.audit_log
  add column if not exists old_row jsonb,
  add column if not exists new_row jsonb;

create index if not exists audit_log_at_idx on public.audit_log (at desc);
create index if not exists audit_log_row_idx on public.audit_log (table_name, row_id);

-- `security definer` so the insert lands even though `audit_log` has no insert policy: nobody
-- may write their own audit rows, and the trigger is the only thing that ever writes one.
--
-- `actor_id` is `auth.uid()`, which is null when the writer is the service role — that is the
-- worker, and null is the honest record of "not a person". `auth.uid()` is schema-qualified
-- because `search_path` is pinned to public.
--
-- An UPDATE stores only the keys that changed, old and new. A whole row on both sides would say
-- what the row is; the audit has to say what happened to it. An UPDATE that changed nothing
-- writes nothing.
create or replace function public.audit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  new_json jsonb;
  old_json jsonb;
  changed jsonb;
begin
  if tg_op = 'INSERT' then
    insert into public.audit_log (actor_id, action, table_name, row_id, new_row)
    values (auth.uid(), 'INSERT', tg_table_name, new.id::text, to_jsonb(new));
    return new;
  elsif tg_op = 'UPDATE' then
    new_json := to_jsonb(new);
    old_json := to_jsonb(old);
    select jsonb_object_agg(key, value) into changed
      from jsonb_each(new_json)
      where old_json -> key is distinct from value;
    if changed is null then
      return new;
    end if;
    insert into public.audit_log (actor_id, action, table_name, row_id, old_row, new_row)
    values (
      auth.uid(), 'UPDATE', tg_table_name, new.id::text,
      (select jsonb_object_agg(key, old_json -> key) from jsonb_each(changed)),
      changed
    );
    return new;
  else
    insert into public.audit_log (actor_id, action, table_name, row_id, old_row)
    values (auth.uid(), 'DELETE', tg_table_name, old.id::text, to_jsonb(old));
    return old;
  end if;
end
$$;

drop trigger if exists audit_scans on public.scans;
create trigger audit_scans after insert or update or delete on public.scans
  for each row execute function public.audit();

drop trigger if exists audit_products on public.products;
create trigger audit_products after insert or update or delete on public.products
  for each row execute function public.audit();

drop trigger if exists audit_evidence on public.evidence;
create trigger audit_evidence after insert or update or delete on public.evidence
  for each row execute function public.audit();

-- ---------------------------------------------------------------- dashboard views

drop view if exists public.dashboard_summary;
create view public.dashboard_summary
with (security_invoker = true) as
select
  count(*) as scans_total,
  count(*) filter (where s.status = 'done') as scans_done,
  count(*) filter (where s.status = 'failed') as scans_failed,
  count(*) filter (where s.status in ('queued', 'processing')) as scans_pending,
  -- A failed scan has no score and is never counted as compliant.
  count(*) filter (where s.status = 'done' and s.compliance_score = 100) as scans_compliant,
  round(avg(s.compliance_score) filter (where s.status = 'done'), 1) as avg_score,
  (select count(*) from public.violations where severity = 'critical') as violations_critical,
  (select count(*) from public.violations where severity = 'major') as violations_major,
  (select count(*) from public.violations where severity = 'minor') as violations_minor
from public.scans s;

-- `severity <> 'info'` drops the notes and every check that reported `unverifiable`: those cost
-- no points and accuse nobody, so they are not violations to rank.
drop view if exists public.top_violations;
create view public.top_violations
with (security_invoker = true) as
select
  v.rule_id,
  v.rule_ref,
  v.severity,
  r.title,
  count(*) as count,
  count(distinct v.scan_id) as scans
from public.violations v
left join public.rules r on r.rule_id = v.rule_id
where v.severity <> 'info'
group by v.rule_id, v.rule_ref, v.severity, r.title
order by count(*) desc, v.rule_id;

-- `category` is left null when the pack has no category on record. It is not coalesced to a
-- word here: "uncategorised" printed in a category column reads like a category, and the page
-- has to be able to say "not recorded" instead.
drop view if exists public.violations_by_category;
create view public.scans_by_category
with (security_invoker = true) as
select
  p.category as category,
  count(*) as scans,
  count(*) filter (where s.status = 'done') as scored,
  count(*) filter (where s.status = 'done' and s.compliance_score = 100) as compliant,
  round(avg(s.compliance_score) filter (where s.status = 'done'), 1) as avg_score
from public.scans s
left join public.products p on p.id = s.product_id
group by p.category
order by count(*) desc;

-- One row per scan with its violation counts already added up, so the recent list is one query
-- and not one query per scan.
create or replace view public.dashboard_recent_scans
with (security_invoker = true) as
select
  s.id,
  s.created_at,
  s.status,
  s.source,
  s.compliance_score,
  s.location,
  p.id as product_id,
  p.name as product_name,
  p.manufacturer as product_manufacturer,
  p.category,
  pr.full_name as inspector_name,
  count(v.id) filter (where v.severity = 'critical') as critical,
  count(v.id) filter (where v.severity = 'major') as major,
  count(v.id) filter (where v.severity = 'minor') as minor
from public.scans s
left join public.products p on p.id = s.product_id
left join public.profiles pr on pr.id = s.inspector_id
left join public.violations v on v.scan_id = s.id
group by s.id, p.id, pr.full_name
order by s.created_at desc;
