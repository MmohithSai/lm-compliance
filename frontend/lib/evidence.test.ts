/**
 * Evidence and notes, without a browser or a database.
 *
 * Run: pnpm test  (node's own test runner, no test framework in the dependency list)
 *
 * What Postgres enforces — the RLS policies themselves — is not testable from here and is not
 * pretended to be. `canAddEvidence` / `canEditNotes` are checked against the wording of the
 * policies they mirror, and the policies themselves are exercised against the hosted project
 * with a real viewer session; see docs/PROGRESS.md.
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import {
  addEvidence,
  canAddEvidence,
  canEditNotes,
  evidencePath,
  notesPatch,
  rejectReason,
  type EvidenceDeps,
  type EvidenceRow,
} from "./evidence.ts";

const SCAN = "3f5b8e1e-e373-4191-b108-77470d565852";
const USER = "11111111-2222-3333-4444-555555555555";

function jpeg(name = "seal.jpg", size = 1024): File {
  return new File([new Uint8Array(size)], name, { type: "image/jpeg" });
}

/** A fake client that records what it was asked to do. `fail` makes one step return an error. */
function deps(fail?: "upload" | "insert") {
  const calls = {
    uploaded: [] as { path: string; contentType: string }[],
    inserted: [] as EvidenceRow[],
    removed: [] as string[][],
    resized: 0,
  };
  let n = 0;
  const impl: EvidenceDeps = {
    newId: () => `ev-${++n}`,
    resize: async () => {
      calls.resized += 1;
      return { blob: new Blob([new Uint8Array(64)], { type: "image/jpeg" }) };
    },
    upload: async (path, _blob, contentType) => {
      if (fail === "upload") return { error: { message: "network is down" } };
      calls.uploaded.push({ path, contentType });
      return { error: null };
    },
    insert: async (row) => {
      if (fail === "insert") return { error: { message: "new row violates row-level security" } };
      calls.inserted.push(row);
      return { error: null };
    },
    remove: async (paths) => {
      calls.removed.push(paths);
    },
  };
  return { impl, calls };
}

// ---------------------------------------------------------------- what is written down

test("attaching a photo records the scan it belongs to, where it is, and who added it", async () => {
  const { impl, calls } = deps();
  const row = await addEvidence(impl, { scanId: SCAN, userId: USER, file: jpeg(), note: " the seal " });

  assert.deepEqual(calls.inserted, [
    {
      id: "ev-1",
      scan_id: SCAN,
      storage_path: `${SCAN}/evidence/ev-1.jpg`,
      note: "the seal",
      created_by: USER,
    },
  ]);
  assert.equal(row.storage_path, calls.inserted[0].storage_path);
  assert.deepEqual(calls.uploaded, [{ path: `${SCAN}/evidence/ev-1.jpg`, contentType: "image/jpeg" }]);
});

test("a photo with no caption is still evidence", async () => {
  const { impl, calls } = deps();
  await addEvidence(impl, { scanId: SCAN, userId: USER, file: jpeg(), note: "   " });
  assert.equal(calls.inserted[0].note, null);
});

test("evidence is stored under its scan, beside the pack photos and the report", () => {
  assert.equal(evidencePath(SCAN, "ev-1"), `${SCAN}/evidence/ev-1.jpg`);
  // Pack photos are <scan>/0.jpg and the report is <scan>/report.pdf, so nothing can collide.
  assert.notEqual(evidencePath(SCAN, "ev-1"), `${SCAN}/0.jpg`);
});

test("several photos on one scan each get their own object", async () => {
  const { impl, calls } = deps();
  for (const name of ["seal.jpg", "batch.jpg", "shelf.jpg"]) {
    await addEvidence(impl, { scanId: SCAN, userId: USER, file: jpeg(name) });
  }
  assert.deepEqual(
    calls.inserted.map((r) => r.storage_path),
    [`${SCAN}/evidence/ev-1.jpg`, `${SCAN}/evidence/ev-2.jpg`, `${SCAN}/evidence/ev-3.jpg`],
  );
  assert.equal(new Set(calls.inserted.map((r) => r.storage_path)).size, 3);
});

// ---------------------------------------------------------------- what is refused

test("a file that is not a photograph is refused before anything is uploaded", async () => {
  const { impl, calls } = deps();
  const pdf = new File([new Uint8Array(16)], "report.pdf", { type: "application/pdf" });
  await assert.rejects(
    () => addEvidence(impl, { scanId: SCAN, userId: USER, file: pdf }),
    /Only JPEG, PNG or WebP/,
  );
  assert.deepEqual(calls.uploaded, []);
  assert.deepEqual(calls.inserted, []);
  assert.equal(calls.resized, 0);
});

test("a photograph too big to be one is refused with its size in the message", () => {
  assert.equal(rejectReason({ type: "image/jpeg", size: 4 * 1024 * 1024 }), null);
  assert.match(rejectReason({ type: "image/jpeg", size: 20 * 1024 * 1024 }) ?? "", /20\.0 MB.*15\.0 MB/);
  assert.equal(rejectReason({ type: "image/png", size: 10 }), null);
  assert.equal(rejectReason({ type: "image/webp", size: 10 }), null);
  assert.match(rejectReason({ type: "", size: 10 }) ?? "", /Only JPEG/);
});

// ---------------------------------------------------------------- what happens when it breaks

test("an upload that fails writes no row", async () => {
  const { impl, calls } = deps("upload");
  await assert.rejects(() => addEvidence(impl, { scanId: SCAN, userId: USER, file: jpeg() }), /network is down/);
  assert.deepEqual(calls.inserted, []);
});

test("a row that cannot be written takes its uploaded file back out of the bucket", async () => {
  const { impl, calls } = deps("insert");
  await assert.rejects(
    () => addEvidence(impl, { scanId: SCAN, userId: USER, file: jpeg() }),
    /row-level security/,
  );
  assert.deepEqual(calls.removed, [[`${SCAN}/evidence/ev-1.jpg`]]);
});

// ---------------------------------------------------------------- the note

test("saving a note sends the note and nothing else", () => {
  // The scan row carries the score, the scale and the status. A note must not be able to reach
  // any of them, so the patch is built here and has exactly one key.
  assert.deepEqual(Object.keys(notesPatch("Shelf 3, cold aisle")), ["notes"]);
  assert.deepEqual(notesPatch("Shelf 3, cold aisle"), { notes: "Shelf 3, cold aisle" });
});

test("clearing the note stores nothing rather than an empty string", () => {
  assert.deepEqual(notesPatch("   "), { notes: null });
  assert.deepEqual(notesPatch(" trimmed "), { notes: "trimmed" });
});

// ---------------------------------------------------------------- who may do it

test("a viewer can attach nothing and edit nothing", () => {
  assert.equal(canAddEvidence("viewer"), false);
  assert.equal(canEditNotes("viewer", USER, USER), false);
  assert.equal(canAddEvidence(null), false);
  assert.equal(canEditNotes(null, USER, USER), false);
});

test("an inspector attaches evidence, and notes only on their own scan", () => {
  assert.equal(canAddEvidence("inspector"), true);
  assert.equal(canEditNotes("inspector", USER, USER), true);
  assert.equal(canEditNotes("inspector", "someone-else", USER), false);
  assert.equal(canEditNotes("inspector", USER, null), false);
});

test("an admin may do both on anyone's scan", () => {
  assert.equal(canAddEvidence("admin"), true);
  assert.equal(canEditNotes("admin", "someone-else", USER), true);
});
