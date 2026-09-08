import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { createClient } from "@/lib/supabase/server";

type Search = { q?: string; from?: string; to?: string };

export default async function ScansPage({ searchParams }: { searchParams: Promise<Search> }) {
  const { q = "", from = "", to = "" } = await searchParams;
  const supabase = await createClient();

  // One flattened row per scan, `search` holding product, brand, maker, inspector, place, note
  // and the scan id. So "Parle" finds a pack by its maker and "Mumbai" finds it by where the
  // inspector was, without the page having to know which field the word came from.
  let query = supabase
    .from("scan_search")
    .select(
      "id, created_at, status, source, compliance_score, product_id, product_name, product_manufacturer, inspector_name",
    )
    .order("created_at", { ascending: false })
    .limit(50);
  if (q) query = query.ilike("search", `%${q}%`);
  // The day boundaries are UTC, so a scan taken late at night can land on the neighbouring day.
  // Fixing that properly means a date column in the view; it has not been worth one yet.
  if (from) query = query.gte("created_at", from);
  if (to) query = query.lt("created_at", `${to}T23:59:59.999Z`);
  const { data: scans, error } = await query;
  if (error) return <p className="text-red-600">{error.message}</p>;

  const filtered = Boolean(q || from || to);
  return (
    <>
      <h1 className="mb-4 text-xl font-semibold">Scans</h1>

      <form method="get" className="mb-4 flex flex-wrap items-end gap-3">
        <div className="min-w-56 flex-1">
          <Label htmlFor="q">Search</Label>
          <Input id="q" name="q" defaultValue={q} placeholder="Product, maker, inspector, place" />
        </div>
        <div>
          <Label htmlFor="from">From</Label>
          <Input id="from" name="from" type="date" defaultValue={from} />
        </div>
        <div>
          <Label htmlFor="to">To</Label>
          <Input id="to" name="to" type="date" defaultValue={to} />
        </div>
        <Button type="submit">Search</Button>
        {filtered && (
          <Link href="/scans" className="py-1.5 text-sm underline">
            Clear
          </Link>
        )}
      </form>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>When</TableHead>
            <TableHead>Product</TableHead>
            <TableHead>Inspector</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Score</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scans.map((s) => (
            <TableRow key={s.id}>
              <TableCell>
                <Link href={`/scans/${s.id}`} className="underline">
                  {s.created_at ? new Date(s.created_at).toLocaleString() : "—"}
                </Link>
                <div className="text-xs text-muted-foreground">{s.source}</div>
              </TableCell>
              <TableCell>
                {s.product_id ? (
                  <Link href={`/products/${s.product_id}`} className="underline">
                    {s.product_name}
                  </Link>
                ) : (
                  <span className="text-muted-foreground">Not identified</span>
                )}
                <div className="text-xs text-muted-foreground">{s.product_manufacturer}</div>
              </TableCell>
              <TableCell>{s.inspector_name ?? "—"}</TableCell>
              <TableCell>
                <Badge variant={s.status === "failed" ? "destructive" : "secondary"}>{s.status}</Badge>
              </TableCell>
              <TableCell>{s.compliance_score ?? "—"}</TableCell>
            </TableRow>
          ))}
          {scans.length === 0 && (
            <TableRow>
              <TableCell colSpan={5}>{filtered ? "No scans match that." : "No scans yet."}</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </>
  );
}
