// The check-constraint unions from supabase/migrations/0001_init.sql. `supabase gen types`
// only sees `text` for these columns, and it overwrites database.types.ts on every
// `make db-types`, so they are written out here by hand. Keep in step with the migration.
export type Role = "admin" | "inspector" | "viewer";
export type ScanSource = "package" | "ecommerce";
export type ScanStatus = "queued" | "processing" | "done" | "failed";
export type ImageKind = "front" | "back" | "other" | "evidence";
export type Severity = "critical" | "major" | "minor" | "info";
