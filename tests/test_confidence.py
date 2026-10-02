from app.models import EvidenceItem, ScholarshipRecord
from app.verifier import score_record


def test_high_confidence_is_deterministic():
    ev = [EvidenceItem(field, "https://example.gov.in/scholarship", f"Evidence for {field}") for field in [
        "name", "amount", "eligibility", "academic_requirements", "education_level",
        "income_criteria", "closing_date", "documents_required", "selection_process",
    ]]
    r = ScholarshipRecord(
        name="Example Scholarship",
        provider="Example Government",
        source_url="https://example.gov.in/scholarship",
        application_url="https://example.gov.in/apply",
        source_type="Government",
        amount="₹50,000",
        eligibility="Indian students",
        academic_requirements="60%",
        education_level="UG",
        income_criteria="Not above ₹3 lakh",
        closing_date="2026-12-31",
        evidence=ev,
        current_status="ACTIVE",
    )
    score, breakdown = score_record(r, official_domain="example.gov.in")
    assert score >= 95
    assert breakdown["official_source"] == 25


def test_missing_evidence_requires_review():
    r = ScholarshipRecord(
        name="Example Scholarship",
        provider="Provider",
        source_url="https://example.gov.in/scholarship",
        application_url="https://example.gov.in/apply",
        current_status="REVIEW_REQUIRED",
        evidence=[],
    )
    score, _ = score_record(r, official_domain="example.gov.in")
    assert score < 95
