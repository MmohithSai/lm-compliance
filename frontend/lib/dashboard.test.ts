import assert from "node:assert/strict";
import test from "node:test";
import {
  barWidth,
  categoryLabel,
  complianceRate,
  inWeek,
  weekEnd,
  weekLabel,
  weekStart,
} from "./dashboard.ts";

// Asia/Kolkata is UTC+5:30 all year, so Monday 00:00 local is the Sunday before at 18:30 UTC.
// 2026-09-07 is a Monday; 2026-09-06T18:30:00Z is the instant that week began.
const MONDAY = "2026-09-06T18:30:00.000Z";
const MONDAY_BEFORE = "2026-08-30T18:30:00.000Z";

test("the week starts at Monday 00:00 in the inspector's timezone, not UTC", () => {
  // Tuesday afternoon IST.
  assert.equal(weekStart(new Date("2026-09-08T10:00:00Z")).toISOString(), MONDAY);
  // The boundary is 18:30 UTC, which is what proves it was not cut at UTC midnight.
  assert.ok(MONDAY.endsWith("18:30:00.000Z"));
});

test("a scan at the exact start of the week is inside it", () => {
  const now = new Date("2026-09-08T10:00:00Z");
  assert.equal(weekStart(new Date(MONDAY)).toISOString(), MONDAY);
  assert.equal(inWeek(MONDAY, now), true);
});

test("one millisecond before the week starts belongs to the week before", () => {
  const justBefore = new Date(Date.parse(MONDAY) - 1);
  assert.equal(weekStart(justBefore).toISOString(), MONDAY_BEFORE);
  assert.equal(inWeek(justBefore, new Date("2026-09-08T10:00:00Z")), false);
});

test("late on Sunday night IST is still this week", () => {
  // 2026-09-13 23:59 IST = 18:29 UTC, the last minute before the next Monday.
  const sundayNight = new Date("2026-09-13T18:29:00Z");
  assert.equal(weekStart(sundayNight).toISOString(), MONDAY);
  assert.equal(inWeek(sundayNight, new Date("2026-09-08T10:00:00Z")), true);
});

test("the week ends where the next one starts, and that instant is not in it", () => {
  const now = new Date("2026-09-08T10:00:00Z");
  assert.equal(weekEnd(now).toISOString(), "2026-09-13T18:30:00.000Z");
  assert.equal(inWeek(weekEnd(now), now), false);
  assert.equal(inWeek(new Date(weekEnd(now).getTime() - 1), now), true);
});

test("the week is the same one from anywhere inside it", () => {
  const days = ["2026-09-07T00:00:00Z", "2026-09-09T23:00:00Z", "2026-09-13T18:00:00Z"];
  for (const d of days) assert.equal(weekStart(new Date(d)).toISOString(), MONDAY);
});

test("the label names the day the count started", () => {
  // "Sep" or "Sept" depending on the ICU data the runtime shipped with; the day is the point.
  assert.match(weekLabel(new Date("2026-09-08T10:00:00Z")), /^Mon 7 Sept?$/);
});

test("compliance rate is null on an empty dataset, never zero", () => {
  assert.equal(complianceRate(0, 0), null);
  assert.equal(complianceRate(0, 4), 0);
  assert.equal(complianceRate(1, 4), 25);
  assert.equal(complianceRate(4, 4), 100);
  // A failed scan is not "done", so it never reaches this function as a denominator.
  assert.equal(complianceRate(1, 3), 33);
});

test("a missing category is said, not invented", () => {
  assert.equal(categoryLabel(null), "Category not recorded");
  assert.equal(categoryLabel(""), "Category not recorded");
  assert.equal(categoryLabel("   "), "Category not recorded");
  assert.equal(categoryLabel("Biscuits"), "Biscuits");
});

test("bars are drawn against the largest value, and a zero draws nothing", () => {
  assert.equal(barWidth(5, 5), "100%");
  assert.equal(barWidth(1, 4), "25%");
  assert.equal(barWidth(0, 4), "0%");
  assert.equal(barWidth(3, 0), "0%");
  // A count of one against a hundred still has to be visible.
  assert.equal(barWidth(1, 100), "2%");
});
