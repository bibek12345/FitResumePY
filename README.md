# FitResume

FitResume is a local-first resume tailoring workstation that blends a NiceGUI front end with a FastAPI backend, PostgreSQL persistence, APScheduler-driven automations, and OpenAI-assisted rewriting (with a mock fallback when no API key is configured). Upload your baseline resumes, ingest job postings, tailor in a couple of clicks, and collect polished DOCX artifacts for every opportunity.

## Features

- **Unified UI**: A NiceGUI-powered interface with a dashboard, resume manager, job board, run history, scheduler, and artifact browser.
- **Resume intelligence**: Extract text from DOCX or PDF resumes, hash contents, and persist them with SQLAlchemy.
- **Job ingestion**: Add single postings or import CSV batches; jobs are tied to companies for richer context.
- **AI tailoring**: Two-step plan + render prompting through OpenAI's Responses API, or an annotated mock generator when `OPENAI_API_KEY` is absent.
- **Artifact pipeline**: Generate tailored DOCX files with `docxtpl`, store structured metadata, and download from the UI.
- **Automation ready**: APScheduler keeps recurring jobs on track; trigger schedules manually or run on cron expressions.
- **Structured logging**: `structlog` emits JSON logs for observability.
- **Testing**: Pytest coverage for the core resume → job → artifact flow (mock AI mode).

## Project Layout

```
fitresume/
  backend/
    main.py                # FastAPI + NiceGUI entrypoint
    config.py              # Environment-driven settings
    db.py                  # SQLAlchemy engine/session helpers
    models.py              # ORM models
    crud.py                # Data access helpers
    schemas.py             # Pydantic models
    services/
      app_service.py
      resume_extraction.py
      rewrite_service.py
      artifact_service.py
      scheduler_service.py
  ui/
    backend_bridge.py
    pages/
      dashboard.py
      resume_manager.py
      job_board.py
      runs.py
      scheduler.py
      artifacts.py
  db/
    init.sql               # PostgreSQL schema
  templates/
    (auto-generated resume_template.docx)
  artifacts/               # Generated resumes (gitignored, contains .gitkeep)
  uploads/                 # Uploaded resumes (created automatically)
  tests/
    test_resume_flow.py
  requirements.txt
  README.md
```

## Prerequisites

- Python 3.11+
- PostgreSQL 13+
- (Optional) OpenAI API key for real rewriting

## Setup

1. **Clone and enter the project**
   ```bash
   git clone <repo-url>
   cd FitResumePY
   ```

2. **Provision the database**
   ```bash
   createdb fitresume
   psql fitresume < db/init.sql
   ```
   > Adjust the commands if your PostgreSQL user/database names differ.

3. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional overrides)
   ```bash
   export DATABASE_URL=postgresql://localhost:5432/fitresume
   export ARTIFACTS_ROOT=./artifacts
   export OPENAI_API_KEY=sk-...  # omit to run in mock mode
   ```

5. **Run the application**
   ```bash
   uvicorn backend.main:app --reload
   ```

6. **Open the UI**
   Visit [http://localhost:8000](http://localhost:8000) for the NiceGUI dashboard.

## Usage Highlights

- **Resume Manager**: Upload DOCX/PDF files and preview the parsed text.
- **Job Board**: Create postings manually or import CSVs, pick a base resume, and tailor instantly.
- **Artifacts**: Tailored DOCX files land under `artifacts/<Company>__<JobKey>/` with accompanying `meta.json`.
- **Scheduler**: Define cron expressions (e.g., `0 8 * * *`) to automate tailoring.
- **Mock vs OpenAI**: When `OPENAI_API_KEY` is unset, the mock rewrite service produces clearly labeled `[MOCK OUTPUT]` resumes, ensuring deterministic tests and offline usability.

## Testing

Run the automated suite (uses SQLite + mock AI under the hood):

```bash
pytest
```

## Notes

- The included `db/init.sql` schema matches the SQLAlchemy models; apply it to PostgreSQL before first run.
- Generated artifacts and uploads remain on disk to support the UI download experience.
- The DOCX template is generated on demand at runtime, so no binary files need to be tracked in version control.
- APScheduler runs in-process; ensure the app remains running to execute scheduled jobs.
