import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Nav } from "@/components/nav";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: "LM Check",
  description: "Legal Metrology (Packaged Commodities) Rules, 2011 compliance checker",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = { themeColor: "#0f172a" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <Providers>
          <Nav />
          <main className="mx-auto max-w-4xl p-4">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
