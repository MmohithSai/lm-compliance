-- lm-compliance: schema, RLS, storage bucket, dashboard views, realtime.
-- Apply: supabase link --project-ref <ref> && supabase db push

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- tables

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  full_name text,
  role text not null default 'viewer' check (role in ('admin', 'inspector', 'viewer')),
  created_at timestamptz not null default now()
);

create table public.products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  brand text,
  manufacturer text,
  category text,
  barcode text,
  created_by uuid references public.profiles (id),
  created_at timestamptz not null default now()
);

create table public.scans (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references public.products (id) on delete set null,
  inspector_id uuid not null references public.profiles (id),
  source text not null default 'package' check (source in ('package', 'ecommerce')),
  status text not null default 'queued' check (status in ('queued', 'processing', 'done', 'failed')),
  error text,
  has_reference_card boolean not null default false,
  pdp_width_mm numeric,
  pdp_height_mm numeric,
  mm_per_px numeric,
  compliance_score int check (compliance_score between 0 and 100),
  notes text,
  location text,
  created_at timestamptz not null default now(),
  finished_at timestamptz
);
create index scans_status_created_idx on public.scans (status, created_at);
create index scans_inspector_idx on public.scans (inspector_id);
create index scans_product_idx on public.scans (product_id);

create table public.scan_images (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid not null references public.scans (id) on delete cascade,
  storage_path text not null,
  kind text not null default 'front' check (kind in ('front', 'back', 'other', 'evidence')),
  width int,
  height int,
  created_at timestamptz not null default now()
);
create index scan_images_scan_idx on public.scan_images (scan_id);

create table public.ocr_words (
  id bigint generated always as identity primary key,
  scan_id uuid not null references public.scans (id) on delete cascade,
  image_id uuid not null references public.scan_images (id) on delete cascade,
  text text not null,
  x int not null,
  y int not null,
  w int not null,
  h int not null,
  confidence numeric not null
);
create index ocr_words_scan_idx on public.ocr_words (scan_id);

create table public.declarations (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid not null references public.scans (id) on delete cascade,
  field text not null,
  value text not null,
  confidence numeric,
  word_ids bigint[] not null default '{}',
  image_id uuid references public.scan_images (id) on delete set null,
  height_mm numeric,
  width_height_ratio numeric,
  extractor text not null default 'regex_layout'
);
create index declarations_scan_idx on public.declarations (scan_id);

create table public.violations (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid not null references public.scans (id) on delete cascade,
  rule_id text not null,
  rule_ref text not null,
  severity text not null check (severity in ('critical', 'major', 'minor', 'info')),
  message text not null,
  evidence jsonb not null default '{}'::jsonb,
  confidence numeric
);
create index violations_scan_idx on public.violations (scan_id);
create index violations_rule_idx on public.violations (rule_id);

create table public.reports (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid not null references public.scans (id) on delete cascade,
  pdf_path text,
  docx_path text,
  json_path text,
  created_at timestamptz not null default now()
);

create table public.evidence (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid not null references public.scans (id) on delete cascade,
  storage_path text,
  note text,
  created_by uuid not null references public.profiles (id),
  created_at timestamptz not null default now()
);

create table public.audit_log (
  id bigint generated always as identity primary key,
  actor_id uuid,
  action text not null,
  table_name text not null,
  row_id text,
  at timestamptz not null default now()
);

-- For the optional local-model extractor (stretch). Empty until then.
create table public.model_calls (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid references public.scans (id) on delete cascade,
  model text not null,
  prompt_hash text,
  input_tokens int,
  output_tokens int,
  latency_ms int,
  output jsonb,
  at timestamptz not null default now()
);

-- ---------------------------------------------------------------- functions & triggers

-- Role of the calling user. security definer so RLS policies can read profiles without recursion.
create or replace function public.auth_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select role from public.profiles where id = auth.uid()
$$;

-- Every new auth user gets a profile with role 'viewer'. Admin promotes.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, role)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'full_name', new.email), 'viewer');
  return new;
end
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

-- Atomic claim for the worker. Service role only.
create or replace function public.claim_scan()
returns setof public.scans
language sql
as $$
  update public.scans
  set status = 'processing'
  where id = (
    select id from public.scans
    where status = 'queued'
    order by created_at
    limit 1
    for update skip locked
  )
  returning *
$$;
revoke all on function public.claim_scan() from public, anon, authenticated;
grant execute on function public.claim_scan() to service_role;

-- ---------------------------------------------------------------- row level security
-- viewer: select only. inspector: select all, write own scans/images/evidence/products. admin: all.
-- Pipeline tables (ocr_words, declarations, violations, reports, model_calls) are written by the
-- worker with the service role, which bypasses RLS.

alter table public.profiles enable row level security;
alter table public.products enable row level security;
alter table public.scans enable row level security;
alter table public.scan_images enable row level security;
alter table public.ocr_words enable row level security;
alter table public.declarations enable row level security;
alter table public.violations enable row level security;
alter table public.reports enable row level security;
alter table public.evidence enable row level security;
alter table public.audit_log enable row level security;
alter table public.model_calls enable row level security;

create policy "profiles read" on public.profiles for select to authenticated using (true);
create policy "profiles admin all" on public.profiles for all to authenticated
  using (public.auth_role() = 'admin') with check (public.auth_role() = 'admin');

create policy "products read" on public.products for select to authenticated using (true);
create policy "products insert" on public.products for insert to authenticated
  with check (public.auth_role() in ('inspector', 'admin') and created_by = auth.uid());
create policy "products update" on public.products for update to authenticated
  using (public.auth_role() = 'admin' or (public.auth_role() = 'inspector' and created_by = auth.uid()));
create policy "products delete" on public.products for delete to authenticated
  using (public.auth_role() = 'admin');

create policy "scans read" on public.scans for select to authenticated using (true);
create policy "scans insert" on public.scans for insert to authenticated
  with check (public.auth_role() in ('inspector', 'admin') and inspector_id = auth.uid());
create policy "scans update" on public.scans for update to authenticated
  using (public.auth_role() = 'admin' or (public.auth_role() = 'inspector' and inspector_id = auth.uid()));
create policy "scans delete" on public.scans for delete to authenticated
  using (public.auth_role() = 'admin');

create policy "scan_images read" on public.scan_images for select to authenticated using (true);
create policy "scan_images insert" on public.scan_images for insert to authenticated
  with check (
    public.auth_role() = 'admin'
    or (
      public.auth_role() = 'inspector'
      and exists (select 1 from public.scans s where s.id = scan_id and s.inspector_id = auth.uid())
    )
  );
create policy "scan_images delete" on public.scan_images for delete to authenticated
  using (public.auth_role() = 'admin');

create policy "evidence read" on public.evidence for select to authenticated using (true);
create policy "evidence insert" on public.evidence for insert to authenticated
  with check (public.auth_role() in ('inspector', 'admin') and created_by = auth.uid());
create policy "evidence update" on public.evidence for update to authenticated
  using (public.auth_role() = 'admin' or (public.auth_role() = 'inspector' and created_by = auth.uid()));
create policy "evidence delete" on public.evidence for delete to authenticated
  using (public.auth_role() = 'admin');

create policy "ocr_words read" on public.ocr_words for select to authenticated using (true);
create policy "declarations read" on public.declarations for select to authenticated using (true);
create policy "violations read" on public.violations for select to authenticated using (true);
create policy "reports read" on public.reports for select to authenticated using (true);
create policy "model_calls read" on public.model_calls for select to authenticated
  using (public.auth_role() = 'admin');
create policy "audit_log read" on public.audit_log for select to authenticated
  using (public.auth_role() = 'admin');

-- ---------------------------------------------------------------- storage

insert into storage.buckets (id, name, public)
values ('scans', 'scans', false)
on conflict (id) do nothing;

create policy "scans bucket read" on storage.objects for select to authenticated
  using (bucket_id = 'scans');
create policy "scans bucket insert" on storage.objects for insert to authenticated
  with check (bucket_id = 'scans' and public.auth_role() in ('inspector', 'admin'));
create policy "scans bucket update" on storage.objects for update to authenticated
  using (bucket_id = 'scans' and public.auth_role() in ('inspector', 'admin'));
create policy "scans bucket delete" on storage.objects for delete to authenticated
  using (bucket_id = 'scans' and public.auth_role() = 'admin');

-- ---------------------------------------------------------------- dashboard views
-- security_invoker: the caller's RLS applies (everyone can read scans, so everyone sees stats).

create view public.dashboard_summary
with (security_invoker = true) as
select
  count(*) filter (where s.created_at >= now() - interval '7 days') as scans_this_week,
  count(*) filter (where s.status = 'done') as scans_done,
  count(*) filter (where s.status = 'failed') as scans_failed,
  count(*) filter (
    where s.status = 'done'
      and not exists (
        select 1 from public.violations v
        where v.scan_id = s.id and v.severity in ('critical', 'major')
      )
  ) as scans_compliant,
  round(avg(s.compliance_score) filter (where s.status = 'done'), 1) as avg_score
from public.scans s;

create view public.top_violations
with (security_invoker = true) as
select v.rule_id, v.rule_ref, v.severity, count(*) as count
from public.violations v
join public.scans s on s.id = v.scan_id
where s.created_at >= now() - interval '30 days'
  and v.severity <> 'info'
group by v.rule_id, v.rule_ref, v.severity
order by count desc;

create view public.violations_by_category
with (security_invoker = true) as
select coalesce(p.category, 'uncategorised') as category, v.severity, count(*) as count
from public.violations v
join public.scans s on s.id = v.scan_id
left join public.products p on p.id = s.product_id
where v.severity <> 'info'
group by 1, 2
order by 1, 2;

-- ---------------------------------------------------------------- realtime

alter publication supabase_realtime add table public.scans;
