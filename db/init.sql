CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    aliases TEXT,
    logo_url TEXT
);

CREATE TABLE IF NOT EXISTS job_postings (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    location TEXT,
    url TEXT,
    raw_text TEXT,
    external_id TEXT,
    url_hash TEXT UNIQUE,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    format TEXT NOT NULL,
    text TEXT,
    text_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS resume_versions (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    job_posting_id INTEGER REFERENCES job_postings(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    base_resume_hash TEXT,
    job_hash TEXT,
    input_signature TEXT,
    template_version TEXT,
    model_name TEXT,
    prompt_hash TEXT,
    token_usage JSONB
);

CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    triggered_by TEXT,
    type TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    cron_expr TEXT NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    criteria_json JSONB
);
