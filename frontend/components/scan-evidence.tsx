"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import type { Severity } from "@/lib/db";

export type Word = { id: number; image_id: string | null; x: number; y: number; w: number; h: number };
export type Panel = { id: string; kind: string; url: string };
export type Declaration = { id: string; field: string; word_ids: number[] };
export type Violation = {
  id: string;
  rule_id: string;
  rule_ref: string;
  severity: Severity;
  message: string;
  word_ids: number[];
  status: string;
  reason: string | null;
};

const TONE: Record<Severity, "destructive" | "secondary" | "outline"> = {
  critical: "destructive",
  major: "destructive",
  minor: "secondary",
  info: "outline",
};

/**
 * The photos with a box round every declaration the pipeline read, and the violations beside
 * them. Picking a violation turns its evidence boxes red, which is the whole point: an inspector
 * has to be able to see on the pack what the report is talking about.
 *
 * Box coordinates are pixels in the uploaded image. preprocess.py deliberately does not resize
 * or rotate, so they still line up; they are turned into percentages of the image the browser
 * actually loaded, so they cannot drift out of step with it. scan_images.width / height are not
 * used for this: they are written by the uploader and a wrong pair there put every box in the
 * wrong place with nothing on the page to say so.
 */
export function ScanEvidence({
  panels,
  words,
  declarations,
  violations,
}: {
  panels: Panel[];
  words: Word[];
  declarations: Declaration[];
  violations: Violation[];
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [size, setSize] = useState<Record<string, { w: number; h: number }>>({});
  const active = violations.find((v) => v.id === selected) ?? null;
  const highlighted = new Set(active?.word_ids ?? []);

  const label = new Map<number, string>();
  for (const d of declarations) for (const id of d.word_ids) label.set(id, d.field);
  for (const id of highlighted) if (!label.has(id)) label.set(id, active?.rule_id ?? "");

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="space-y-4">
        {panels.map((panel) => {
          const natural = size[panel.id];
          const boxes = natural ? words.filter((w) => w.image_id === panel.id && label.has(w.id)) : [];
          return (
            <figure key={panel.id} className="space-y-1">
              <div className="relative overflow-hidden rounded border">
                {/* eslint-disable-next-line @next/next/no-img-element -- a signed Storage URL,
                    shown at its own aspect ratio so the boxes below land on the right words. */}
                <img
                  src={panel.url}
                  alt={`${panel.kind} panel`}
                  className="block w-full"
                  onLoad={(e) =>
                    setSize((prev) => ({
                      ...prev,
                      [panel.id]: {
                        w: e.currentTarget.naturalWidth,
                        h: e.currentTarget.naturalHeight,
                      },
                    }))
                  }
                />
                {boxes.map((w) => {
                  const on = highlighted.has(w.id);
                  return (
                    <span
                      key={w.id}
                      title={label.get(w.id)}
                      className={`absolute border-2 ${on ? "border-red-500 bg-red-500/20" : "border-sky-500/70"}`}
                      style={{
                        left: `${(w.x / natural.w) * 100}%`,
                        top: `${(w.y / natural.h) * 100}%`,
                        width: `${(w.w / natural.w) * 100}%`,
                        height: `${(w.h / natural.h) * 100}%`,
                      }}
                    />
                  );
                })}
              </div>
              <figcaption className="text-xs text-muted-foreground">{panel.kind}</figcaption>
            </figure>
          );
        })}
      </div>

      <div className="space-y-2">
        <h2 className="font-semibold">Violations</h2>
        {violations.length === 0 && <p className="text-sm text-muted-foreground">Nothing to report.</p>}
        {violations.map((v) => {
          const unverifiable = v.status === "unverifiable";
          return (
            <button
              key={v.id}
              type="button"
              onClick={() => setSelected(selected === v.id ? null : v.id)}
              className={`block w-full rounded border p-3 text-left ${selected === v.id ? "border-red-500" : ""}`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={TONE[v.severity]}>{v.severity}</Badge>
                <span className="font-mono text-xs">{v.rule_id}</span>
                <span className="text-xs text-muted-foreground">{v.rule_ref}</span>
                {unverifiable && <Badge variant="outline">not verifiable</Badge>}
              </div>
              <p className="mt-1 text-sm">{v.message}</p>
              {v.word_ids.length === 0 && !unverifiable && (
                <p className="mt-1 text-xs text-muted-foreground">
                  No box to show: the declaration is not on the photos.
                </p>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
