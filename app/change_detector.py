from __future__ import annotations

from .models import ScholarshipRecord

TRACKED_FIELDS = (
    "amount", "eligibility", "academic_requirements", "education_level", "income_criteria",
    "age_criteria", "gender_criteria", "category_criteria", "domicile_requirements",
    "institution_requirements", "opening_date", "closing_date", "documents_required",
    "selection_process", "renewal_requirements", "current_status", "application_url", "source_url",
)


def compare(old: dict, new: ScholarshipRecord) -> list[dict]:
    result = []
    data = new.to_dict()
    for field in TRACKED_FIELDS:
        old_value = old.get(field)
        new_value = data.get(field)
        if (old_value or "") != (new_value or ""):
            result.append({"field_name": field, "old_value": old_value, "new_value": new_value})
    return result
