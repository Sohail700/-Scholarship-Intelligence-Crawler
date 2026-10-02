from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Database  # noqa: E402
from app.models import EvidenceItem, ScholarshipRecord  # noqa: E402
from app.verifier import score_record  # noqa: E402


def replay_change(name_contains: str, old_deadline: str, source_url: str, evidence_url: str) -> None:
    db = Database()
    rows = [r for r in db.list_scholarships() if name_contains.lower() in r["name"].lower()]
    if not rows:
        raise SystemExit(f"Scholarship containing {name_contains!r} not found. Run seed-demo first.")
    row = rows[0]
    data = dict(row)
    data["closing_date"] = old_deadline
    old_evidence = EvidenceItem("closing_date", evidence_url, f"Historical deadline stored for change demonstration: {old_deadline}")
    current_evidence = EvidenceItem("closing_date", source_url, f"Current official source deadline: {row['closing_date']}")
    record = ScholarshipRecord(
        name=row["name"], provider=row["provider"], source_url=row["source_url"], application_url=row["application_url"],
        source_type=row["source_type"], amount=row["amount"], eligibility=row["eligibility"],
        academic_requirements=row["academic_requirements"], education_level=row["education_level"],
        income_criteria=row["income_criteria"], age_criteria=row["age_criteria"], gender_criteria=row["gender_criteria"],
        category_criteria=row["category_criteria"], domicile_requirements=row["domicile_requirements"],
        institution_requirements=row["institution_requirements"], opening_date=row["opening_date"],
        closing_date=row["closing_date"], documents_required=row["documents_required"],
        selection_process=row["selection_process"], renewal_requirements=row["renewal_requirements"],
        current_status=row["current_status"], confidence_score=float(row["confidence_score"]),
        confidence_breakdown={}, evidence=[old_evidence, current_evidence], content_hash=row["content_hash"] or "demo",
    )
    score_record(record, official_domain=source_url.split("//", 1)[1].split("/", 1)[0].removeprefix("www."))
    # Insert a historical event manually without replacing the current deadline.
    with db.conn() as con:
        con.execute(
            "INSERT INTO change_events(scholarship_id,field_name,old_value,new_value,detected_at,source_url,evidence_text) VALUES(?,?,?,?,?,?,?)",
            (row["id"], "closing_date", old_deadline, row["closing_date"], "2026-10-02T00:00:00+00:00", source_url, f"Historical value {old_deadline} -> current value {row['closing_date']}. Evidence: {evidence_url}"),
        )
    print(f"Recorded change: {row['name']} | {old_deadline} -> {row['closing_date']}")


def main() -> None:
    replay_change(
        "Parivartan ECSS Programme - School",
        "2026-08-31",
        "https://www.parivartanecss.com/",
        "https://www.shiksha.com/college/articles/hdfc-scholarship-2026-27-eligibility-amount-last-date-and-how-to-apply-online-blogId-241309",
    )
    replay_change(
        "SBI Platinum Jubilee Asha",
        "2026-09-04",
        "https://www.sbiashascholarship.co.in/",
        "https://assamjobapply.com/sbi-asha-scholarship-2026-27/",
    )


if __name__ == "__main__":
    main()
