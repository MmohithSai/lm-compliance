import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { ScanEvidence, type Panel, type Violation } from "@/components/scan-evidence";
import { ScanRealtime } from "@/components/scan-realtime";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Severity } from "@/lib/db";
import { createClient } from "@/lib/supabase/server";

const WAITING: Record<string, string> = {
  queued: "Waiting for the worker…",
  processing: "Checking the photos…",
};

type Evidence = { word_ids?: number[]; status?: string; reason?: string | null };

export default async function ScanPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: scan } = await supabase.from("scans").select("*").eq("id", id).single();
  if (!scan) notFound();

  const [{ data: images }, { data: words }, { data: declarations }, { data: violations }] = await Promise.all([
    supabase.from("scan_images").select("id, kind, storage_path, width, height").eq("scan_id", id).order("kind"),
    supabase.from("ocr_words").select("id, image_id, x, y, w, h").eq("scan_id", id),
    supabase.from("declarations").select("id, field, value, confidence, word_ids, image_id").eq("scan_id", id),
    supabase.from("violations").select("id, rule_id, rule_ref, severity, message, evidence").eq("scan_id", id),
  ]);

  // The bucket is private, so every photo needs a short-lived signed URL.
  const paths = (images ?? []).map((i) => i.storage_path);
  const { data: signed } = paths.length
    ? await supabase.storage.from("scans").createSignedUrls(paths, 3600)
    : { data: [] };
  const url = new Map((signed ?? []).map((s) => [s.path, s.signedUrl]));
  const panels: Panel[] = (images ?? []).flatMap((i) =>
    url.get(i.storage_path)
      ? [{ id: i.id, kind: i.kind, url: url.get(i.storage_path)!, width: i.width, height: i.height }]
      : [],
  );

  const rows: Violation[] = (violations ?? []).map((v) => {
    const evidence = (v.evidence ?? {}) as Evidence;
    return {
      id: v.id,
      rule_id: v.rule_id,
      rule_ref: v.rule_ref,
      severity: v.severity as Severity,
      message: v.message,
      word_ids: evidence.word_ids ?? [],
      status: evidence.status ?? "fail",
      reason: evidence.reason ?? null,
    };
  });
  const scored = rows.filter((v) => v.status === "fail" && v.severity !== "info").length;

  return (
    <div className="space-y-4">
      <ScanRealtime id={id} live={scan.status === "queued" || scan.status === "processing"} />
      <h1 className="text-xl font-semibold">Scan</h1>
      <p>
        <Badge>{scan.status}</Badge> · {scan.source} · {new Date(scan.created_at).toLocaleString()}
      </p>
      {scan.compliance_score !== null && (
        <div>
          <p className="text-3xl font-bold">{scan.compliance_score} / 100</p>
          <p className="text-xs text-muted-foreground">
            {scored === 0 ? "No violation costs points." : `${scored} violation(s) cost points.`} 25 for each
            critical, 10 for each major, 3 for each minor. Notes and checks marked &ldquo;not verifiable&rdquo;
            cost nothing.
          </p>
        </div>
      )}
      {scan.error && <p className="text-sm text-red-600">{scan.error}</p>}
      {WAITING[scan.status] && <p className="text-sm text-muted-foreground">{WAITING[scan.status]}</p>}
      <p className="text-xs text-muted-foreground">
        Reference card: {scan.has_reference_card ? "yes" : "no"}. Scale: {scan.mm_per_px ?? "not verifiable"}.
      </p>

      <ScanEvidence
        panels={panels}
        words={words ?? []}
        declarations={(declarations ?? []).map((d) => ({ id: d.id, field: d.field, word_ids: d.word_ids }))}
        violations={rows}
      />

      <h2 className="font-semibold">Declarations read</h2>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Field</TableHead>
            <TableHead>Value</TableHead>
            <TableHead>Confidence</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(declarations ?? []).map((d) => (
            <TableRow key={d.id}>
              <TableCell className="font-mono text-xs">{d.field}</TableCell>
              <TableCell>{d.value}</TableCell>
              <TableCell>{d.confidence === null ? "—" : d.confidence.toFixed(2)}</TableCell>
            </TableRow>
          ))}
          {(declarations ?? []).length === 0 && (
            <TableRow>
              <TableCell colSpan={3}>Nothing read from the photos yet.</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {rows.some((v) => v.reason) && (
        <div className="space-y-1">
          <h2 className="font-semibold">What could not be checked</h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {rows
              .filter((v) => v.reason)
              .map((v) => (
                <li key={v.id}>
                  <span className="font-mono text-xs">{v.rule_id}</span> — {v.reason}
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  );
}
