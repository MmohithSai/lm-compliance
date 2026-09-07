"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ImageKind, ScanSource } from "@/lib/database.types";
import { resizeImage } from "@/lib/image";
import { createClient } from "@/lib/supabase/client";

const KINDS: ImageKind[] = ["front", "back", "other"];

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [source, setSource] = useState<ScanSource>("package");
  const [hasCard, setHasCard] = useState(false);
  const [pdpW, setPdpW] = useState("");
  const [pdpH, setPdpH] = useState("");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (files.length === 0) return setStatus("Add at least one photo.");
    setBusy(true);
    try {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) throw new Error("Not signed in.");

      // id first: images land in scans/<scan_id>/ before the row exists, so the worker never
      // claims a scan whose photos are still uploading.
      const scanId = crypto.randomUUID();
      const images = [];
      for (const [i, file] of files.entries()) {
        setStatus(`Uploading photo ${i + 1} of ${files.length}…`);
        const { blob, width, height } = await resizeImage(file);
        const storage_path = `${scanId}/${i}.jpg`;
        const { error } = await supabase.storage
          .from("scans")
          .upload(storage_path, blob, { contentType: "image/jpeg" });
        if (error) throw error;
        images.push({ scan_id: scanId, storage_path, kind: KINDS[Math.min(i, 2)], width, height });
      }

      const { error: scanError } = await supabase.from("scans").insert({
        id: scanId,
        inspector_id: user.id,
        source,
        status: "queued",
        has_reference_card: hasCard,
        pdp_width_mm: pdpW ? Number(pdpW) : null,
        pdp_height_mm: pdpH ? Number(pdpH) : null,
        notes: notes || null,
      });
      if (scanError) throw scanError;
      const { error: imgError } = await supabase.from("scan_images").insert(images);
      if (imgError) throw imgError;

      router.push(`/scans/${scanId}`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  }

  return (
    <Card className="mx-auto max-w-lg">
      <CardHeader>
        <CardTitle>New scan</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-5">
          <div className="flex gap-2">
            {(["package", "ecommerce"] as const).map((s) => (
              <Button
                key={s}
                type="button"
                variant={source === s ? "default" : "outline"}
                onClick={() => setSource(s)}
              >
                {s === "package" ? "Package photo" : "E-commerce screenshot"}
              </Button>
            ))}
          </div>

          <div className="space-y-1">
            <Label htmlFor="photos">Photos (front, back, and one with the reference card)</Label>
            <Input
              id="photos"
              type="file"
              accept="image/*"
              capture="environment"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files ?? []).slice(0, 3))}
            />
            <p className="text-xs text-muted-foreground">Up to 3. Resized to 1600 px before upload.</p>
          </div>

          {source === "package" && (
            <>
              <div className="flex items-center gap-2">
                <Checkbox id="card" checked={hasCard} onCheckedChange={(v) => setHasCard(v === true)} />
                <Label htmlFor="card">A reference card (ArUco or credit-card size) is in the photo</Label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="pdpw">Panel width (mm, optional)</Label>
                  <Input
                    id="pdpw"
                    type="number"
                    inputMode="decimal"
                    min="0"
                    value={pdpW}
                    onChange={(e) => setPdpW(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="pdph">Panel height (mm, optional)</Label>
                  <Input
                    id="pdph"
                    type="number"
                    inputMode="decimal"
                    min="0"
                    value={pdpH}
                    onChange={(e) => setPdpH(e.target.value)}
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Without a card or panel size, font checks are reported as “not verifiable”. Nothing is estimated.
              </p>
            </>
          )}

          <div className="space-y-1">
            <Label htmlFor="notes">Notes (optional)</Label>
            <Input
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Shop, batch, anything useful"
            />
          </div>

          {status && <p className="text-sm">{status}</p>}
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Working…" : "Upload and check"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
