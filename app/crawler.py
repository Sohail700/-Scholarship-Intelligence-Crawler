from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .change_detector import compare
from .config import ROOT, SETTINGS
from .database import Database
from .discovery import discover, load_seeds
from .extractor import build_record, classify_source
from .fetcher import Fetcher
from .models import ScholarshipRecord
from .verifier import score_record

SCHOLARSHIP_TITLE_HINTS = (
    "scholarship", "fellowship", "stipend", "financial assistance", "education grant", "coaching"
)


def candidate_titles_from_html(html_text: str) -> list[str]:
    soup = BeautifulSoup(html_text, "html.parser")
    titles: list[str] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        title = " ".join(tag.get_text(" ", strip=True).split())
        low = title.lower()
        if any(h in low for h in SCHOLARSHIP_TITLE_HINTS) and len(title) >= 12:
            titles.append(title)
    return list(dict.fromkeys(titles))


def split_nsp_like_text(text: str) -> list[tuple[str, str]]:
    lines = [" ".join(x.split()) for x in text.splitlines() if " ".join(x.split())]
    results: list[tuple[str, str]] = []
    department = "National Scholarship Portal / Government of India"
    for line in lines:
        low = line.lower()
        if any(x in low for x in ("ministry of ", "department of ", "all india council", "north eastern council")) and "scholarship" not in low:
            department = line
        if any(h in low for h in SCHOLARSHIP_TITLE_HINTS) and len(line) >= 18 and len(line) <= 220:
            if "schemes on nsp" in low or "scholarship eligibility" in low:
                continue
            results.append((line, department))
    # de-duplicate by normalized title
    seen = set()
    unique = []
    for title, provider in results:
        key = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
        if key not in seen:
            seen.add(key)
            unique.append((title, provider))
    return unique


class Crawler:
    def __init__(self) -> None:
        self.fetcher = Fetcher()
        self.db = Database()
        self.seeds = load_seeds(ROOT / "data" / "seeds.json")

    def run(self) -> dict:
        self.db.init()
        run_id = self.db.begin_run()
        discovered_count = 0
        stored_count = 0
        updated_count = 0
        error_count = 0
        all_seen_keys: set[str] = set()

        try:
            for seed in self.seeds:
                try:
                    pages = discover(seed, self.fetcher)
                except Exception:
                    error_count += 1
                    continue
                max_pages = SETTINGS.max_pages_per_seed
                for url, _depth in pages[:max_pages]:
                    discovered_count += 1
                    try:
                        fetched = self.fetcher.fetch(url)
                        source_type = classify_source(fetched.final_url, seed["official_domain"], seed.get("source_type"))
                        # The NSP listing itself exposes all scheme records. Linked guideline PDFs are
                        # discoverable evidence, but are not inserted as separate scholarships because
                        # their document titles can create false duplicate records.
                        is_nsp_listing = urlparse(url).path.lower().endswith("all-scholarships") or "scholarships.gov.in/All-Scholarships" in url
                        if seed["official_domain"] == "scholarships.gov.in" and not is_nsp_listing:
                            continue
                        # NSP list pages expose many records from a single page.
                        if is_nsp_listing:
                            pairs = split_nsp_like_text(fetched.text)
                            for title, provider in pairs:
                                rec = build_record(
                                    page_text=fetched.text,
                                    source_url=fetched.final_url,
                                    source_type=source_type,
                                    provider=provider,
                                    discovered_title=title,
                                    application_url="https://scholarships.gov.in/",
                                )
                                if rec and rec.canonical_key not in all_seen_keys:
                                    rec.content_hash = fetched.content_hash
                                    score_record(rec, official_domain=seed["official_domain"], page_present=True)
                                    _id, existed, _changes = self.db.upsert(rec)
                                    all_seen_keys.add(rec.canonical_key)
                                    stored_count += 1
                                    updated_count += int(existed)
                        else:
                            rec = build_record(
                                page_text=fetched.text,
                                source_url=fetched.final_url,
                                source_type=source_type,
                                provider=seed.get("provider", "Unknown provider"),
                                application_url=fetched.final_url,
                            )
                            if rec and rec.canonical_key not in all_seen_keys:
                                rec.content_hash = fetched.content_hash
                                score_record(rec, official_domain=seed["official_domain"], page_present=True)
                                _id, existed, _changes = self.db.upsert(rec)
                                all_seen_keys.add(rec.canonical_key)
                                stored_count += 1
                                updated_count += int(existed)
                    except Exception:
                        error_count += 1
                        continue
        finally:
            self.db.finish_run(
                run_id,
                discovered=discovered_count,
                stored=stored_count,
                updated=updated_count,
                errors=error_count,
                notes="Live crawl complete; see individual records/evidence for audit details.",
            )
        return {
            "run_id": run_id,
            "discovered": discovered_count,
            "stored": stored_count,
            "updated": updated_count,
            "errors": error_count,
        }
