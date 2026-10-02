from app.change_detector import compare
from app.models import ScholarshipRecord


def test_deadline_change_detected():
    old = {
        "amount": "₹10,000",
        "eligibility": "Indian students",
        "academic_requirements": "60%",
        "education_level": "UG",
        "income_criteria": "<= 4 lakh",
        "closing_date": "2026-08-31",
        "documents_required": "Marksheets",
        "selection_process": "Merit",
        "renewal_requirements": "Pass year",
        "current_status": "ACTIVE",
        "application_url": "https://example.gov.in/apply",
        "source_url": "https://example.gov.in/scholarship",
    }
    new = ScholarshipRecord(
        name="Example Scholarship", provider="Example", source_url="https://example.gov.in/scholarship",
        application_url="https://example.gov.in/apply", amount="₹10,000", eligibility="Indian students",
        academic_requirements="60%", education_level="UG", income_criteria="<= 4 lakh", closing_date="2026-09-15",
        documents_required="Marksheets", selection_process="Merit", renewal_requirements="Pass year", current_status="ACTIVE",
    )
    changes = compare(old, new)
    assert any(x["field_name"] == "closing_date" for x in changes)
