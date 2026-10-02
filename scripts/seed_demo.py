from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Database  # noqa: E402
from app.models import EvidenceItem, ScholarshipRecord  # noqa: E402
from app.verifier import score_record  # noqa: E402


def seed() -> None:
    db = Database()
    db.init()
    records = json.loads((ROOT / "data" / "sample_scholarships.json").read_text(encoding="utf-8"))
    for data in records:
        evidence = [EvidenceItem(**x) for x in data.pop("evidence", [])]
        record = ScholarshipRecord(**data, evidence=evidence)
        score_record(record, official_domain=data["source_url"].split("//", 1)[1].split("/", 1)[0].removeprefix("www."))
        db.upsert(record)
    print(f"Loaded {len(records)} demo scholarship records into {db.path}")


if __name__ == "__main__":
    seed()
