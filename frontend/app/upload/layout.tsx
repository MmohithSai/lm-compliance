import { redirect } from "next/navigation";
import { canUpload, currentRole } from "@/lib/roles";
import { createClient } from "@/lib/supabase/server";

/**
 * A viewer may not open the upload form, whether or not they can see the link to it.
 *
 * This runs on the server, so typing /upload into the address bar is turned away before the form
 * is ever sent. It is still not the guard: a viewer who skips the app and posts straight at the
 * REST API is refused by the `scans insert` and `scans bucket insert` policies in Postgres.
 * `supabase/check_rls.py` proves that against the hosted project.
 */
export default async function UploadLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { role } = await currentRole(supabase);
  if (!canUpload(role)) redirect("/scans");
  return <>{children}</>;
}
