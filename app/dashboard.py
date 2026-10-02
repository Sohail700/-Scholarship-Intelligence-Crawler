from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Database  # noqa: E402


db = Database()
db.init()

st.set_page_config(page_title="Scholarship Intelligence", layout="wide")
st.title("Scholarship Intelligence")
st.caption("Atlas-style evidence-backed scholarship repository")

if st.button("Run live crawler"):
    with st.spinner("Crawling official sources..."):
        result = subprocess.run([sys.executable, "-m", "app.cli", "crawl"], cwd=ROOT, capture_output=True, text=True)
    if result.returncode == 0:
        st.success("Crawler finished")
        st.code(result.stdout)
    else:
        st.error("Crawler failed")
        st.code(result.stderr)
    st.rerun()

stats = db.stats()
cols = st.columns(7)
metrics = [
    ("Total discovered", stats["total"]),
    ("Verified", stats["verified"]),
    ("Review required", stats["review"]),
    ("Active", stats["active"]),
    ("Expired", stats["expired"]),
    ("Recently updated", stats["recently_updated"]),
    ("Average confidence", f'{stats["average_confidence"]}%'),
]
for col, (label, value) in zip(cols, metrics):
    col.metric(label, value)

st.divider()
query = st.text_input("Search scholarships", placeholder="name, provider, eligibility...")
rows = db.list_scholarships(query)
if not rows:
    st.info("No records found. Run `python -m app.cli seed-demo` or the live crawler.")
    st.stop()

summary = pd.DataFrame([
    {
        "Name": r["name"],
        "Provider": r["provider"],
        "Type": r["source_type"],
        "Deadline": r["closing_date"] or "Not specified",
        "Availability": r["current_status"],
        "Verification": r["verification_status"],
        "Confidence": f'{r["confidence_score"]:.1f}%',
        "Last verified": r["last_verified"],
    }
    for r in rows
])
st.dataframe(summary, use_container_width=True, hide_index=True)

st.divider()
selected_id = st.selectbox(
    "Open scholarship details",
    options=[int(r["id"]) for r in rows],
    format_func=lambda x: next(r["name"] for r in rows if int(r["id"]) == x),
)

record = db.get(selected_id)
assert record is not None
left, right = st.columns([2, 1])
with left:
    st.subheader(record["name"])
    st.write(f'**Provider:** {record["provider"]}')
    st.write(f'**Amount / Benefit:** {record["amount"]}')
    st.write(f'**Eligibility:** {record["eligibility"]}')
    st.write(f'**Academic requirements:** {record["academic_requirements"]}')
    st.write(f'**Course / level:** {record["education_level"]}')
    st.write(f'**Income criteria:** {record["income_criteria"]}')
    st.write(f'**Age criteria:** {record["age_criteria"]}')
    st.write(f'**Gender criteria:** {record["gender_criteria"]}')
    st.write(f'**Category criteria:** {record["category_criteria"]}')
    st.write(f'**Domicile:** {record["domicile_requirements"]}')
    st.write(f'**Institution requirements:** {record["institution_requirements"]}')
    st.write(f'**Opening date:** {record["opening_date"] or "Not specified"}')
    st.write(f'**Closing date:** {record["closing_date"] or "Not specified"}')
    st.write(f'**Documents:** {record["documents_required"]}')
    st.write(f'**Selection:** {record["selection_process"]}')
    st.write(f'**Renewal:** {record["renewal_requirements"]}')
with right:
    st.metric("Confidence Score", f'{record["confidence_score"]:.1f}%')
    st.write(f'**Availability:** {record["current_status"]}')
    st.write(f'**Verification:** {record["verification_status"]}')
    st.write(f'**Source type:** {record["source_type"]}')
    st.write(f'**Last verified:** {record["last_verified"]}')
    st.markdown(f'**Official source:** [{record["source_url"]}]({record["source_url"]})')
    if record["application_url"]:
        st.markdown(f'**Application:** [{record["application_url"]}]({record["application_url"]})')

st.subheader("Why this score?")
breakdown = json.loads(record["confidence_breakdown"] or "{}")
st.table(pd.DataFrame({"Signal": list(breakdown.keys()), "Points": list(breakdown.values())}))

st.subheader("Source evidence")
for ev in db.evidence(selected_id):
    st.markdown(f'**{ev["field_name"]}** - {ev["evidence_text"]}')
    st.caption(ev["source_url"])

st.subheader("Change history")
changes = db.changes(selected_id)
if changes:
    st.dataframe(pd.DataFrame([
        {
            "Field": c["field_name"],
            "Old value": c["old_value"],
            "New value": c["new_value"],
            "Detected": c["detected_at"],
            "Source": c["source_url"],
        }
        for c in changes
    ]), use_container_width=True, hide_index=True)
else:
    st.info("No change events recorded yet.")
