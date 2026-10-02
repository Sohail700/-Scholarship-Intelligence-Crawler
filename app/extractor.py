from __future__ import annotations

import re
from datetime import date, datetime
from typing import Iterable
from urllib.parse import urlparse

from dateutil import parser as date_parser

from .models import EvidenceItem, ScholarshipRecord

PLACEHOLDER = "Not specified on the official source"

CURRENCY_RE = re.compile(r"(?:₹|Rs\.?|INR)\s?[0-9][0-9,]*(?:\.\d+)?(?:\s?(?:lakh|crore))?", re.I)
DATE_RE = re.compile(
    r"\b(?:0?[1-9]|[12]\d|3[01])[-/ ](?:0?[1-9]|1[0-2])[-/ ](?:20\d{2})\b|"
    r"\b(?:0?[1-9]|[12]\d|3[01])\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d{2}\b",
    re.I,
)
PERCENT_RE = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%|\b\d(?:\.\d+)?\s?CGPA\b", re.I)


def clean(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip(" -:;|")
    return value


def snippet(text: str, needle: str, radius: int = 260) -> str:
    if not text:
        return ""
    idx = text.lower().find(needle.lower())
    if idx < 0:
        return clean(text[:radius])
    start = max(0, idx - radius // 2)
    end = min(len(text), idx + len(needle) + radius // 2)
    return clean(text[start:end])


def find_context(text: str, terms: Iterable[str], *, limit: int = 2) -> tuple[str, list[str]]:
    lines = [clean(x) for x in text.splitlines() if clean(x)]
    found: list[str] = []
    for line in lines:
        low = line.lower()
        if any(term.lower() in low for term in terms):
            found.append(line)
            if len(found) >= limit:
                break
    if not found:
        return PLACEHOLDER, []
    return " ".join(found), found


def extract_dates(text: str, keywords: Iterable[str]) -> tuple[str, str, list[EvidenceItem]]:
    lines = [clean(x) for x in text.splitlines() if clean(x)]
    opening = ""
    closing = ""
    evidence: list[EvidenceItem] = []
    for line in lines:
        low = line.lower()
        dates = DATE_RE.findall(line)
        if not dates:
            continue
        if any(k in low for k in ("open from", "opening", "start date", "applications open")) and not opening:
            opening = dates[0]
        if any(k in low for k in ("closing", "close on", "last date", "deadline", "application open till")) and not closing:
            closing = dates[0]
    return opening, closing, evidence


def normalize_date(value: str) -> str:
    if not value:
        return ""
    try:
        dt = date_parser.parse(value, dayfirst=True, fuzzy=True)
        return dt.date().isoformat()
    except Exception:
        return value


def classify_source(source_url: str, official_domain: str, declared_type: str | None = None) -> str:
    if declared_type:
        return declared_type
    host = (urlparse(source_url).hostname or "").lower()
    if host.endswith(".gov.in") or host == "gov.in":
        return "Government"
    if host.endswith(".ac.in") or host.endswith(".edu.in"):
        return "University"
    return "Other"


def extract_amount(text: str) -> tuple[str, list[str]]:
    matches = CURRENCY_RE.findall(text)
    if not matches:
        return PLACEHOLDER, []
    unique = list(dict.fromkeys(clean(x) for x in matches))
    return " / ".join(unique[:3]), unique[:3]


def extract_field(text: str, terms: tuple[str, ...], default: str = PLACEHOLDER) -> tuple[str, list[str]]:
    value, evidence = find_context(text, terms, limit=3)
    return (value if value != PLACEHOLDER else default), evidence


def build_record(
    *,
    page_text: str,
    source_url: str,
    source_type: str,
    provider: str,
    discovered_title: str | None = None,
    application_url: str = "",
    extra_source_url: str | None = None,
) -> ScholarshipRecord | None:
    title = clean(discovered_title or "")
    if not title:
        for line in page_text.splitlines()[:40]:
            c = clean(line)
            if "scholarship" in c.lower() or "fellowship" in c.lower():
                title = c
                break
    if not title or len(title) < 8:
        return None

    amount, amount_ev = extract_amount(page_text)
    eligibility, elig_ev = extract_field(page_text, ("eligibility", "eligible", "who can apply", "eligibility criteria"))
    academic, academic_ev = extract_field(page_text, ("marks", "percentage", "percentile", "cgpa", "academic requirement"))
    income, income_ev = extract_field(page_text, ("family income", "annual income", "income from all sources", "parental income"))
    age, age_ev = extract_field(page_text, ("age", "years of age"))
    gender, gender_ev = extract_field(page_text, ("girl", "female", "women", "gender"))
    category, cat_ev = extract_field(page_text, ("sc", "st", "obc", "ews", "disab", "category"))
    domicile, domicile_ev = extract_field(page_text, ("domicile", "resident of", "state/ut", "state or union territory"))
    institution, inst_ev = extract_field(page_text, ("recognized institution", "aicte approved", "university", "college", "institution"))
    documents, docs_ev = extract_field(page_text, ("documents required", "documents", "marksheet", "income certificate"))
    selection, selection_ev = extract_field(page_text, ("selection process", "shortlisted", "interview", "selection"))
    renewal, renewal_ev = extract_field(page_text, ("renewal", "renewed", "continuation"))
    education, education_ev = extract_field(page_text, ("class 1", "class 9", "class xii", "undergraduate", "postgraduate", "degree", "diploma", "iti", "mba", "phd"))

    opening, closing, _ = extract_dates(page_text, ("open", "start", "close", "deadline"))
    if not closing:
        # Fallback: explicit 'last date' anywhere.
        for line in page_text.splitlines():
            if "last date" in line.lower() or "deadline" in line.lower():
                m = DATE_RE.search(line)
                if m:
                    closing = m.group(0)
                    break
    opening = normalize_date(opening)
    closing = normalize_date(closing)

    status = status_from_text_and_deadline(page_text, closing)
    evidence_url = extra_source_url or source_url
    evidence: list[EvidenceItem] = []
    base_fields = {
        "name": (title, title),
        "amount": (amount, "amount"),
        "eligibility": (eligibility, "eligibility"),
        "academic_requirements": (academic, "marks"),
        "income_criteria": (income, "income"),
        "documents_required": (documents, "documents"),
        "selection_process": (selection, "selection"),
        "renewal_requirements": (renewal, "renewal"),
        "education_level": (education, "education"),
    }
    for field_name, (value, anchor) in base_fields.items():
        quote = snippet(page_text, anchor) if anchor in page_text.lower() else "See official source page."
        evidence.append(EvidenceItem(field_name, evidence_url, quote if quote else "See official source page."))
    if closing:
        evidence.append(EvidenceItem("closing_date", evidence_url, snippet(page_text, closing)))
    if opening:
        evidence.append(EvidenceItem("opening_date", evidence_url, snippet(page_text, opening)))

    return ScholarshipRecord(
        name=title,
        provider=provider,
        source_url=source_url,
        application_url=application_url or source_url,
        source_type=source_type,
        amount=amount,
        eligibility=eligibility,
        academic_requirements=academic,
        education_level=education,
        income_criteria=income,
        age_criteria=age,
        gender_criteria=gender,
        category_criteria=category,
        domicile_requirements=domicile,
        institution_requirements=institution,
        opening_date=opening,
        closing_date=closing,
        documents_required=documents,
        selection_process=selection,
        renewal_requirements=renewal,
        current_status=status,
        evidence=evidence,
    )


def status_from_text_and_deadline(text: str, closing: str) -> str:
    upper = text.upper()
    if "NOT YET OPENED" in upper:
        return "NOT_YET_OPENED"
    if closing:
        try:
            dt = datetime.fromisoformat(closing).date()
            return "ACTIVE" if dt >= date.today() else "EXPIRED"
        except Exception:
            pass
    if any(x in upper for x in ("APPLICATIONS ARE CLOSED", "APPLICATION CLOSED", "LAST DATE HAS PASSED")):
        return "EXPIRED"
    return "REVIEW_REQUIRED"
