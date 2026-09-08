/**
 * Who is signed in, and what the page should therefore draw.
 *
 * The predicates mirror the RLS policies in supabase/migrations/0001_init.sql. They are here to
 * hide a button, never to be the guard: the guard is Postgres. A viewer who reaches /upload by
 * typing the URL is turned away by `app/upload/layout.tsx`, and a viewer who skips the frontend
 * entirely and posts at the REST API is refused by the `scans insert` policy. Both are checked
 * against the hosted project by `supabase/check_rls.py`.
 *
 * `canAddEvidence` and `canEditNotes` are the same idea for the scan page and already live in
 * `lib/evidence.ts`; they stay there, beside the code that uses them.
 */

import type { SupabaseClient } from "@supabase/supabase-js";
import type { User } from "@supabase/supabase-js";
import type { Database } from "./database.types";
import type { Role } from "./db";

/** RLS: `scans insert` and `scans bucket insert` — inspector or admin. A viewer, never. */
export function canUpload(role: Role | null): boolean {
  return role === "inspector" || role === "admin";
}

/** RLS: `audit_log read` and `model_calls read` — admin only. */
export function canSeeAudit(role: Role | null): boolean {
  return role === "admin";
}

/**
 * The signed-in user and their role, in one place. Three pages were each writing this query,
 * and a fourth was about to.
 */
export async function currentRole(
  supabase: SupabaseClient<Database>,
): Promise<{ user: User | null; role: Role | null }> {
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return { user: null, role: null };
  const { data } = await supabase.from("profiles").select("role").eq("id", user.id).single();
  return { user, role: (data?.role ?? null) as Role | null };
}
