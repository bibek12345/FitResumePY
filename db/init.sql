CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    aliases TEXT,
    logo_url TEXT
);

CREATE TABLE IF NOT EXISTS job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    location TEXT,
    url TEXT,
    raw_text TEXT,
    external_id TEXT,
    url_hash TEXT UNIQUE,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    format TEXT NOT NULL,
    text TEXT,
    text_hash TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resume_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    job_posting_id INTEGER REFERENCES job_postings(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    base_resume_hash TEXT,
    job_hash TEXT,
    input_signature TEXT,
    template_version TEXT,
    model_name TEXT,
    prompt_hash TEXT,
    token_usage TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_by TEXT,
    type TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    status TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cron_expr TEXT NOT NULL,
    is_enabled INTEGER DEFAULT 1,
    criteria_json TEXT
);
