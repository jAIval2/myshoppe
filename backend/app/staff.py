"""Explicit operator command: python -m app.staff EMAIL ROLE [--revoke]."""

import argparse
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert
from . import db
from .identity import PERMISSIONS, Actor, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("role", choices=PERMISSIONS)
    parser.add_argument("--revoke", action="store_true")
    args = parser.parse_args()
    with db.engine.begin() as c:
        user = c.execute(select(db.profiles).where(db.profiles.c.email == args.email)).mappings().first()
        if not user:
            raise SystemExit("Account must first sign in using verified email. No account was changed.")
        if args.revoke:
            c.execute(update(db.staff).where(db.staff.c.user_id == user["id"]).values(active=False))
        else:
            c.execute(
                insert(db.staff)
                .values(user_id=user["id"], role=args.role, active=True)
                .on_conflict_do_update(
                    index_elements=[db.staff.c.user_id], set_={"role": args.role, "active": True}
                )
            )
        c.execute(delete(db.sessions).where(db.sessions.c.user_id == user["id"]))
        audit(
            c,
            Actor("operator-cli"),
            "staff.revoked" if args.revoke else "staff.granted",
            user["id"],
            {"role": args.role},
        )
    print("Staff membership updated; existing sessions revoked. Sign in again with MFA.")


if __name__ == "__main__":
    main()
