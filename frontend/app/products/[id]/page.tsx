import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { createClient } from "@/lib/supabase/server";

/** Every scan filed under one pack, newest first. The point of the page is the column of
 *  scores: one number says whether this pack was compliant that day, a column says whether the
 *  maker fixed it. */
export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();

  const [{ data: product }, { data: scans }] = await Promise.all([
    supabase.from("products").select("name, brand, manufacturer, category").eq("id", id).single(),
    supabase
      .from("scan_search")
      .select("id, created_at, status, source, compliance_score, inspector_name, location")
      .eq("product_id", id)
      .order("created_at", { ascending: false })
      .limit(100),
  ]);
  if (!product) notFound();

  const scored = (scans ?? []).filter((s) => s.compliance_score !== null);
  const average = scored.length
    ? Math.round(scored.reduce((sum, s) => sum + (s.compliance_score ?? 0), 0) / scored.length)
    : null;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">{product.name}</h1>
        <p className="text-sm text-muted-foreground">
          {[product.brand, product.manufacturer, product.category].filter(Boolean).join(" · ") ||
            "No maker recorded."}
        </p>
      </div>

      <p className="text-sm">
        {scans?.length ?? 0} scan{scans?.length === 1 ? "" : "s"}
        {average !== null && ` · average score ${average}`}
      </p>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>When</TableHead>
            <TableHead>Inspector</TableHead>
            <TableHead>Where</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Score</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(scans ?? []).map((s) => (
            <TableRow key={s.id}>
              <TableCell>
                <Link href={`/scans/${s.id}`} className="underline">
                  {s.created_at ? new Date(s.created_at).toLocaleString() : "—"}
                </Link>
                <div className="text-xs text-muted-foreground">{s.source}</div>
              </TableCell>
              <TableCell>{s.inspector_name ?? "—"}</TableCell>
              <TableCell>{s.location ?? "—"}</TableCell>
              <TableCell>
                <Badge variant={s.status === "failed" ? "destructive" : "secondary"}>{s.status}</Badge>
              </TableCell>
              <TableCell>{s.compliance_score ?? "—"}</TableCell>
            </TableRow>
          ))}
          {(scans ?? []).length === 0 && (
            <TableRow>
              <TableCell colSpan={5}>No scans for this product.</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      <Link href="/scans" className="text-sm underline">
        Back to scans
      </Link>
    </div>
  );
}
