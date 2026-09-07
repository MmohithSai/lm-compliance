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

from pipeline import run_scan
from pipeline.models import ScanRow

log = logging.getLogger("worker")
POLL_SECONDS = float(os.environ.get("WORKER_POLL_SECONDS", "3"))


def connect() -> Client:
    url = os.environ.get("SUPABASE_URL") or os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    return create_client(url, os.environ["SUPABASE_SERVICE_ROLE_KEY"])


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
        finish(sb, scan.id, status="failed", error=f"{type(e).__name__}: {e}"[:500])
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sb = connect()
    log.info("worker up, polling every %ss", POLL_SECONDS)
    while True:
        if not process_one(sb):
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
