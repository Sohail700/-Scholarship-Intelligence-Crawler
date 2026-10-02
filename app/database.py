from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import SETTINGS
from .models import EvidenceItem, ScholarshipRecord


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path or SETTINGS.db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def conn(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def init(self) -> None:
        schema = (Path(__file__).resolve().parents[1] / "schema.sql").read_text(encoding="utf-8")
        with self.conn() as con:
            con.executescript(schema)

    def get_by_key(self, key: str) -> sqlite3.Row | None:
        with self.conn() as con:
            return con.execute("SELECT * FROM scholarships WHERE canonical_key=?", (key,)).fetchone()

    def upsert(self, record: ScholarshipRecord) -> tuple[int, bool, list[dict]]:
        self.init()
        existing = self.get_by_key(record.canonical_key)
        ts = now_iso()
        verified_at = record.last_verified or ts
        changed_fields: list[dict] = []
        with self.conn() as con:
            if existing:
                scholarship_id = int(existing["id"])
                fields = [
                    "name", "provider", "source_url", "application_url", "source_type", "amount",
                    "eligibility", "academic_requirements", "education_level", "income_criteria",
                    "age_criteria", "gender_criteria", "category_criteria", "domicile_requirements",
                    "institution_requirements", "opening_date", "closing_date", "documents_required",
                    "selection_process", "renewal_requirements", "current_status", "verification_status", "confidence_score",
                    "confidence_breakdown", "last_verified", "content_hash", "updated_at"
                ]
                for field in fields:
                    old = existing[field]
                    new = record.to_dict().get(field)
                    if field == "confidence_breakdown":
                        new = json.dumps(new or {}, ensure_ascii=False)
                    if (old or "") != (new or "") and field not in {"updated_at", "last_verified", "content_hash", "confidence_score", "confidence_breakdown"}:
                        changed_fields.append({"field_name": field, "old_value": old, "new_value": new})
                con.execute(
                    """UPDATE scholarships SET
                    name=?, provider=?, source_url=?, application_url=?, source_type=?, amount=?, eligibility=?,
                    academic_requirements=?, education_level=?, income_criteria=?, age_criteria=?, gender_criteria=?,
                    category_criteria=?, domicile_requirements=?, institution_requirements=?, opening_date=?, closing_date=?,
                    documents_required=?, selection_process=?, renewal_requirements=?, current_status=?, verification_status=?, confidence_score=?,
                    confidence_breakdown=?, last_verified=?, content_hash=?, updated_at=? WHERE id=?""",
                    (
                        record.name, record.provider, record.source_url, record.application_url, record.source_type,
                        record.amount, record.eligibility, record.academic_requirements, record.education_level,
                        record.income_criteria, record.age_criteria, record.gender_criteria, record.category_criteria,
                        record.domicile_requirements, record.institution_requirements, record.opening_date,
                        record.closing_date, record.documents_required, record.selection_process,
                        record.renewal_requirements, record.current_status, record.verification_status, record.confidence_score,
                        json.dumps(record.confidence_breakdown, ensure_ascii=False), verified_at, record.content_hash, ts, scholarship_id,
                    ),
                )
            else:
                cursor = con.execute(
                    """INSERT INTO scholarships (
                    canonical_key,name,provider,source_url,application_url,source_type,amount,eligibility,
                    academic_requirements,education_level,income_criteria,age_criteria,gender_criteria,category_criteria,
                    domicile_requirements,institution_requirements,opening_date,closing_date,documents_required,
                    selection_process,renewal_requirements,current_status,verification_status,confidence_score,confidence_breakdown,
                    last_verified,content_hash,created_at,updated_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        record.canonical_key, record.name, record.provider, record.source_url, record.application_url,
                        record.source_type, record.amount, record.eligibility, record.academic_requirements,
                        record.education_level, record.income_criteria, record.age_criteria, record.gender_criteria,
                        record.category_criteria, record.domicile_requirements, record.institution_requirements,
                        record.opening_date, record.closing_date, record.documents_required, record.selection_process,
                        record.renewal_requirements, record.current_status, record.verification_status, record.confidence_score,
                        json.dumps(record.confidence_breakdown, ensure_ascii=False), verified_at, record.content_hash, ts, ts,
                    ),
                )
                scholarship_id = int(cursor.lastrowid)

            con.execute("DELETE FROM evidence WHERE scholarship_id=?", (scholarship_id,))
            for ev in record.evidence:
                con.execute(
                    "INSERT INTO evidence(scholarship_id,field_name,source_url,evidence_text,retrieved_at) VALUES(?,?,?,?,?)",
                    (scholarship_id, ev.field_name, ev.source_url, ev.evidence_text, ts),
                )
            con.execute(
                "INSERT INTO source_snapshots(scholarship_id,source_url,content_hash,crawled_at) VALUES(?,?,?,?)",
                (scholarship_id, record.source_url, record.content_hash, ts),
            )
            for change in changed_fields:
                con.execute(
                    "INSERT INTO change_events(scholarship_id,field_name,old_value,new_value,detected_at,source_url,evidence_text) VALUES(?,?,?,?,?,?,?)",
                    (
                        scholarship_id, change["field_name"], str(change["old_value"] or ""), str(change["new_value"] or ""),
                        ts, record.source_url, next((e.evidence_text for e in record.evidence if e.field_name == change["field_name"]), ""),
                    ),
                )
        return scholarship_id, bool(existing), changed_fields

    def begin_run(self) -> int:
        self.init()
        with self.conn() as con:
            cur = con.execute("INSERT INTO crawl_runs(started_at) VALUES(?)", (now_iso(),))
            return int(cur.lastrowid)

    def finish_run(self, run_id: int, *, discovered: int, stored: int, updated: int, errors: int, notes: str = "") -> None:
        with self.conn() as con:
            con.execute(
                "UPDATE crawl_runs SET finished_at=?, discovered_count=?, stored_count=?, updated_count=?, error_count=?, notes=? WHERE id=?",
                (now_iso(), discovered, stored, updated, errors, notes, run_id),
            )

    def list_scholarships(self, search: str = "") -> list[sqlite3.Row]:
        self.init()
        with self.conn() as con:
            if search:
                like = f"%{search}%"
                return list(con.execute(
                    "SELECT * FROM scholarships WHERE name LIKE ? OR provider LIKE ? OR eligibility LIKE ? ORDER BY updated_at DESC",
                    (like, like, like),
                ))
            return list(con.execute("SELECT * FROM scholarships ORDER BY updated_at DESC"))

    def get(self, scholarship_id: int) -> sqlite3.Row | None:
        self.init()
        with self.conn() as con:
            return con.execute("SELECT * FROM scholarships WHERE id=?", (scholarship_id,)).fetchone()

    def evidence(self, scholarship_id: int) -> list[sqlite3.Row]:
        self.init()
        with self.conn() as con:
            return list(con.execute("SELECT * FROM evidence WHERE scholarship_id=? ORDER BY id", (scholarship_id,)))

    def changes(self, scholarship_id: int) -> list[sqlite3.Row]:
        self.init()
        with self.conn() as con:
            return list(con.execute("SELECT * FROM change_events WHERE scholarship_id=? ORDER BY detected_at DESC", (scholarship_id,)))

    def stats(self) -> dict:
        self.init()
        with self.conn() as con:
            total = con.execute("SELECT COUNT(*) c FROM scholarships").fetchone()["c"]
            verified = con.execute("SELECT COUNT(*) c FROM scholarships WHERE verification_status='VERIFIED'").fetchone()["c"]
            review = con.execute("SELECT COUNT(*) c FROM scholarships WHERE verification_status='REVIEW_REQUIRED'").fetchone()["c"]
            active = con.execute("SELECT COUNT(*) c FROM scholarships WHERE current_status='ACTIVE'").fetchone()["c"]
            expired = con.execute("SELECT COUNT(*) c FROM scholarships WHERE current_status='EXPIRED'").fetchone()["c"]
            avg = con.execute("SELECT COALESCE(AVG(confidence_score),0) x FROM scholarships").fetchone()["x"]
            cutoff = (datetime.now(timezone.utc).timestamp() - 30 * 86400)
            recent_iso = datetime.fromtimestamp(cutoff, timezone.utc).isoformat()
            recent = con.execute("SELECT COUNT(*) c FROM scholarships WHERE updated_at>=?", (recent_iso,)).fetchone()["c"]
            source_types = list(con.execute("SELECT DISTINCT source_type FROM scholarships ORDER BY source_type"))
            return {
                "total": total,
                "verified": verified,
                "review": review,
                "active": active,
                "expired": expired,
                "average_confidence": round(float(avg), 1),
                "recently_updated": recent,
                "source_types": [row["source_type"] for row in source_types],
            }
