/**
 * What the three roles are allowed to see on screen.
 *
 * This is a test of what gets drawn, not of who is actually let through. The real check is in
 * Postgres and is exercised by `supabase/check_rls.py` against the hosted project; if these two
 * ever disagree, Postgres is right and this file is the bug.
 */

import assert from "node:assert/strict";
import test from "node:test";
import type { Role } from "./db.ts";
import { canAddEvidence, canEditNotes } from "./evidence.ts";
import { canSeeAudit, canUpload } from "./roles.ts";

const ROLES: (Role | null)[] = ["admin", "inspector", "viewer", null];

test("a viewer cannot upload, and neither can a signed-out session", () => {
  assert.equal(canUpload("viewer"), false);
  assert.equal(canUpload(null), false);
});

test("an inspector and an admin can upload", () => {
  assert.equal(canUpload("inspector"), true);
  assert.equal(canUpload("admin"), true);
});

test("only an admin sees the audit log", () => {
  assert.deepEqual(
    ROLES.map(canSeeAudit),
    [true, false, false, false],
  );
});

test("adding P7 did not take anything away from the inspector", () => {
  const inspector = "insp-1";
  assert.equal(canUpload("inspector"), true);
  assert.equal(canAddEvidence("inspector"), true);
  assert.equal(canEditNotes("inspector", inspector, inspector), true);
  // Still not another inspector's scan, which is what the `scans update` policy says.
  assert.equal(canEditNotes("inspector", "someone-else", inspector), false);
});

test("a viewer can change nothing on a scan", () => {
  assert.equal(canUpload("viewer"), false);
  assert.equal(canAddEvidence("viewer"), false);
  assert.equal(canEditNotes("viewer", "insp-1", "viewer-1"), false);
  // Not even a scan whose inspector_id somehow matches their own id.
  assert.equal(canEditNotes("viewer", "viewer-1", "viewer-1"), false);
});

test("an admin may do all of it", () => {
  assert.equal(canUpload("admin"), true);
  assert.equal(canAddEvidence("admin"), true);
  assert.equal(canEditNotes("admin", "insp-1", "admin-1"), true);
  assert.equal(canSeeAudit("admin"), true);
});
