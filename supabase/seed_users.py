"""Create the 3 demo users (admin, inspector, viewer). Demo passwords only; change these.

Run: cd worker && uv run --env-file ../.env python ../supabase/seed_users.py
"""

from __future__ import annotations

import os

from supabase import create_client

USERS = [
    ("admin@example.com", "Admin-demo-2026", "admin", "Demo Admin"),
    ("inspector@example.com", "Inspector-demo-2026", "inspector", "Demo Inspector"),
    ("viewer@example.com", "Viewer-demo-2026", "viewer", "Demo Viewer"),
]


def main() -> None:
    url = os.environ.get("SUPABASE_URL") or os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    sb = create_client(url, os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    existing = {u.email: u.id for u in sb.auth.admin.list_users()}
    for email, password, role, name in USERS:
        uid = existing.get(email)
        if uid is None:
            created = sb.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {"full_name": name},
                }
            )
            assert created.user is not None
            uid = created.user.id
        # the on_auth_user_created trigger made the profile with role 'viewer'; promote here
        sb.table("profiles").update({"role": role, "full_name": name}).eq("id", uid).execute()
        print(f"{email:24} {role:10} {password}")


if __name__ == "__main__":
    main()
