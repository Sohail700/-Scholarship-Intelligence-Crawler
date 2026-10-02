from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class EvidenceItem:
    field_name: str
    source_url: str
    evidence_text: str


@dataclass
class ScholarshipRecord:
    name: str
    provider: str
    source_url: str
    application_url: str = ""
    source_type: str = "Other"
    amount: str = "Not specified on the official source"
    eligibility: str = "Not specified on the official source"
    academic_requirements: str = "Not specified on the official source"
    education_level: str = "Not specified on the official source"
    income_criteria: str = "Not specified on the official source"
    age_criteria: str = "Not specified on the official source"
    gender_criteria: str = "Not specified on the official source"
    category_criteria: str = "Not specified on the official source"
    domicile_requirements: str = "Not specified on the official source"
    institution_requirements: str = "Not specified on the official source"
    opening_date: str = ""
    closing_date: str = ""
    documents_required: str = "Not specified on the official source"
    selection_process: str = "Not specified on the official source"
    renewal_requirements: str = "Not specified on the official source"
    current_status: str = "REVIEW_REQUIRED"
    verification_status: str = "REVIEW_REQUIRED"
    confidence_score: float = 0.0
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    last_verified: str = ""
    evidence: List[EvidenceItem] = field(default_factory=list)
    content_hash: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["evidence"] = [asdict(e) for e in self.evidence]
        return data

    @property
    def canonical_key(self) -> str:
        normalized = " ".join(self.name.lower().replace("-", " ").split())
        provider = " ".join(self.provider.lower().replace("-", " ").split())
        return f"{normalized}|{provider}"
