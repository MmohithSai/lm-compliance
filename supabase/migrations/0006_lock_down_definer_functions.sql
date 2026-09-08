-- P7. Three `security definer` functions were reachable at /rest/v1/rpc/<name> by anyone with
-- the anon key, and one of them was new in 0005. Supabase's security advisor found it.
--
-- None of the three is meant to be called by hand. `audit()` and `handle_new_user()` are trigger
-- functions: called directly they have no NEW record and raise, so the exposure buys an attacker
-- an error message rather than a write. `auth_role()` returns the caller's own role and leaks
-- nothing. So this is not a hole that was open — it is a door that should never have been in the
-- wall, and `claim_scan()` in 0001 already showed how to take it out.
--
-- Postgres checks EXECUTE on a trigger function when the trigger is created, not when it fires,
-- so the triggers keep working with no grant at all. Verified after pushing: `supabase/check_rls.py`
-- still records every insert, update and delete, and a fresh auth user still gets a profile.

revoke all on function public.audit() from public, anon, authenticated;
revoke all on function public.handle_new_user() from public, anon, authenticated;

-- `auth_role()` is the one that cannot simply be revoked from PUBLIC and left there. Every RLS
-- policy in 0001 calls it, and a policy expression is evaluated as the signed-in user, so
-- without an EXECUTE grant of its own `authenticated` would lose the right to call the function
-- its own policies depend on — and every write in the app would start failing. Revoke the blanket
-- grant, then hand it back to exactly the role that needs it.
revoke all on function public.auth_role() from public, anon;
grant execute on function public.auth_role() to authenticated, service_role;

-- `claim_scan()` names public.scans in full, so a hostile search_path could not have redirected
-- it; pinning it silences the linter and makes that guarantee explicit rather than incidental.
create or replace function public.claim_scan()
returns setof public.scans
language sql
set search_path = public
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
