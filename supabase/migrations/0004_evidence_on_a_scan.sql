-- P6. Evidence photographs attached to a scan after it finished.
--
-- The table, its RLS and the private `scans` bucket all exist since 0001 and are reused as they
-- stand: read for anyone signed in, insert for an inspector or an admin writing their own row,
-- update for the author or an admin, delete for an admin. Nothing here adds a second way to
-- authorise a file — evidence lives in the same bucket as the photographs and the reports, at
-- `<scan id>/evidence/<evidence id>.jpg`, and is read through the same signed URLs.
--
-- Two things were missing. The lookup the scan page makes (`where scan_id = …`) had no index,
-- which every other child of `scans` has. And a row with neither a photograph nor a note is not
-- evidence of anything, so the database says so rather than the form.

create index if not exists evidence_scan_idx on public.evidence (scan_id);

alter table public.evidence
  add constraint evidence_carries_something check (storage_path is not null or note is not null);
