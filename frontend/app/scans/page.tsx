import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { createClient } from "@/lib/supabase/server";

export default async function ScansPage() {
  const supabase = await createClient();
  const { data: scans, error } = await supabase
    .from("scans")
    .select("id, status, source, compliance_score, created_at")
    .order("created_at", { ascending: false })
    .limit(50);
  if (error) return <p className="text-red-600">{error.message}</p>;

  return (
    <>
      <h1 className="mb-4 text-xl font-semibold">Scans</h1>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>When</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Score</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scans.map((s) => (
            <TableRow key={s.id}>
              <TableCell>
                <Link href={`/scans/${s.id}`} className="underline">
                  {new Date(s.created_at).toLocaleString()}
                </Link>
              </TableCell>
              <TableCell>{s.source}</TableCell>
              <TableCell>
                <Badge variant={s.status === "failed" ? "destructive" : "secondary"}>{s.status}</Badge>
              </TableCell>
              <TableCell>{s.compliance_score ?? "—"}</TableCell>
            </TableRow>
          ))}
          {scans.length === 0 && (
            <TableRow>
              <TableCell colSpan={4}>No scans yet.</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </>
  );
}
