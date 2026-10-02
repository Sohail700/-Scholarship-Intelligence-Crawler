# Technical Note - Atlas Scholarship Intelligence Crawler

## Architecture

The system is a Python application built around a small crawl pipeline. A JSON source registry provides only a small number of official seed pages. The discovery layer performs breadth-first traversal and ranks candidate links using scholarship-related keywords. The fetcher retrieves HTML and official PDFs. The extractor converts page text into a common scholarship schema. The verifier checks whether the source is official, whether the scholarship is actually present, whether application/deadline evidence exists, and whether important fields are traceable. A deterministic scorer converts those signals into a 0-100 confidence value. SQLite stores current records, evidence, crawl runs, content hashes and change events. Streamlit exposes the resulting intelligence through a dashboard.

## Technology choices

Python was selected for its mature HTML/PDF processing ecosystem. Requests and BeautifulSoup keep the crawler lightweight. pypdf allows official guideline PDFs to be processed without paid services. SQLite satisfies the assignment's inspectable free-database requirement. Streamlit supplies the requested working interface with minimal infrastructure. The optional local Ollama hook is deliberately non-authoritative: it can help normalize text, but it is never allowed to manufacture values or create the confidence score.

## Discovery methodology

The system intentionally avoids a one-URL/one-scraper design. Seeds are source families, not individual scholarship records. A seed may expose many scholarship pages, specification PDFs, FAQs and application pages. The crawler follows relevant links within the official domain and deduplicates records by normalized scholarship name/provider. A future extension can add sitemap ingestion, RSS/Atom, or a local search index without changing the core verification/database design.

## Extraction methodology

Visible text is normalized first. Candidate scholarship titles are identified from semantic headings and scholarship-related keywords. Context windows around terms such as `deadline`, `last date`, `income`, `marks`, `award`, `eligibility`, `documents`, `selection`, and `renewal` are used to capture field values. Currency, percentage, date and age patterns are normalized conservatively. Linked PDF guidelines can add supporting evidence. A missing value is represented explicitly as `Not specified on the official source`; it is never invented.

## Verification methodology

Official-source verification uses the configured official-domain registry plus government/university domain checks. The system distinguishes `source_url` from `application_url`. Aggregator pages are not treated as authoritative. Every important displayed field can be accompanied by evidence containing the source URL, snippet and retrieval time.

## Confidence-score methodology

The score is calculated by deterministic rules, not by an LLM:

- Official source: 25
- Scholarship present on official source: 15
- Official application URL: 10
- Eligibility evidence: 10
- Deadline evidence: 10
- Currentness: 10
- Field-level traceability: 10
- Extraction consistency: 10

Total = 100 before conflict penalties. Conflicts can reduce the score by up to 20. A score of 95 or higher produces `VERIFIED`; anything below 95 produces `REVIEW_REQUIRED`.

This directly addresses the assignment's rule that a model must not simply generate a confidence number.

## Anti-hallucination design

The extractor is evidence-first. Values are accepted only when a matching source context is available. The database also stores the evidence used for important values, making it possible to go from `Database -> Official Source -> Evidence -> Extracted Value`. The optional local LLM can only be used for normalization and should be disabled for strict audit mode. The confidence engine is always deterministic.

## Change detection

Before an update, the crawler loads the previous record. Significant fields are compared against the newly extracted values. Any change produces a `change_event` containing field name, old value, new value, detection time, source URL and evidence. The current record is updated for normal application queries, but the historical value remains in `change_events`. This prevents silent overwrites.

## Stale and expired data

Deadline dates are parsed from official evidence and evaluated against the crawl date. Past deadlines become `EXPIRED`. Pages that disappear or cannot be re-verified can become `NO_LONGER_VERIFIABLE`. Sources that have not yet opened can be represented as `NOT_YET_OPENED`. The dashboard makes these states visible instead of deleting them.

## Submission interpretation

The implementation is intended to be a working crawler, not a design-only document. The repository includes executable code, a live source registry, a SQLite schema, sample data, tests, and a dashboard. The reproducibility snapshot helps demonstrate the application when a live internet connection is unavailable; the same code path supports repeated live crawling.
