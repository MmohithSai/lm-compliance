import {
  AlertTriangle,
  CircleAlert,
  ClipboardList,
  Info,
  ScrollText,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  barWidth,
  categoryLabel,
  complianceRate,
  scoreTone,
  weekLabel,
  weekStart,
} from "@/lib/dashboard";
import { canSeeAudit } from "@/lib/roles";
import { currentRole } from "@/lib/roles";
import { createClient } from "@/lib/supabase/server";

const RECENT = 8;
const TOP = 5;

/**
 * Everything on this page is read back from what the worker stored. No OCR runs here, no rule is
 * re-evaluated, and no score is recomputed — the number in a card is the number in the PDF.
 *
 * Six queries, all aggregated by Postgres: four views, one count, and the audit tail for an
 * admin. The views are `security_invoker`, so a role that cannot read a scan does not see it in
 * the totals either.
 */
export default async function DashboardPage() {
  const supabase = await createClient();
  const now = new Date();
  const since = weekStart(now);
  const { role } = await currentRole(supabase);

  const [summary, week, top, byCategory, recent, audit] = await Promise.all([
    supabase.from("dashboard_summary").select("*").single(),
    supabase
      .from("scans")
      .select("id", { count: "exact", head: true })
      .gte("created_at", since.toISOString()),
    supabase.from("top_violations").select("*").limit(TOP),
    supabase.from("scans_by_category").select("*"),
    supabase.from("dashboard_recent_scans").select("*").limit(RECENT),
    canSeeAudit(role)
      ? supabase
          .from("audit_log")
          .select("id, action, table_name, row_id, at, actor_id")
          .order("at", { ascending: false })
          .limit(6)
      : Promise.resolve({ data: null, error: null }),
  ]);

  const s = summary.data;
  const done = s?.scans_done ?? 0;
  const rate = complianceRate(s?.scans_compliant ?? 0, done);
  const error = summary.error ?? top.error ?? byCategory.error ?? recent.error;
  if (error) return <p className="text-red-600">{error.message}</p>;

  const categories = byCategory.data ?? [];
  const mostScans = Math.max(1, ...categories.map((c) => Number(c.scans ?? 0)));
  const topRules = top.data ?? [];
  const mostViolations = Math.max(1, ...topRules.map((v) => Number(v.count ?? 0)));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Legal Metrology (Packaged Commodities) Rules, 2011 — every figure below is read back
          from a finished scan. Nothing is estimated.
        </p>
      </div>

      {/* KPI cards. Two across on a phone, four on a laptop. */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi
          icon={<ClipboardList className="size-4" />}
          label="Scans this week"
          value={week.count ?? 0}
          note={`Since ${weekLabel(now)}, India time`}
        />
        <Kpi
          icon={<ShieldCheck className="size-4" />}
          label="Compliance rate"
          value={rate === null ? "—" : `${rate}%`}
          note={rate === null ? "No finished scans yet" : `${s?.scans_compliant} of ${done} scored 100`}
          tone={rate === null ? undefined : scoreTone(rate === 100 ? 100 : rate)}
        />
        <Kpi
          icon={<CircleAlert className="size-4" />}
          label="Average score"
          value={s?.avg_score ?? "—"}
          note={`${done} done · ${s?.scans_failed ?? 0} failed · ${s?.scans_pending ?? 0} waiting`}
        />
        <Kpi
          icon={<TriangleAlert className="size-4" />}
          label="Violations found"
          value={
            (s?.violations_critical ?? 0) + (s?.violations_major ?? 0) + (s?.violations_minor ?? 0)
          }
          note={`${s?.violations_critical ?? 0} critical · ${s?.violations_major ?? 0} major · ${
            s?.violations_minor ?? 0
          } minor`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Top violations. The rule's name comes from public.rules, which the worker mirrors
            from rules/pc_rules_2011.yaml — the frontend holds no copy of the law. */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Most common violations</CardTitle>
            <p className="text-xs text-muted-foreground">
              Across all scans. Notes and checks that could not be verified are not counted.
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            {topRules.length === 0 && <Empty>No violation has been recorded yet.</Empty>}
            {topRules.map((v) => (
              <div key={`${v.rule_id}-${v.severity}`} className="space-y-1">
                <div className="flex items-baseline gap-2 text-sm">
                  <span className="font-mono text-xs font-semibold">{v.rule_id}</span>
                  <span className="min-w-0 flex-1 truncate">{v.title ?? v.rule_ref}</span>
                  <span className="tabular-nums font-semibold">{v.count}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className={`h-full rounded-full ${SEVERITY_BAR[v.severity ?? "minor"] ?? "bg-slate-500"}`}
                    style={{ width: barWidth(Number(v.count ?? 0), mostViolations) }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  {v.rule_ref} · {v.severity} · on {v.scans} scan{v.scans === 1 ? "" : "s"}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* By category. `category` is null on every product the worker files today: nothing on a
            pack declares one. The row says so rather than inventing a bucket. */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">By category</CardTitle>
            <p className="text-xs text-muted-foreground">
              Scans and how many of them scored 100.
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            {categories.length === 0 && <Empty>No scans yet.</Empty>}
            {categories.map((c) => {
              const scored = Number(c.scored ?? 0);
              const pct = complianceRate(Number(c.compliant ?? 0), scored);
              return (
                <div key={c.category ?? "none"} className="space-y-1">
                  <div className="flex items-baseline gap-2 text-sm">
                    <span
                      className={`min-w-0 flex-1 truncate ${c.category ? "" : "italic text-muted-foreground"}`}
                    >
                      {categoryLabel(c.category)}
                    </span>
                    <span className="tabular-nums font-semibold">{c.scans}</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-slate-700"
                      style={{ width: barWidth(Number(c.scans ?? 0), mostScans) }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {pct === null
                      ? "Nothing finished yet"
                      : `${pct}% compliant · average ${c.avg_score ?? "—"}`}
                  </p>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      {/* Recent scans. A table on a laptop, one card per scan on a phone — a five column table
          at 375 px either scrolls sideways or squeezes the product name to nothing. */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Recent scans</CardTitle>
        </CardHeader>
        <CardContent>
          {recent.data?.length === 0 && <Empty>No scans yet.</Empty>}
          <ul className="divide-y">
            {(recent.data ?? []).map((r) => (
              <li key={r.id}>
                {/* Two lines, always. The pack's own name runs to a full postal address on some
                    of these — the maker is the name the OCR read — so it truncates rather than
                    wrapping four deep and pushing the score off the row. */}
                <Link href={`/scans/${r.id}`} className="flex items-center gap-3 py-2.5 hover:bg-slate-50">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {r.product_name ?? <span className="text-muted-foreground">Not identified</span>}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {[
                        r.created_at ? new Date(r.created_at).toLocaleDateString("en-IN") : null,
                        r.inspector_name,
                        r.source,
                        // Only when there is one. "Category not recorded" on every row is the
                        // same sentence four times; the panel above already says it once.
                        r.category,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  </div>
                  <Counts
                    critical={Number(r.critical ?? 0)}
                    major={Number(r.major ?? 0)}
                    minor={Number(r.minor ?? 0)}
                  />
                  <Badge variant={r.status === "failed" ? "destructive" : "secondary"}>
                    {r.status}
                  </Badge>
                  <span
                    className={`w-8 shrink-0 text-right text-sm font-semibold tabular-nums ${scoreTone(
                      r.compliance_score,
                    )}`}
                  >
                    {r.compliance_score ?? "—"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <Link href="/scans" className="mt-3 inline-block text-sm underline">
            All scans
          </Link>
        </CardContent>
      </Card>

      {/* Admin only, and the RLS policy says so too: `audit_log read` is `auth_role() = 'admin'`.
          A viewer or an inspector who forged this request gets an empty list from Postgres. */}
      {canSeeAudit(role) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <ScrollText className="size-4" /> Recent activity
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Written by database triggers, not by this page. An entry with no actor was written
              by the worker.
            </p>
          </CardHeader>
          <CardContent>
            {(audit.data ?? []).length === 0 && <Empty>Nothing recorded yet.</Empty>}
            <ul className="space-y-1 text-sm">
              {(audit.data ?? []).map((a) => (
                <li key={a.id} className="flex flex-wrap items-baseline gap-x-2">
                  <span className="font-mono text-xs">{a.action}</span>
                  <span className="font-medium">{a.table_name}</span>
                  <span className="font-mono text-xs text-muted-foreground">
                    {a.row_id?.slice(0, 8)}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {a.actor_id ? a.actor_id.slice(0, 8) : "worker"}
                  </span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {new Date(a.at).toLocaleString("en-IN")}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

const SEVERITY_BAR: Record<string, string> = {
  critical: "bg-red-600",
  major: "bg-amber-500",
  minor: "bg-slate-500",
};

function Kpi({
  icon,
  label,
  value,
  note,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  note: string;
  tone?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="flex items-center gap-1.5 text-xs font-normal text-muted-foreground">
          {icon}
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className={`text-2xl font-semibold tabular-nums ${tone ?? ""}`}>{value}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{note}</p>
      </CardContent>
    </Card>
  );
}

/** The severities that cost points, as three small numbers. Info never appears: it costs none. */
function Counts({ critical, major, minor }: { critical: number; major: number; minor: number }) {
  if (critical + major + minor === 0) {
    return <span className="text-xs text-emerald-700">clean</span>;
  }
  return (
    <span className="flex items-center gap-2 text-xs tabular-nums">
      {critical > 0 && (
        <span className="flex items-center gap-0.5 text-red-700">
          <AlertTriangle className="size-3" />
          {critical}
        </span>
      )}
      {major > 0 && (
        <span className="flex items-center gap-0.5 text-amber-700">
          <TriangleAlert className="size-3" />
          {major}
        </span>
      )}
      {minor > 0 && (
        <span className="flex items-center gap-0.5 text-slate-600">
          <Info className="size-3" />
          {minor}
        </span>
      )}
    </span>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="py-4 text-sm text-muted-foreground">{children}</p>;
}
