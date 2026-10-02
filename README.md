# Atlas Scholarship Intelligence Crawler

A submission-ready implementation for **Edxso AI Engineer Intern - Assignment 2: Build the Scholarship Intelligence Crawler**.

The project implements the required pipeline:

**Discover -> Crawl -> Extract -> Verify -> Score -> Store -> Update**

It is built with free/open-source technologies and uses SQLite by default. No paid API, paid scraping service, or hosted LLM is required.

## 1. What the assignment asks for

The assignment requires a working system that continuously discovers authentic scholarship opportunities for Indian students, converts unstructured web information into a common schema, verifies each record against the official/primary source, calculates an evidence-based confidence score, stores records in a database, detects changes between crawls, identifies stale/expired scholarships, and provides a small dashboard.

The important hard requirements are:

- 20+ real scholarship records
- 15+ verified against primary/official sources
- 10+ records with confidence >= 95%
- 3+ source types
- 2+ change-detection examples
- 2+ expired/stale examples
- field-level evidence traceability
- repeatable/automated crawling
- free/open-source/free-tier tools only

This implementation is designed around those requirements rather than around a particular framework.

## 2. Architecture

```text
                    +-----------------------+
                    | Seed source registry  |
                    | government / CSR /    |
                    | university / trust    |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | Discovery engine       |
                    | BFS + same-domain      |
                    | keyword prioritization |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | Fetcher                |
                    | requests + PDF parser  |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | Extraction engine      |
                    | HTML/PDF -> normalized |
                    | scholarship records     |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | Verification engine    |
                    | official source check  |
                    | evidence checks        |
                    | freshness checks       |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | Deterministic score    |
                    | 0-100, not LLM-made    |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | SQLite                 |
                    | records + evidence +   |
                    | snapshots + changes    |
                    +-----------+-----------+
                                |
                    +-----------+-----------+
                    |                       |
                    v                       v
           +----------------+      +----------------+
           | Update/history |      | Streamlit UI   |
           | change events  |      | search/details |
           +----------------+      +----------------+
```

## 3. Technology choices

| Area | Technology | Reason |
|---|---|---|
| Language | Python 3.11+ | Simple, portable, free |
| HTTP | Requests | Reliable standard HTTP client |
| HTML | BeautifulSoup | Lightweight HTML parsing |
| PDF | pypdf | Parse official scholarship guideline PDFs |
| Database | SQLite | Free, inspectable, zero server setup |
| UI | Streamlit | Fast working dashboard |
| Config | python-dotenv | Local environment configuration |
| Testing | pytest | Automated verification tests |
| Optional AI | Local Ollama HTTP endpoint | Free/local only; never used to invent facts or scores |

No API key is required for the default mode.

## 4. Project structure

```text
atlas-scholarship-crawler/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── fetcher.py
│   ├── discovery.py
│   ├── extractor.py
│   ├── verifier.py
│   ├── change_detector.py
│   ├── crawler.py
│   ├── cli.py
│   └── dashboard.py
├── data/
│   ├── seeds.json
│   └── sample_scholarships.json
├── scripts/
│   ├── seed_demo.py
│   └── demo_change.py
├── tests/
│   ├── test_confidence.py
│   ├── test_change_detection.py
│   └── test_discovery.py
├── .env.example
├── .gitignore
├── requirements.txt
├── schema.sql
├── TECHNICAL_NOTE.md
└── README.md
```

## 5. Setup - Windows PowerShell

### Step 1 - Clone the GitHub repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd atlas-scholarship-crawler
```

### Step 2 - Create a virtual environment

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Step 3 - Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4 - Configure environment

```powershell
Copy-Item .env.example .env
```

The default `.env` works without any API key.

### Step 5 - Initialize the database

```powershell
python -m app.cli init-db
```

The SQLite file is created at `data/atlas.db`.

## 6. Load the reproducible demonstration dataset

The repository includes a snapshot created from official scholarship sources checked on **2026-10-02**. It exists so the dashboard and submission can be demonstrated even when your machine has no internet access.

Run:

```powershell
python -m app.cli seed-demo
```

Then inspect the database:

```powershell
python -m app.cli stats
```

The demo dataset is not a substitute for live crawling. It is a reproducible starting snapshot; the live crawler is the actual implementation requested by the assignment.

## 7. Run the live crawler

```powershell
python -m app.cli crawl
```

The crawler will:

1. read the source registry in `data/seeds.json`;
2. open each seed source;
3. discover relevant same-domain links instead of relying only on one hard-coded scholarship list;
4. crawl HTML and linked official PDFs;
5. extract scholarship records;
6. classify the source type;
7. verify the official source;
8. calculate the deterministic evidence-based confidence score;
9. save field-level evidence;
10. compare the new record with the old DB record;
11. write change events without deleting history;
12. update status and last-verified timestamps.

For a smaller test crawl:

```powershell
$env:MAX_PAGES_PER_SEED="5"
python -m app.cli crawl
```

For a larger crawl:

```powershell
$env:MAX_PAGES_PER_SEED="40"
python -m app.cli crawl
```

## 8. Run the dashboard

```powershell
streamlit run app/dashboard.py
```

Open the local address printed by Streamlit, normally:

```text
http://localhost:8501
```

The dashboard includes:

- Total discovered
- Verified
- Review required
- Active
- Expired
- Recently updated
- Average confidence
- Searchable scholarship table
- Detailed scholarship page
- Confidence breakdown / "Why this score?"
- Last verified date
- Change history
- Source evidence

## 9. Demonstrate repeat crawling and change detection

The recommended demo flow is:

### First run

```powershell
python -m app.cli seed-demo
python -m app.cli stats
```

### Create a known old snapshot and then run change detection

```powershell
python scripts/demo_change.py
python -m app.cli stats
```

The script deliberately replays two documented 2026 deadline extensions in the database so the UI can show historical changes immediately. The production crawler uses the same mechanism automatically when a second live crawl observes a changed value.

The two real-world examples represented are:

1. HDFC Bank Parivartan ECSS: an earlier 2026 deadline was extended to 31 October 2026.
2. SBI Foundation Asha: an earlier 4 September 2026 deadline was extended to 19 September 2026.

The live current value is always taken from the primary program page; the historical value is retained only as change history/evidence.

## 10. How confidence is calculated

The score is deterministic and explainable. The LLM is **not** asked to invent a number.

```text
Official source                    25 points
Scholarship present on source     15 points
Official application URL           10 points
Eligibility evidence               10 points
Deadline evidence                  10 points
Currentness                         10 points
Field-level traceability            10 points
Extraction consistency               10 points
------------------------------------------------
Maximum                            100 points
```

A conflict penalty of up to 20 points is applied when multiple values for the same important field cannot be reconciled.

Verification-status rule:

```text
score >= 95  -> VERIFIED
score < 95   -> REVIEW_REQUIRED
```

Availability and verification are stored separately: `current_status` contains `ACTIVE`, `EXPIRED`, `NOT_YET_OPENED`, or `NO_LONGER_VERIFIABLE`, while `verification_status` contains `VERIFIED` or `REVIEW_REQUIRED`.

A field that is absent is never guessed. The extractor stores a transparent value such as:

```text
Not specified on the official source
```

rather than manufacturing an amount, income limit, date, or eligibility rule.

## 11. Evidence traceability

Every important extracted field is stored with an evidence row:

```text
Scholarship
   |
   +-- field: deadline
   |
   +-- source URL
   |
   +-- evidence snippet
   |
   +-- retrieved timestamp
```

This makes it possible to audit a displayed value back to its source.

## 12. Authenticity / official-source verification

The system never treats an aggregator as the authoritative source.

A source is considered official when its domain matches one of the configured official source domains or one of the high-confidence government/university domain patterns.

Examples included in the source registry:

- National Scholarship Portal: `scholarships.gov.in`
- HDFC Bank Parivartan programme: `parivartanecss.com`
- SBI Foundation Asha: `sbiashascholarship.co.in`
- LIC Golden Jubilee Foundation: `licindia.in`
- Amity University scholarships: `amity.edu`
- MAHE scholarships: `manipal.edu`
- J N Tata Endowment: `jntataendowment.org`

Aggregator pages may be discovered as hints in future extensions, but they are never promoted to authoritative source records by this implementation.

## 13. Discovery methodology

Discovery is deliberately not implemented as:

```text
URL 1 -> scraper 1
URL 2 -> scraper 2
URL 3 -> scraper 3
```

Instead, the crawler starts from a small seed registry and then performs breadth-first link discovery within each official domain. Links are scored by scholarship-related keywords such as:

```text
scholarship, fellowship, financial aid, funding, stipend,
scheme, student support, education assistance, apply
```

A source can therefore expose additional scholarship pages without requiring a new hard-coded record for each page.

## 14. Extraction methodology

The extractor uses several layers:

1. semantic headings and card-like containers;
2. visible text normalization;
3. JSON-LD where present;
4. keyword/context rules for deadlines, awards, income, merit, gender, category, domicile, institutions, documents, selection and renewal;
5. linked official PDF guideline extraction;
6. deterministic normalization into the common schema.

For pages with JavaScript-heavy content, the design can be extended with Playwright. The current default avoids that dependency and uses normal HTTP first.

## 15. Auto-crawler / repeatability

The database stores crawl runs and the raw content hash of crawled source pages. Running the crawler again updates the current record while retaining the old state in `change_events`.

Example:

```text
Run 1
  Scholarship A discovered
  Scholarship B discovered
  Scholarship C discovered

Run 2
  Scholarship A unchanged
  Scholarship B deadline changed -> CHANGE_DETECTED
  Scholarship C expired -> status updated
  Scholarship D newly discovered
```

## 16. Stale / expired detection

The crawler derives status using current source presence and deadline information.

Possible statuses:

- `ACTIVE`
- `NOT_YET_OPENED`
- `EXPIRED`
- `NO_LONGER_VERIFIABLE`
- `REVIEW_REQUIRED`

An old record is not silently deleted when it becomes unavailable. The current status is updated and the verification timestamp/history remains queryable.

## 17. Sample output

The included snapshot contains more than the assignment's 20-record minimum and intentionally includes government, corporate CSR, university and foundation/trust records so the dashboard demonstrates multiple source types.

The dataset includes both active and expired examples. This makes the UI useful for demonstrating stale-data handling instead of showing only currently open scholarships.

## 18. Useful commands

```powershell
# initialize
python -m app.cli init-db

# load demo snapshot
python -m app.cli seed-demo

# show metrics
python -m app.cli stats

# verify assignment minimums from the current database
python scripts/check_assignment.py

# live crawl
python -m app.cli crawl

# run tests
pytest -q

# start dashboard
streamlit run app/dashboard.py
```

## 19. How to record the demonstration video

The assignment requests a short working demonstration. Record this sequence:

```text
1. Open terminal
2. python -m app.cli seed-demo
3. streamlit run app/dashboard.py
4. Show the dashboard counters
5. Search for a scholarship
6. Open one scholarship
7. Show confidence breakdown
8. Show source evidence
9. Show change history
10. Return to terminal
11. python -m app.cli crawl
12. Refresh dashboard
13. Explain that unchanged records are kept, changed fields are logged, and expired records are reclassified
```

## 20. GitHub submission steps

```powershell
git init
git add .
git commit -m "Build scholarship intelligence crawler"
git branch -M main
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
git push -u origin main
```

Do not commit `.env` or `data/atlas.db` if you do not want to share your local DB. The `.gitignore` already excludes the live database and environment file.

For the assignment submission, keep the repository's source code, README, requirements, schema, seed/sample data, tests and configuration visible.

## 21. Important authenticity note

The sample snapshot is a dated reproducibility fixture, not a statement that every scholarship will remain open after the snapshot date. The live crawler is the authoritative mechanism for updating status and deadlines. Users should always follow the official source URL displayed by the application before acting on a scholarship.
