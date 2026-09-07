"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { createClient } from "@/lib/supabase/client";

/**
 * Re-renders the scan page when the worker updates this scan.
 * Realtime is enabled on public.scans in 0001_init.sql. Nothing to do once the scan is finished.
 */
export function ScanRealtime({ id, live }: { id: string; live: boolean }) {
  const router = useRouter();
  useEffect(() => {
    if (!live) return;
    const supabase = createClient();
    const channel = supabase
      .channel(`scan:${id}`)
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "scans", filter: `id=eq.${id}` },
        () => router.refresh(),
      )
      .subscribe();
    return () => {
      void supabase.removeChannel(channel);
    };
  }, [id, live, router]);
  return null;
}
