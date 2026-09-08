"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ACCEPTED_TYPES, addEvidence, type EvidenceRow } from "@/lib/evidence";
import { resizeImage } from "@/lib/image";
import { createClient } from "@/lib/supabase/client";
import { uuid } from "@/lib/uuid";

export type EvidencePhoto = {
  id: string;
  url: string | null;
  note: string | null;
  /** Already formatted. A client component that calls toLocaleString() renders one thing on the
   *  server and another in the browser, and React fails hydration over the difference. */
  taken: string;
  author: string | null;
};

/**
 * Photographs an inspector attaches to a scan after it has finished — the shelf, the seal, a
 * second pack from the same batch. They live in the same private bucket as the pack photos and
 * the report, at `<scan id>/evidence/<id>.jpg`, and are read through the same signed URLs.
 *
 * They are not `scan_images`: the worker downloads every `scan_images` row and re-reads it, so
 * putting evidence there would change the score of a scan that has already been reported on.
 * Nothing on this page can do that.
 */
export function ScanEvidencePhotos({
  scanId,
  photos,
  canAdd,
}: {
  scanId: string;
  photos: EvidencePhoto[];
  canAdd: boolean;
}) {
  const router = useRouter();
  const picker = useRef<HTMLInputElement>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function attach(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    e.target.value = ""; // so picking the same file twice still fires onChange
    if (files.length === 0) return;

    setError(null);
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) return setError("Not signed in.");

    const deps = {
      newId: uuid,
      resize: resizeImage,
      upload: async (path: string, blob: Blob, contentType: string) =>
        await supabase.storage.from("scans").upload(path, blob, { contentType }),
      insert: async (row: EvidenceRow) => await supabase.from("evidence").insert(row),
      remove: async (paths: string[]) => await supabase.storage.from("scans").remove(paths),
    };

    try {
      for (const [i, file] of files.entries()) {
        setBusy(`Attaching photo ${i + 1} of ${files.length}…`);
        await addEvidence(deps, { scanId, userId: user.id, file, note });
      }
      setNote("");
      router.refresh();
    } catch (err) {
      // addEvidence has already taken any half-uploaded file back out of the bucket.
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-3">
      <h2 className="font-semibold">Evidence photos</h2>

      {photos.length > 0 && (
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {photos.map((p) => (
            <li key={p.id} className="space-y-1">
              {p.url ? (
                <a href={p.url} target="_blank" rel="noreferrer">
                  {/* eslint-disable-next-line @next/next/no-img-element -- a signed URL is not a static asset */}
                  <img
                    src={p.url}
                    alt={p.note ?? "Evidence photo"}
                    className="w-full rounded-lg border object-cover"
                  />
                </a>
              ) : (
                <div className="rounded-lg border p-4 text-xs text-muted-foreground">
                  This photo could not be opened.
                </div>
              )}
              {p.note && <p className="text-xs">{p.note}</p>}
              <p className="text-xs text-muted-foreground">
                {p.author ?? "Unknown"} · {p.taken}
              </p>
            </li>
          ))}
        </ul>
      )}
      {photos.length === 0 && <p className="text-sm text-muted-foreground">No evidence photos yet.</p>}

      {canAdd && (
        <div className="space-y-2">
          <input
            ref={picker}
            type="file"
            accept={ACCEPTED_TYPES.join(",")}
            multiple
            className="hidden"
            onChange={attach}
          />
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="What this photo shows (optional)"
            className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-base outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm"
          />
          <Button type="button" variant="outline" onClick={() => picker.current?.click()} disabled={busy !== null}>
            {busy ?? "Add evidence photo"}
          </Button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      )}
    </div>
  );
}
