CREATE TABLE IF NOT EXISTS scholarships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    provider TEXT,
    source_url TEXT NOT NULL,
    application_url TEXT,
    source_type TEXT NOT NULL,
    amount TEXT,
    eligibility TEXT,
    academic_requirements TEXT,
    education_level TEXT,
    income_criteria TEXT,
    age_criteria TEXT,
    gender_criteria TEXT,
    category_criteria TEXT,
    domicile_requirements TEXT,
    institution_requirements TEXT,
    opening_date TEXT,
    closing_date TEXT,
    documents_required TEXT,
    selection_process TEXT,
    renewal_requirements TEXT,
    current_status TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    confidence_breakdown TEXT NOT NULL,
    last_verified TEXT NOT NULL,
    content_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scholarship_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    evidence_text TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    FOREIGN KEY (scholarship_id) REFERENCES scholarships(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    discovered_count INTEGER DEFAULT 0,
    stored_count INTEGER DEFAULT 0,
    updated_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS source_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scholarship_id INTEGER NOT NULL,
    source_url TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    crawled_at TEXT NOT NULL,
    FOREIGN KEY (scholarship_id) REFERENCES scholarships(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS change_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scholarship_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detected_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    evidence_text TEXT,
    FOREIGN KEY (scholarship_id) REFERENCES scholarships(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scholarships_status ON scholarships(current_status);
CREATE INDEX IF NOT EXISTS idx_scholarships_score ON scholarships(confidence_score);
CREATE INDEX IF NOT EXISTS idx_scholarships_verification ON scholarships(verification_status);
CREATE INDEX IF NOT EXISTS idx_evidence_scholarship ON evidence(scholarship_id);
CREATE INDEX IF NOT EXISTS idx_changes_scholarship ON change_events(scholarship_id);
