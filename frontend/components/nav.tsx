import Link from "next/link";
import { SignOutButton } from "@/components/sign-out";
import { createClient } from "@/lib/supabase/server";

export async function Nav() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const role = user
    ? (await supabase.from("profiles").select("role").eq("id", user.id).single()).data?.role
    : null;

  return (
    <header className="border-b bg-white">
      <nav className="mx-auto flex max-w-4xl items-center gap-4 px-4 py-3 text-sm">
        <Link href="/upload" className="font-semibold">
          LM Check
        </Link>
        {user && (
          <>
            {role !== "viewer" && <Link href="/upload">Upload</Link>}
            <Link href="/scans">Scans</Link>
            <Link href="/dashboard">Dashboard</Link>
            <span className="ml-auto text-muted-foreground">
              {user.email} · {role ?? "…"}
            </span>
            <SignOutButton />
          </>
        )}
      </nav>
    </header>
  );
}
