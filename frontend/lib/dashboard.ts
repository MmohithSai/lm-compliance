/**
 * The arithmetic behind the dashboard, as plain functions so it can be run without a browser.
 *
 * Nothing here computes a compliance answer. The score, the violations and their severities are
 * read off what the worker stored; these functions only decide which rows fall inside a week,
 * how a ratio is turned into a percentage, and what to print when a value is missing.
 */

/**
 * The inspector's timezone, and the only place a week boundary is decided.
 *
 * The reports print UTC because a report timestamps one event. A dashboard buckets events into
 * a human week, and the human is in India: a week that turns over at 00:00 UTC puts every scan
 * taken between midnight and 05:30 on Monday morning into last week, which is a whole working
 * dawn on the wrong side of the line. So the week is Asia/Kolkata, it is computed here on the
 * server from an explicit zone, and it is never taken from whatever clock the browser is set to.
 */
export const WEEK_TZ = "Asia/Kolkata";

const PARTS = new Intl.DateTimeFormat("en-GB", {
  timeZone: WEEK_TZ,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
});

/** How far ahead of UTC the zone is at this instant, in milliseconds. */
function offsetMs(at: Date): number {
  const p = Object.fromEntries(PARTS.formatToParts(at).map((x) => [x.type, x.value]));
  const wall = Date.UTC(
    Number(p.year),
    Number(p.month) - 1,
    Number(p.day),
    Number(p.hour) % 24, // some ICU builds render midnight as "24"
    Number(p.minute),
    Number(p.second),
  );
  return wall - Math.floor(at.getTime() / 1000) * 1000;
}

/**
 * The instant Monday began, in `WEEK_TZ`. "Scans this week" is `created_at >= this`.
 *
 * India has no daylight saving, so the offset at `now` is also the offset at the boundary up to
 * seven days earlier. In a zone that does have it, the offset would have to be recomputed at the
 * boundary rather than reused.
 */
export function weekStart(now: Date): Date {
  const off = offsetMs(now);
  const local = new Date(now.getTime() + off); // the wall clock, dressed as UTC
  const sinceMonday = (local.getUTCDay() + 6) % 7; // Monday = 0, Sunday = 6
  local.setUTCDate(local.getUTCDate() - sinceMonday);
  local.setUTCHours(0, 0, 0, 0);
  return new Date(local.getTime() - off);
}

/** The instant the same week ends — next Monday. A scan at exactly this time is next week's. */
export function weekEnd(now: Date): Date {
  return new Date(weekStart(now).getTime() + 7 * 24 * 60 * 60 * 1000);
}

/** Is this scan inside the week containing `now`? */
export function inWeek(createdAt: string | Date, now: Date): boolean {
  const at = typeof createdAt === "string" ? new Date(createdAt) : createdAt;
  return at >= weekStart(now) && at < weekEnd(now);
}

/** "Mon 7 Sep" — the label under the week's count, in the same zone the count was cut on. */
export function weekLabel(now: Date): string {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: WEEK_TZ,
    weekday: "short",
    day: "numeric",
    month: "short",
  }).format(weekStart(now));
}

/**
 * Percentage of finished scans that were fully compliant, or null when nothing has finished.
 * Null, not zero: no scans is not the same as no compliant scans, and a dashboard that prints
 * "0% compliant" on an empty database is telling an inspector something untrue.
 */
export function complianceRate(compliant: number, done: number): number | null {
  if (done <= 0) return null;
  return Math.round((compliant / done) * 100);
}

/** A pack whose category was never recorded. Not invented, not called "other". */
export function categoryLabel(category: string | null | undefined): string {
  return category?.trim() ? category : "Category not recorded";
}

/** Bar width as a percentage of the largest value in the same chart. */
export function barWidth(value: number, largest: number): string {
  if (largest <= 0 || value <= 0) return "0%";
  return `${Math.max(2, Math.round((value / largest) * 100))}%`;
}

/** Green / amber / red for a score, matching the badge colours used on the scan page. */
export function scoreTone(score: number | null): string {
  if (score === null) return "text-muted-foreground";
  if (score === 100) return "text-emerald-700";
  if (score >= 70) return "text-amber-700";
  return "text-red-700";
}
