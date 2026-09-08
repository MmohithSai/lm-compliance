"""Prove the roles against the hosted project, with three real signed-in sessions.

The frontend hides an upload button from a viewer. That is not a security boundary and this
script exists because of it: every check below goes straight at PostgREST and Storage with the
anon key and a real JWT, exactly as a person with the browser's dev tools would.

    cd worker && uv run --env-file ../.env python ../supabase/check_rls.py

Reads NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY. The service-role key is used
only to read a row back and to tidy up, because a service-role client bypasses RLS and so can
prove nothing about it.

Everything is tried against rows this script makes, never against the project's own scans, and
they are deleted at the end. The first version did work on the oldest real scan and overwrote
its note; the audit log is what caught it, which is the whole argument for having one.
"""

from __future__ import annotations

import os
import sys
import uuid
from collections.abc import Callable
from typing import Any

from supabase import Client, create_client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed_users import USERS  # noqa: E402 - same folder, and the passwords live in one place

PASSWORD = {role: password for _, password, role, _ in USERS}
EMAIL = {role: email for email, _, role, _ in USERS}

failures: list[str] = []


def check(role: str, what: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    if not ok:
        failures.append(f"{role} {what}")
    print(f"  [{mark}] {role:9} {what}{f'  - {detail}' if detail else ''}")


def refused(fn: Callable[[], Any]) -> tuple[bool, str]:
    """True when Postgres or Storage said no.

    An insert raises. An update or a delete that RLS filters out does not raise: it matches no
    rows and returns an empty list, which is the same refusal wearing different clothes.
    """
    try:
        res = fn()
    except Exception as e:  # noqa: BLE001 - any refusal counts, and the message is printed
        return True, f"{type(e).__name__}: {str(e)[:70]}"
    rows = getattr(res, "data", None)
    if isinstance(rows, list) and len(rows) == 0:
        return True, "0 rows affected"
    return False, f"allowed: {str(rows)[:70]}"


def sign_in(url: str, anon: str, role: str) -> tuple[Client, str]:
    sb = create_client(url, anon)
    session = sb.auth.sign_in_with_password({"email": EMAIL[role], "password": PASSWORD[role]})
    assert session.user is not None
    return sb, session.user.id


def main() -> int:  # noqa: PLR0915 - a checklist reads better as one list
    url = os.environ.get("SUPABASE_URL") or os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    anon = os.environ["NEXT_PUBLIC_SUPABASE_ANON_KEY"]
    service = create_client(url, os.environ["SUPABASE_SERVICE_ROLE_KEY"])

    viewer, viewer_id = sign_in(url, anon, "viewer")
    inspector, inspector_id = sign_in(url, anon, "inspector")
    admin, admin_id = sign_in(url, anon, "admin")

    scan_id = str(uuid.uuid4())
    admin_scan_id = str(uuid.uuid4())
    evidence_id = str(uuid.uuid4())

    # ------------------------------------------------------------------ 1. the inspector works
    print("\n1. Inspector - everything P1 and P6 gave them still works")
    ok, detail = refused(
        lambda: (
            inspector.table("scans")
            .insert(
                {
                    "id": scan_id,
                    "inspector_id": inspector_id,
                    "source": "package",
                    # 'done', not 'queued': a queued row would be claimed by a running worker, and
                    # this scan has no photographs behind it.
                    "status": "done",
                    "compliance_score": 100,
                    "location": "RLS check",
                }
            )
            .execute()
        )
    )
    check("inspector", "insert a scan", not ok, detail)
    made_scan = not ok
    if not made_scan:
        print("\nThe inspector could not create the scan the rest of the checks need.")
        return 1

    ok, detail = refused(
        lambda: inspector.storage.from_("scans").upload(
            f"{scan_id}/rls-check.txt", b"rls check", {"content-type": "text/plain"}
        )
    )
    check("inspector", "upload to the scans bucket", not ok, detail)

    ok, detail = refused(
        lambda: (
            inspector.table("evidence")
            .insert(
                {
                    "id": evidence_id,
                    "scan_id": scan_id,
                    "note": "rls check",
                    "created_by": inspector_id,
                }
            )
            .execute()
        )
    )
    check("inspector", "add evidence (P6)", not ok, detail)

    ok, detail = refused(
        lambda: (
            inspector.table("scans").update({"notes": "inspector note"}).eq("id", scan_id).execute()
        )
    )
    check("inspector", "edit the note on their own scan (P6)", not ok, detail)

    # A scan belonging to somebody else, made for the purpose so no real row is at risk.
    admin.table("scans").insert(
        {
            "id": admin_scan_id,
            "inspector_id": admin_id,
            "source": "package",
            "status": "done",
            "compliance_score": 100,
            "location": "RLS check (admin's)",
        }
    ).execute()
    ok, detail = refused(
        lambda: (
            inspector.table("scans").update({"notes": "not mine"}).eq("id", admin_scan_id).execute()
        )
    )
    check("inspector", "cannot edit somebody else's scan", ok, detail)

    ok, detail = refused(
        lambda: inspector.table("scans").delete().eq("id", admin_scan_id).execute()
    )
    check("inspector", "cannot delete a scan at all", ok, detail)

    rows = inspector.table("audit_log").select("id").limit(1).execute().data
    check("inspector", "cannot read the audit log", len(rows) == 0, f"{len(rows)} rows")

    # ------------------------------------------------------------------ 2. the viewer is refused
    print("\n2. Viewer - every write, straight at the API, no browser involved")
    target = service.table("scans").select("*").eq("id", scan_id).single().execute().data
    target_id = scan_id

    ok, detail = refused(
        lambda: (
            viewer.table("scans")
            .insert({"inspector_id": viewer_id, "source": "package", "status": "queued"})
            .execute()
        )
    )
    check("viewer", "insert a scan", ok, detail)

    ok, detail = refused(
        lambda: (
            viewer.table("scans")
            .insert({"inspector_id": inspector_id, "source": "package", "status": "queued"})
            .execute()
        )
    )
    check("viewer", "insert a scan as somebody else", ok, detail)

    ok, detail = refused(
        lambda: viewer.storage.from_("scans").upload(
            f"{target_id}/viewer.txt", b"nope", {"content-type": "text/plain"}
        )
    )
    check("viewer", "upload to the scans bucket", ok, detail)

    ok, detail = refused(
        lambda: (
            viewer.table("scan_images")
            .insert({"scan_id": target_id, "storage_path": f"{target_id}/9.jpg", "kind": "front"})
            .execute()
        )
    )
    check("viewer", "attach an image to a scan", ok, detail)

    ok, detail = refused(
        lambda: (
            viewer.table("evidence")
            .insert({"scan_id": target_id, "note": "viewer", "created_by": viewer_id})
            .execute()
        )
    )
    check("viewer", "add evidence", ok, detail)

    ok, detail = refused(
        lambda: (
            viewer.table("scans").update({"notes": "viewer was here"}).eq("id", target_id).execute()
        )
    )
    check("viewer", "edit the note on a scan", ok, detail)

    ok, detail = refused(
        lambda: viewer.table("scans").update({"compliance_score": 0}).eq("id", target_id).execute()
    )
    check("viewer", "change a compliance score", ok, detail)

    ok, detail = refused(lambda: viewer.table("scans").delete().eq("id", target_id).execute())
    check("viewer", "delete a scan", ok, detail)

    ok, detail = refused(
        lambda: (
            viewer.table("products").insert({"name": "viewer", "created_by": viewer_id}).execute()
        )
    )
    check("viewer", "insert a product", ok, detail)

    ok, detail = refused(
        lambda: viewer.table("products").update({"name": "renamed"}).neq("name", "").execute()
    )
    check("viewer", "rename a product", ok, detail)

    ok, detail = refused(
        lambda: viewer.table("profiles").update({"role": "admin"}).eq("id", viewer_id).execute()
    )
    check("viewer", "promote themselves to admin", ok, detail)

    ok, detail = refused(
        lambda: (
            viewer.table("evidence").update({"note": "edited"}).eq("scan_id", target_id).execute()
        )
    )
    check("viewer", "edit somebody else's evidence", ok, detail)

    ok, detail = refused(lambda: viewer.table("evidence").delete().eq("id", evidence_id).execute())
    check("viewer", "delete somebody else's evidence", ok, detail)

    rows = viewer.table("audit_log").select("id").limit(1).execute().data
    check("viewer", "cannot read the audit log", len(rows) == 0, f"{len(rows)} rows")

    # What a viewer *is* for.
    seen = viewer.table("scan_search").select("id").limit(50).execute().data
    check("viewer", "can still read scans", len(seen) > 0, f"{len(seen)} scans")
    summary = viewer.table("dashboard_summary").select("*").single().execute().data
    check("viewer", "can still read the dashboard", summary is not None)

    after = service.table("scans").select("*").eq("id", target_id).single().execute().data
    unchanged = all(
        after[k] == target[k] for k in ("notes", "compliance_score", "status", "inspector_id")
    )
    check(
        "viewer", "left the scan exactly as it was", unchanged, f"score {after['compliance_score']}"
    )
    ev_after = service.table("evidence").select("note").eq("scan_id", target_id).execute().data
    check(
        "viewer",
        "left the evidence exactly as it was",
        [e["note"] for e in ev_after] == ["rls check"],
    )

    # ------------------------------------------------------------------ 3. the admin sees it all
    print("\n3. Admin - the full dashboard and the audit log")
    for view in (
        "dashboard_summary",
        "top_violations",
        "scans_by_category",
        "dashboard_recent_scans",
    ):
        data = admin.table(view).select("*").execute().data
        check("admin", f"reads {view}", data is not None, f"{len(data)} rows")

    titled = admin.table("top_violations").select("rule_id, title").limit(5).execute().data
    check(
        "admin",
        "top violations carry a rule title",
        all(v["title"] for v in titled),
        ", ".join(f"{v['rule_id']}" for v in titled),
    )

    audit = admin.table("audit_log").select("*").order("at", desc=True).limit(200).execute().data
    check("admin", "reads the audit log", len(audit) > 0, f"{len(audit)} entries")

    everyone = admin.table("profiles").select("id, role").execute().data
    check("admin", "sees every profile", len(everyone) >= 3, f"{len(everyone)} profiles")

    all_scans = admin.table("scans").select("id").execute().data
    viewer_scans = viewer.table("scans").select("id").execute().data
    check(
        "admin",
        "sees at least what a viewer sees",
        len(all_scans) >= len(viewer_scans),
        f"{len(all_scans)} vs {len(viewer_scans)}",
    )

    # -------------------------------------------------------- 3b. what the dashboard counts
    # The one arithmetic that must not be got wrong: a scan the pipeline could not finish is not
    # a compliant scan. `score([])` is 100 by construction, so a failed scan carrying a score
    # would show up as a perfect pack — the same wrong answer the worker's own guard exists to
    # prevent. Two rows, one done and perfect and one failed, and the deltas have to say so.
    print("\n3b. Dashboard totals - a failed scan is not a compliant scan")
    fail_id, pass_id = str(uuid.uuid4()), str(uuid.uuid4())
    before_totals = admin.table("dashboard_summary").select("*").single().execute().data
    inspector.table("scans").insert(
        [
            {
                "id": pass_id,
                "inspector_id": inspector_id,
                "source": "package",
                "status": "done",
                "compliance_score": 100,
            },
            {
                "id": fail_id,
                "inspector_id": inspector_id,
                "source": "package",
                "status": "failed",
                "error": "RLS check",
            },
        ]
    ).execute()
    after_totals = admin.table("dashboard_summary").select("*").single().execute().data
    delta = {k: (after_totals[k] or 0) - (before_totals[k] or 0) for k in before_totals}
    check("dashboard", "the failed scan is counted as failed", delta["scans_failed"] == 1)
    check("dashboard", "the failed scan is not counted as done", delta["scans_done"] == 1)
    check(
        "dashboard",
        "only the perfect scan is counted as compliant",
        delta["scans_compliant"] == 1,
        f"+{delta['scans_compliant']}",
    )
    check("dashboard", "both scans are counted in the total", delta["scans_total"] == 2)
    # The same count query the dashboard makes for "scans this week"; the boundary itself is
    # decided and tested in frontend/lib/dashboard.ts.
    week = (
        admin.table("scans").select("id", count="exact").gte("created_at", "1970-01-01").execute()
    )
    check("dashboard", "the scans-since count query runs", week.count is not None, str(week.count))
    admin.table("scans").delete().in_("id", [pass_id, fail_id]).execute()
    restored = admin.table("dashboard_summary").select("*").single().execute().data
    check(
        "dashboard",
        "removing them puts every total back",
        all(restored[k] == before_totals[k] for k in before_totals),
    )

    # ------------------------------------------------------------------ 4. the audit triggers
    print("\n4. Audit - written by the database, actor and values recorded")
    entries = (
        service.table("audit_log")
        .select("*")
        .eq("table_name", "scans")
        .eq("row_id", scan_id)
        .order("id")
        .execute()
        .data
    )
    actions = [e["action"] for e in entries]
    check("audit", "insert and update recorded", actions[:2] == ["INSERT", "UPDATE"], str(actions))
    check(
        "audit",
        "actor is the inspector who wrote the row",
        bool(entries) and entries[0]["actor_id"] == inspector_id,
        str(entries[0]["actor_id"]) if entries else "no entry",
    )
    check("audit", "timestamp populated", bool(entries) and bool(entries[0]["at"]))
    check(
        "audit",
        "insert stored the new row",
        bool(entries) and (entries[0]["new_row"] or {}).get("location") == "RLS check",
    )
    upd = next((e for e in entries if e["action"] == "UPDATE"), None)
    check(
        "audit",
        "update stored only what changed, old and new",
        upd is not None
        and set(upd["new_row"]) == {"notes"}
        and upd["new_row"]["notes"] == "inspector note"
        and upd["old_row"]["notes"] is None,
        f"{upd['old_row']} -> {upd['new_row']}" if upd else "no update entry",
    )
    check(
        "audit",
        "nothing the viewer tried was recorded",
        not any(
            e["actor_id"] == viewer_id
            for e in service.table("audit_log").select("actor_id").execute().data
        ),
    )

    ev = (
        service.table("audit_log")
        .select("*")
        .eq("table_name", "evidence")
        .eq("row_id", evidence_id)
        .execute()
        .data
    )
    check("audit", "evidence insert recorded", len(ev) == 1, str([e["action"] for e in ev]))

    # Products, and with them the proof that the audit does not depend on the frontend: this
    # write is made with the service-role key, which never goes near a browser and bypasses RLS.
    # The trigger is on the table, so it fires anyway, and records no actor because there is
    # none — that is what the worker's own writes look like.
    product_id = str(uuid.uuid4())
    service.table("products").insert(
        {"id": product_id, "name": "RLS check product", "manufacturer": "RLS check"}
    ).execute()
    service.table("products").update({"category": "Test"}).eq("id", product_id).execute()
    service.table("products").delete().eq("id", product_id).execute()
    prod = (
        service.table("audit_log")
        .select("action, actor_id, old_row, new_row")
        .eq("table_name", "products")
        .eq("row_id", product_id)
        .order("id")
        .execute()
        .data
    )
    check(
        "audit",
        "a direct database write is audited, with no actor",
        [p["action"] for p in prod] == ["INSERT", "UPDATE", "DELETE"]
        and all(p["actor_id"] is None for p in prod),
        str([p["action"] for p in prod]),
    )
    check(
        "audit",
        "the product update recorded old and new",
        len(prod) == 3
        and prod[1]["old_row"] == {"category": None}
        and prod[1]["new_row"] == {"category": "Test"},
        str(prod[1]["new_row"]) if len(prod) > 1 else "no update entry",
    )

    # The audit table has no trigger on itself, so writing one entry cannot write another.
    self_audit = (
        service.table("audit_log").select("id").eq("table_name", "audit_log").execute().data
    )
    check(
        "audit",
        "the audit log does not audit itself",
        len(self_audit) == 0,
        f"{len(self_audit)} rows",
    )

    # ------------------------------------------------------------------ 5. clean up
    print("\n5. Clean up - the rows this script made are removed")
    deleted = refused(lambda: admin.table("scans").delete().eq("id", scan_id).execute())
    check("admin", "deletes the test scan", not deleted[0], deleted[1][:40])
    admin.table("scans").delete().eq("id", admin_scan_id).execute()
    service.storage.from_("scans").remove([f"{scan_id}/rls-check.txt"])
    left = service.table("scans").select("id").in_("id", [scan_id, admin_scan_id]).execute().data
    check("cleanup", "both test scans are gone", len(left) == 0, f"{len(left)} left")

    dels = (
        service.table("audit_log")
        .select("action, actor_id")
        .eq("row_id", scan_id)
        .eq("action", "DELETE")
        .execute()
        .data
    )
    check(
        "audit",
        "delete recorded, actor is the admin",
        len(dels) == 1 and dels[0]["actor_id"] == admin_id,
    )
    ev_del = (
        service.table("audit_log")
        .select("action")
        .eq("row_id", evidence_id)
        .eq("action", "DELETE")
        .execute()
        .data
    )
    check("audit", "the cascaded evidence delete is recorded", len(ev_del) == 1)

    if failures:
        print(f"\n{len(failures)} FAILED: " + ", ".join(failures))
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
