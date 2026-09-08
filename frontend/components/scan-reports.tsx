import { CircleAlert, FileJson, FileText, FileType2, LoaderCircle } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import type { ScanStatus } from "@/lib/db";

export type ReportFile = { format: "pdf" | "docx" | "json"; href: string };

const LOOK = {
  pdf: { label: "PDF", hint: "print or send", Icon: FileText },
  docx: { label: "Word", hint: "edit before filing", Icon: FileType2 },
  json: { label: "JSON", hint: "for another system", Icon: FileJson },
} as const;

/**
 * The three report files, or the reason there are none yet.
 *
 * The worker writes them to `scans/<scan id>/report.*` when the scan finishes, and the page
 * hands over short-lived signed URLs — the bucket is private, so a link cannot leak a scan to
 * someone who could not open the scan page in the first place.
 */
export function ScanReports({ status, files }: { status: ScanStatus; files: ReportFile[] }) {
  if (status === "queued" || status === "processing") {
    return (
      <Line icon={<LoaderCircle className="size-4 animate-spin" />}>
        The report is written when the checks finish.
      </Line>
    );
  }
  if (status === "failed") {
    return <Line icon={<CircleAlert className="size-4" />}>This scan failed, so there is no report.</Line>;
  }
  if (files.length === 0) {
    return (
      <Line icon={<CircleAlert className="size-4" />}>
        No report was written for this scan. Upload the photos again to get one.
      </Line>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {files.map(({ format, href }) => {
          const { label, hint, Icon } = LOOK[format];
          return (
            <a
              key={format}
              href={href}
              className={buttonVariants({ variant: "outline", size: "lg", className: "min-w-36 flex-1" })}
            >
              <Icon className="size-4" />
              {label}
              <span className="text-xs text-muted-foreground">{hint}</span>
            </a>
          );
        })}
      </div>
      {files.length < 3 && (
        <p className="text-xs text-muted-foreground">
          {(["pdf", "docx", "json"] as const)
            .filter((f) => !files.some((file) => file.format === f))
            .map((f) => LOOK[f].label)
            .join(" and ")}{" "}
          could not be written for this scan. The versions above hold the same findings.
        </p>
      )}
    </div>
  );
}

function Line({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <p className="flex items-center gap-2 text-sm text-muted-foreground">
      {icon}
      {children}
    </p>
  );
}
