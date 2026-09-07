import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { createClient } from "@/lib/supabase/server";

// Placeholder. P7 adds top violations, by category, recent scans.
export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: summary } = await supabase.from("dashboard_summary").select("*").single();
  const stats = [
    ["Scans this week", summary?.scans_this_week],
    ["Done", summary?.scans_done],
    ["Compliant", summary?.scans_compliant],
    ["Failed", summary?.scans_failed],
    ["Average score", summary?.avg_score],
  ] as const;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {stats.map(([label, value]) => (
        <Card key={label}>
          <CardHeader className="pb-1">
            <CardTitle className="text-sm font-normal text-muted-foreground">{label}</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{value ?? "—"}</CardContent>
        </Card>
      ))}
    </div>
  );
}
