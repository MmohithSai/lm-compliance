// Hand-written from supabase/migrations/0001_init.sql. Regenerate once the project is linked:
//   make db-types   (supabase gen types typescript --linked > frontend/lib/database.types.ts)
export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];

export type Role = "admin" | "inspector" | "viewer";
export type ScanSource = "package" | "ecommerce";
export type ScanStatus = "queued" | "processing" | "done" | "failed";
export type ImageKind = "front" | "back" | "other" | "evidence";
export type Severity = "critical" | "major" | "minor" | "info";

type Table<Row, Insert = Partial<Row>, Update = Partial<Row>> = {
  Row: Row;
  Insert: Insert;
  Update: Update;
  Relationships: [];
};

export type Database = {
  public: {
    Tables: {
      profiles: Table<{ id: string; full_name: string | null; role: Role; created_at: string }>;
      products: Table<{
        id: string;
        name: string;
        brand: string | null;
        manufacturer: string | null;
        category: string | null;
        barcode: string | null;
        created_by: string | null;
        created_at: string;
      }>;
      scans: Table<{
        id: string;
        product_id: string | null;
        inspector_id: string;
        source: ScanSource;
        status: ScanStatus;
        error: string | null;
        has_reference_card: boolean;
        pdp_width_mm: number | null;
        pdp_height_mm: number | null;
        mm_per_px: number | null;
        compliance_score: number | null;
        notes: string | null;
        location: string | null;
        created_at: string;
        finished_at: string | null;
      }>;
      scan_images: Table<{
        id: string;
        scan_id: string;
        storage_path: string;
        kind: ImageKind;
        width: number | null;
        height: number | null;
        created_at: string;
      }>;
      declarations: Table<{
        id: string;
        scan_id: string;
        field: string;
        value: string;
        confidence: number | null;
        word_ids: number[];
        image_id: string | null;
        height_mm: number | null;
        width_height_ratio: number | null;
        extractor: string;
      }>;
      violations: Table<{
        id: string;
        scan_id: string;
        rule_id: string;
        rule_ref: string;
        severity: Severity;
        message: string;
        evidence: Json;
        confidence: number | null;
      }>;
      reports: Table<{
        id: string;
        scan_id: string;
        pdf_path: string | null;
        docx_path: string | null;
        json_path: string | null;
        created_at: string;
      }>;
      evidence: Table<{
        id: string;
        scan_id: string;
        storage_path: string | null;
        note: string | null;
        created_by: string;
        created_at: string;
      }>;
    };
    Views: {
      dashboard_summary: {
        Row: {
          scans_this_week: number;
          scans_done: number;
          scans_failed: number;
          scans_compliant: number;
          avg_score: number | null;
        };
        Relationships: [];
      };
      top_violations: {
        Row: { rule_id: string; rule_ref: string; severity: Severity; count: number };
        Relationships: [];
      };
      violations_by_category: {
        Row: { category: string; severity: Severity; count: number };
        Relationships: [];
      };
    };
    Functions: Record<string, never>;
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
};
