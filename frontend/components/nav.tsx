import { Scale } from "lucide-react";
import Link from "next/link";
import { SignOutButton } from "@/components/sign-out";
import { canUpload, currentRole } from "@/lib/roles";
import { createClient } from "@/lib/supabase/server";

export async function Nav() {
  const supabase = await createClient();
  const { user, role } = await currentRole(supabase);

  return (
    <header className="border-b bg-white">
      <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 text-sm">
        <Link href="/dashboard" className="flex items-center gap-1.5 font-semibold">
          <Scale className="size-4" />
          LM Check
        </Link>
        {user && (
          <>
            <Link href="/dashboard">Dashboard</Link>
            <Link href="/scans">Scans</Link>
            {/* A viewer has no upload link, and no way in through the URL either:
                app/upload/layout.tsx turns them away, and Postgres refuses the insert. */}
            {canUpload(role) && <Link href="/upload">Upload</Link>}
            <span className="ml-auto flex items-center gap-2 text-muted-foreground">
              <span className="hidden sm:inline">{user.email}</span>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-700">
                {role ?? "…"}
              </span>
            </span>
            <SignOutButton />
          </>
        )}
      </nav>
    </header>
  );
}
