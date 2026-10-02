from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Database  # noqa: E402


def main() -> None:
    db = Database()
    db.init()
    s = db.stats()
    with db.conn() as con:
        changes = con.execute("SELECT COUNT(*) c FROM change_events").fetchone()["c"]
        expired = con.execute("SELECT COUNT(*) c FROM scholarships WHERE current_status IN ('EXPIRED','NO_LONGER_VERIFIABLE')").fetchone()["c"]
        high = con.execute("SELECT COUNT(*) c FROM scholarships WHERE confidence_score >= 95").fetchone()["c"]

    checks = {
        "20+ real records in database": s["total"] >= 20,
        "15+ verified": s["verified"] >= 15,
        "10+ confidence >= 95": high >= 10,
        "3+ source types": len(s["source_types"]) >= 3,
        "2+ change events": changes >= 2,
        "2+ expired/stale": expired >= 2,
    }
    print("Atlas Assignment 2 checks")
    for label, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'} - {label}")
    print(f"\nCounts: total={s['total']}, verified={s['verified']}, high_confidence={high}, changes={changes}, expired_or_stale={expired}")
    print(f"Source types: {', '.join(s['source_types'])}")
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
