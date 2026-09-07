import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Legal Metrology Compliance Checker",
    short_name: "LM Check",
    description: "Photograph a package, get a rule-by-rule compliance report.",
    start_url: "/upload",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#0f172a",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }],
  };
}
