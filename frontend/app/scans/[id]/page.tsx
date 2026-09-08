import { CircleAlert } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { ScanEvidence, type Panel, type Violation } from "@/components/scan-evidence";
import { ScanEvidencePhotos, type EvidencePhoto } from "@/components/scan-evidence-photos";
import { ScanNotes } from "@/components/scan-notes";
import { ScanRealtime } from "@/components/scan-realtime";
import { ScanReports, type ReportFile } from "@/components/scan-reports";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ScanStatus, Severity } from "@/lib/db";
import { canAddEvidence, canEditNotes } from "@/lib/evidence";
import { currentRole } from "@/lib/roles";
import { createClient } from "@/lib/supabase/server";

const WAITING: Record<string, string> = {
  queued: "Waiting for the worker…",
  processing: "Checking the photos…",
};

type Evidence = { word_ids?: number[]; status?: string; reason?: string | null };

export default async function ScanPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: scan } = await supabase
    .from("scans")
    .select("*, products(id, name, manufacturer)")
    .eq("id", id)
    .single();
  if (!scan) notFound();

  const [
    { data: images },
    { data: words },
    { data: declarations },
    { data: violations },
    { data: report },
    { data: evidence },
  ] = await Promise.all([
      supabase.from("scan_images").select("id, kind, storage_path").eq("scan_id", id).order("kind"),
      supabase.from("ocr_words").select("id, image_id, x, y, w, h").eq("scan_id", id),
      supabase
        .from("declarations")
        .select("id, field, value, confidence, word_ids, image_id, height_mm, width_height_ratio")
        .eq("scan_id", id),
      supabase.from("violations").select("id, rule_id, rule_ref, severity, message, evidence").eq("scan_id", id),
      supabase.from("reports").select("pdf_path, docx_path, json_path").eq("scan_id", id).maybeSingle(),
      supabase
        .from("evidence")
        .select("id, storage_path, note, created_at, profiles(full_name)")
        .eq("scan_id", id)
        .order("created_at"),
    ]);

  // Who is looking, and therefore what they may change. Both checks mirror the RLS policies;
  // Postgres is what actually refuses a viewer, this only decides what to draw.
  const { user, role } = await currentRole(supabase);

  // One signed URL per report file. `download` puts a sensible filename on the saved file
  // instead of the bucket path, and the URL is only issued to a session that could read the
  // scan row above — the bucket itself is private.
  const wanted = [
    { format: "pdf", path: report?.pdf_path },
    { format: "docx", path: report?.docx_path },
    { format: "json", path: report?.json_path },
  ] as const;
  const files: ReportFile[] = (
    await Promise.all(
      wanted.map(async ({ format, path }) => {
        if (!path) return null;
        const { data } = await supabase.storage
          .from("scans")
          .createSignedUrl(path, 3600, { download: `lm-report-${id.slice(0, 8)}.${format}` });
        return data ? { format, href: data.signedUrl } : null;
      }),
    )
  ).filter((f) => f !== null);

  // The bucket is private, so every photo needs a short-lived signed URL. Evidence photographs
  // are signed in the same call and on the same terms as the pack photos: the session could read
  // the scan row above, so it may see the scan's files.
  const evidencePaths = (evidence ?? []).flatMap((e) => (e.storage_path ? [e.storage_path] : []));
  const paths = [...(images ?? []).map((i) => i.storage_path), ...evidencePaths];
  const { data: signed } = paths.length
    ? await supabase.storage.from("scans").createSignedUrls(paths, 3600)
    : { data: [] };
  const url = new Map((signed ?? []).map((s) => [s.path, s.signedUrl]));
  const evidencePhotos: EvidencePhoto[] = (evidence ?? []).map((e) => ({
    id: e.id,
    url: e.storage_path ? (url.get(e.storage_path) ?? null) : null,
    note: e.note,
    taken: new Date(e.created_at).toLocaleString(),
    author: e.profiles?.full_name ?? null,
  }));
  const panels: Panel[] = (images ?? []).flatMap((i) =>
    url.get(i.storage_path)
      ? [{ id: i.id, kind: i.kind, url: url.get(i.storage_path)! }]
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
      {/* Which pack this is, matched on the maker and the generic name the OCR read off it.
          Unmatched is the honest answer when the pack declared no maker — which is D1. A failed
          scan says nothing at all here: "not identified" would claim we looked, and nothing was
          ever read to look with. */}
      {scan.status !== "failed" && (
        <p className="text-sm">
          {scan.products ? (
            <>
              <Link href={`/products/${scan.products.id}`} className="underline">
                {scan.products.name}
              </Link>
              {scan.products.manufacturer && ` · ${scan.products.manufacturer}`}
            </>
          ) : (
            <span className="text-muted-foreground">
              Product not identified from this {scan.source === "ecommerce" ? "listing" : "pack"}.
            </span>
          )}
        </p>
      )}
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
      {/* A failed scan reached no verdict, and the page must not read like one. The heading
          says so, the worker's own sentence says why and what to do next, and neither the
          score block above nor the report block below can show anything: `compliance_score`
          was never written and no report file was rendered. */}
      {scan.status === "failed" && (
        <div className="space-y-1 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm">
          <p className="flex items-center gap-2 font-semibold text-destructive">
            <CircleAlert className="size-4 shrink-0" />
            This scan could not be assessed.
          </p>
          {scan.error && <p className="text-pretty">{scan.error}</p>}
          <p className="text-muted-foreground">
            No verdict was reached. This is not a pass and not a failure &mdash; the pack or listing was
            never checked against the Rules.
          </p>
        </div>
      )}
      {WAITING[scan.status] && <p className="text-sm text-muted-foreground">{WAITING[scan.status]}</p>}
      {/* On a listing there is no pack in the frame, so a scale would measure the screen. The
          print size and placement rules are not applied at all, which is not the same thing as
          being unverifiable — see `_applies` in the rule engine. */}
      <p className="text-xs text-muted-foreground">
        {scan.source === "ecommerce"
          ? "A screenshot is not the package, so only Rule 6(10) — what the listing must declare — is checked. Print size, contrast and placement are not judged from a listing."
          : `Reference card: ${scan.has_reference_card ? "yes" : "no"}. ${
              scan.mm_per_px
                ? `Scale: 1 pixel = ${Number(scan.mm_per_px).toFixed(3)} mm, so print size is measured.`
                : "No scale in the photo, so print size and contrast are not verifiable."
            }`}
      </p>

      <div className="space-y-2">
        <h2 className="font-semibold">Report</h2>
        <ScanReports status={scan.status as ScanStatus} files={files} />
      </div>

      <div className="space-y-2">
        <h2 className="font-semibold">Inspector&rsquo;s note</h2>
        <ScanNotes
          scanId={id}
          initial={scan.notes}
          canEdit={canEditNotes(role, scan.inspector_id, user?.id ?? null)}
        />
      </div>

      <ScanEvidencePhotos scanId={id} photos={evidencePhotos} canAdd={canAddEvidence(role)} />

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
            <TableHead>Print height</TableHead>
            <TableHead>Confidence</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(declarations ?? []).map((d) => (
            <TableRow key={d.id}>
              <TableCell className="font-mono text-xs">{d.field}</TableCell>
              <TableCell>{d.value}</TableCell>
              <TableCell className="whitespace-nowrap text-xs">
                {d.height_mm === null
                  ? "not measured"
                  : `${Number(d.height_mm).toFixed(1)} mm${
                      d.width_height_ratio === null ? "" : ` · w/h ${Number(d.width_height_ratio).toFixed(2)}`
                    }`}
              </TableCell>
              <TableCell>{d.confidence === null ? "—" : d.confidence.toFixed(2)}</TableCell>
            </TableRow>
          ))}
          {(declarations ?? []).length === 0 && (
            <TableRow>
              <TableCell colSpan={4}>
                {scan.status === "failed"
                  ? "Nothing could be read from these photos."
                  : "Nothing read from the photos yet."}
              </TableCell>
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
