from __future__ import annotations

from datetime import date, datetime, timedelta
from urllib.parse import urlparse

from .models import ScholarshipRecord

WEIGHTS = {
    "official_source": 25,
    "present_on_source": 15,
    "official_application_url": 10,
    "eligibility_evidence": 10,
    "deadline_evidence": 10,
    "currentness": 10,
    "field_traceability": 10,
    "extraction_consistency": 10,
}

IMPORTANT_FIELDS = (
    "amount",
    "eligibility",
    "academic_requirements",
    "education_level",
    "income_criteria",
    "closing_date",
    "documents_required",
    "selection_process",
)


def official_source_ok(record: ScholarshipRecord, official_domain: str) -> bool:
    host = (urlparse(record.source_url).hostname or "").lower().removeprefix("www.")
    official = official_domain.lower().removeprefix("www.")
    return host == official or host.endswith("." + official)


def application_url_ok(record: ScholarshipRecord, official_domain: str) -> bool:
    if not record.application_url:
        return False
    host = (urlparse(record.application_url).hostname or "").lower().removeprefix("www.")
    official = official_domain.lower().removeprefix("www.")
    if host == official or host.endswith("." + official):
        return True
    # NSP applications commonly start at the official portal while a program page is under a provider path.
    return host.endswith("scholarships.gov.in") or host.endswith("parivartanecss.com")


def nonempty_supported(value: str) -> bool:
    return bool(value and value.strip() and value.strip() != "Not specified on the official source")


def score_record(record: ScholarshipRecord, *, official_domain: str, page_present: bool = True) -> tuple[float, dict[str, float]]:
    breakdown: dict[str, float] = {}
    breakdown["official_source"] = float(WEIGHTS["official_source"] if official_source_ok(record, official_domain) else 0)
    breakdown["present_on_source"] = float(WEIGHTS["present_on_source"] if page_present else 0)
    breakdown["official_application_url"] = float(WEIGHTS["official_application_url"] if application_url_ok(record, official_domain) else 0)

    evidence_fields = {item.field_name for item in record.evidence}
    breakdown["eligibility_evidence"] = float(WEIGHTS["eligibility_evidence"] if ("eligibility" in evidence_fields or nonempty_supported(record.eligibility)) else 0)
    breakdown["deadline_evidence"] = float(WEIGHTS["deadline_evidence"] if ("closing_date" in evidence_fields or nonempty_supported(record.closing_date)) else 0)

    currentness = 0
    if record.current_status == "ACTIVE" or record.current_status == "NOT_YET_OPENED":
        currentness = WEIGHTS["currentness"]
    elif record.current_status == "EXPIRED":
        # The source can still be authentic and current even when the opportunity itself has ended.
        currentness = 6
    breakdown["currentness"] = float(currentness)

    traced = sum(1 for field in IMPORTANT_FIELDS if field in evidence_fields or nonempty_supported(getattr(record, field)))
    breakdown["field_traceability"] = WEIGHTS["field_traceability"] * (traced / len(IMPORTANT_FIELDS))

    consistency = bool(record.name and record.provider and record.source_url and len(record.name) >= 8)
    breakdown["extraction_consistency"] = float(WEIGHTS["extraction_consistency"] if consistency else 0)

    score = sum(breakdown.values())
    record.confidence_score = round(score, 1)
    record.confidence_breakdown = breakdown
    record.verification_status = "VERIFIED" if score >= 95 else "REVIEW_REQUIRED"
    return record.confidence_score, breakdown
