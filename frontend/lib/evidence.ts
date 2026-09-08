/**
 * Evidence photographs and the inspector's note, as plain functions.
 *
 * Everything that decides something lives here rather than in the components, so it can be run
 * without a browser: which files are accepted, where a photograph is stored, what is written to
 * the database, what happens when an upload half-succeeds, and who is allowed to do any of it.
 * The components supply a real Supabase client and a real resizer; the tests supply fakes.
 *
 * The permission checks mirror the RLS policies in `supabase/migrations/0001_init.sql` word for
 * word. They are here to grey out a button, never to be the guard: the guard is Postgres, and a
 * viewer who calls the API directly is refused there.
 */

import type { Role } from "./db";

/** Types a phone or a laptop actually produces and `createImageBitmap` can decode. */
export const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
/** Before resizing. A 12 MP phone JPEG is about 5 MB; past this it is not a photograph of a pack. */
export const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;

/** Beside the pack photographs and the report, in the same private bucket. */
export function evidencePath(scanId: string, evidenceId: string): string {
  return `${scanId}/evidence/${evidenceId}.jpg`;
}

/** Why this file cannot be attached, or null if it can. Plain words: an inspector reads this. */
export function rejectReason(file: { type: string; size: number }): string | null {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return "Only JPEG, PNG or WebP photos can be attached.";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    const mb = (n: number) => (n / 1024 / 1024).toFixed(1);
    return `That photo is ${mb(file.size)} MB. The limit is ${mb(MAX_UPLOAD_BYTES)} MB.`;
  }
  return null;
}

type StorageError = { message: string } | null;

export type EvidenceDeps = {
  upload(path: string, blob: Blob, contentType: string): Promise<{ error: StorageError }>;
  remove(paths: string[]): Promise<unknown>;
  insert(row: EvidenceRow): Promise<{ error: StorageError }>;
  resize(file: File): Promise<{ blob: Blob }>;
  newId(): string;
};

export type EvidenceRow = {
  id: string;
  scan_id: string;
  storage_path: string;
  note: string | null;
  created_by: string;
};

/**
 * Resize, upload, then record. In that order, and the row is written last on purpose: a row
 * pointing at a file that is not there would show an inspector a broken photograph and call it
 * evidence. If the row cannot be written the uploaded file is deleted again, so a failed attach
 * leaves the scan exactly as it was.
 *
 * Nothing here touches the scan itself. Evidence is a separate table and a separate object in
 * Storage; the declarations, the violations and the score are not read and cannot be changed.
 */
export async function addEvidence(
  deps: EvidenceDeps,
  args: { scanId: string; userId: string; file: File; note?: string },
): Promise<EvidenceRow> {
  const reason = rejectReason(args.file);
  if (reason) throw new Error(reason);

  const id = deps.newId();
  const path = evidencePath(args.scanId, id);
  const { blob } = await deps.resize(args.file);

  const uploaded = await deps.upload(path, blob, "image/jpeg");
  if (uploaded.error) throw new Error(uploaded.error.message);

  const note = args.note?.trim() ? args.note.trim() : null;
  const row: EvidenceRow = { id, scan_id: args.scanId, storage_path: path, note, created_by: args.userId };
  const recorded = await deps.insert(row);
  if (recorded.error) {
    await deps.remove([path]); // no orphan in the bucket, and no half-attached evidence
    throw new Error(recorded.error.message);
  }
  return row;
}

/** The only patch the notes box ever sends. One key, so saving a note cannot touch a result. */
export function notesPatch(notes: string): { notes: string | null } {
  return { notes: notes.trim() === "" ? null : notes.trim() };
}

/** RLS: `evidence insert` — role inspector or admin, writing a row as themselves. */
export function canAddEvidence(role: Role | null): boolean {
  return role === "inspector" || role === "admin";
}

/** RLS: `scans update` — an admin, or the inspector whose scan it is. A viewer, never. */
export function canEditNotes(
  role: Role | null,
  scanInspectorId: string,
  userId: string | null,
): boolean {
  if (role === "admin") return true;
  return role === "inspector" && userId !== null && userId === scanInspectorId;
}
