"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { notesPatch } from "@/lib/evidence";
import { createClient } from "@/lib/supabase/client";

/**
 * The inspector's own note on the scan. It is a column on `scans`, so the report already prints
 * it ("Inspector's notes") without anything being added to P5.
 *
 * `canEdit` only decides whether the box is shown. The refusal itself is the `scans update`
 * policy: an admin, or the inspector whose scan it is. A viewer gets the note to read.
 */
export function ScanNotes({
  scanId,
  initial,
  canEdit,
}: {
  scanId: string;
  initial: string | null;
  canEdit: boolean;
}) {
  const router = useRouter();
  const [value, setValue] = useState(initial ?? "");
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    setStatus(null);
    const supabase = createClient();
    const { error } = await supabase.from("scans").update(notesPatch(value)).eq("id", scanId);
    setBusy(false);
    setStatus(error ? error.message : "Saved.");
    if (!error) router.refresh(); // so the report and anything else server-rendered agree
  }

  if (!canEdit) {
    return value.trim() ? (
      <p className="text-sm whitespace-pre-wrap">{value}</p>
    ) : (
      <p className="text-sm text-muted-foreground">No note on this scan.</p>
    );
  }

  return (
    <div className="space-y-2">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={3}
        placeholder="Where the pack was found, what the photos do not show, anything the report should carry."
        className="w-full rounded-lg border border-input bg-transparent px-2.5 py-1.5 text-base outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm"
      />
      <div className="flex items-center gap-3">
        <Button type="button" onClick={save} disabled={busy}>
          {busy ? "Saving…" : "Save note"}
        </Button>
        {status && <span className="text-sm text-muted-foreground">{status}</span>}
      </div>
    </div>
  );
}
