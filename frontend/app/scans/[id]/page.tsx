import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { ScanRealtime } from "@/components/scan-realtime";
import { createClient } from "@/lib/supabase/server";

const WAITING: Record<string, string> = {
  queued: "Waiting for the worker…",
  processing: "Checking the photos…",
};

// P3 adds the image with boxes, the declarations table and the violations list.
export default async function ScanPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: scan } = await supabase.from("scans").select("*").eq("id", id).single();
  if (!scan) notFound();

  return (
    <div className="space-y-3">
      <ScanRealtime id={id} live={scan.status === "queued" || scan.status === "processing"} />
      <h1 className="text-xl font-semibold">Scan</h1>
      <p>
        <Badge>{scan.status}</Badge> · {scan.source} · {new Date(scan.created_at).toLocaleString()}
      </p>
      {scan.compliance_score !== null && <p className="text-3xl font-bold">{scan.compliance_score} / 100</p>}
      {scan.error && <p className="text-sm text-red-600">{scan.error}</p>}
      {WAITING[scan.status] && <p className="text-sm text-muted-foreground">{WAITING[scan.status]}</p>}
      <p className="text-xs text-muted-foreground">
        Reference card: {scan.has_reference_card ? "yes" : "no"}. Scale: {scan.mm_per_px ?? "not verifiable"}.
      </p>
    </div>
  );
}
