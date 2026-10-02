# Submission Checklist - Assignment 2

Use this exact order before submitting.

## A. Local setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app.cli init-db
```

## B. Load and verify the included reproducibility snapshot

```powershell
python -m app.cli seed-demo
python scripts/check_assignment.py
```

You should see PASS for all six assignment minimum checks.

## C. Open the UI

```powershell
streamlit run app/dashboard.py
```

In the dashboard, show:

1. summary counters;
2. source types;
3. a searchable scholarship list;
4. one scholarship detail page;
5. confidence score;
6. "Why this score?" breakdown;
7. source evidence;
8. change history.

## D. Demonstrate two change events

```powershell
python scripts/demo_change.py
```

Refresh the dashboard and open either HDFC or SBI Asha to show the change history.

## E. Run the real crawler

Close to normal network access, run:

```powershell
python -m app.cli crawl
```

Then refresh Streamlit. This is the actual working crawler; the demo snapshot is only a reproducible starting point.

## F. Run tests

```powershell
pytest -q
```

Expected result in this repository:

```text
5 passed
```

## G. GitHub

Create an empty GitHub repository, then from the project folder:

```powershell
git init
git add .
git commit -m "Build scholarship intelligence crawler"
git branch -M main
git remote add origin https://github.com/<USERNAME>/<REPOSITORY>.git
git push -u origin main
```

Do not commit `.env`. The local `data/atlas.db` is also ignored by default. The sample JSON is the shareable dataset.

## H. Demonstration video

A 2-4 minute recording is enough. Use this flow:

```text
Terminal -> seed demo -> assignment checks -> Streamlit dashboard
-> search -> detail -> confidence -> evidence -> change history
-> terminal -> live crawl -> refresh dashboard
```

Say what is happening at each stage using the assignment terminology:

```text
Discovery
Crawling
Extraction
Official-source verification
Confidence scoring
Storage
Update
Change detection
Stale/expired detection
```

## I. Short technical note

Submit `TECHNICAL_NOTE.md` (or convert it to PDF if requested by the recruiter). Keep it within the assignment's three-page maximum.

It covers:

- architecture;
- technology choices;
- discovery methodology;
- extraction methodology;
- verification methodology;
- confidence-score methodology;
- anti-hallucination approach;
- change detection.

## J. Final self-check against the PDF

- [x] Working crawler, not design-only
- [x] 20+ real scholarship records in demo snapshot
- [x] 15+ verified records in demo DB
- [x] 10+ records with confidence >= 95
- [x] 3+ source types
- [x] 2+ change-detection examples
- [x] 2+ expired/stale examples
- [x] Official source URL retained
- [x] Application URL retained where available
- [x] Evidence retained
- [x] Last verified retained
- [x] Change history retains old and new values
- [x] SQLite database
- [x] Searchable dashboard
- [x] Free/open-source stack
- [x] No paid scraping service
