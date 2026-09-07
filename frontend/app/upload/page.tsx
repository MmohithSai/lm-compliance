"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ImageKind, ScanSource } from "@/lib/db";
import { resizeImage } from "@/lib/image";
import { uuid } from "@/lib/uuid";
import { createClient } from "@/lib/supabase/client";

const KINDS: ImageKind[] = ["front", "back", "other"];
const SLOTS = ["Front panel", "Back panel", "With the reference card"];

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
  const camera = useRef<HTMLInputElement>(null);
  const gallery = useRef<HTMLInputElement>(null);
  const full = files.length >= 3;

  function pick(e: React.ChangeEvent<HTMLInputElement>) {
    setFiles((prev) => [...prev, ...Array.from(e.target.files ?? [])].slice(0, 3));
    e.target.value = ""; // so re-picking the same file still fires onChange
  }

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
      const scanId = uuid();
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
            <Label>Photos (front, back, and one with the reference card)</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="lg"
                className="flex-1"
                disabled={full}
                onClick={() => camera.current?.click()}
              >
                Take photo
              </Button>
              <Button
                type="button"
                variant="outline"
                size="lg"
                className="flex-1"
                disabled={full}
                onClick={() => gallery.current?.click()}
              >
                Choose files
              </Button>
            </div>
            {/* capture opens the camera but caps the pick at one file, so the gallery input is
                the only one that can take all three at once. Both append to the same list. */}
            <input ref={camera} type="file" accept="image/*" capture="environment" hidden onChange={pick} />
            <input ref={gallery} type="file" accept="image/*" multiple hidden onChange={pick} />
            <p className="text-xs text-muted-foreground">
              {files.length}/3 chosen. Resized to 1600 px before upload.
            </p>
            {files.length > 0 && (
              <ul className="space-y-1 pt-1">
                {files.map((f, i) => (
                  <li key={`${f.name}-${f.lastModified}-${i}`} className="flex items-center gap-2 text-sm">
                    <span className="w-40 shrink-0 text-muted-foreground">{SLOTS[i]}</span>
                    <span className="truncate">{f.name}</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="ml-auto"
                      onClick={() => setFiles((prev) => prev.filter((_, j) => j !== i))}
                    >
                      Remove
                    </Button>
                  </li>
                ))}
              </ul>
            )}
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
