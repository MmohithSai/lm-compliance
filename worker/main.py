"""Worker loop: claim one queued scan every POLL seconds, run the pipeline, write status back.

Run: cd worker && uv run --env-file ../.env python main.py
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any, cast

from supabase import Client, create_client

from pipeline import UnreadableScan, run_scan
from pipeline.models import ScanRow
from pipeline.rules_engine import load_rules

log = logging.getLogger("worker")
POLL_SECONDS = float(os.environ.get("WORKER_POLL_SECONDS", "3"))


def connect() -> Client:
    url = os.environ.get("SUPABASE_URL") or os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    return create_client(url, os.environ["SUPABASE_SERVICE_ROLE_KEY"])


def sync_rules(sb: Client) -> int:
    """Mirror rules/pc_rules_2011.yaml into public.rules, so the dashboard can print a rule's
    name beside its code without a second copy of the law living in the frontend.

    The YAML is the law; this table is a projection of it, refreshed every time the worker
    starts. Upsert on the primary key, so editing a title in the YAML changes it here and a
    rule that was never added is added. Rules deleted from the YAML are left behind on purpose:
    violations already recorded under them still need their name.
    """
    rows = [
        {
            "rule_id": r.rule_id,
            "rule_ref": r.rule_ref,
            "title": r.title,
            "severity": r.severity.value,
            "synced_at": datetime.now(UTC).isoformat(),
        }
        for r in load_rules()
    ]
    sb.table("rules").upsert(rows).execute()
    return len(rows)


def claim(sb: Client) -> ScanRow | None:
    rows = cast(list[dict[str, Any]], sb.rpc("claim_scan").execute().data)
    return ScanRow.model_validate(rows[0]) if rows else None


def finish(sb: Client, scan_id: str, **fields: str | float | None) -> None:
    sb.table("scans").update({**fields, "finished_at": datetime.now(UTC).isoformat()}).eq(
        "id", scan_id
    ).execute()


def process_one(sb: Client) -> bool:
    scan = claim(sb)
    if scan is None:
        return False
    log.info("processing %s", scan.id)
    try:
        result = run_scan(sb, scan)
        finish(
            sb,
            scan.id,
            status="done",
            compliance_score=result.compliance_score,
            mm_per_px=result.mm_per_px,
        )
    except Exception as e:  # noqa: BLE001 - a failed scan must never kill the loop
        log.exception("scan %s failed", scan.id)
        # An unreadable photograph is an answer for the inspector, not a crash, so its message
        # is stored as the sentence they should read. Anything else keeps its class name, which
        # is for whoever reads the log.
        why = str(e) if isinstance(e, UnreadableScan) else f"{type(e).__name__}: {e}"
        finish(sb, scan.id, status="failed", error=why[:500])
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sb = connect()
    log.info("synced %d rules", sync_rules(sb))
    log.info("worker up, polling every %ss", POLL_SECONDS)
    while True:
        if not process_one(sb):
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
