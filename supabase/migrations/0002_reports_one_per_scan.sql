-- P5. One report row per scan, so a re-run replaces its report instead of stacking a second
-- one beside it and leaving the detail page to guess which is current. The worker upserts on
-- this constraint; the files themselves are overwritten in place at scans/<scan id>/report.*.

create unique index if not exists reports_scan_key on public.reports (scan_id);
