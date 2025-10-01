 codex/build-fitresume-project-with-full-features-nhskwq
# FitResume

FitResume is a local-first resume tailoring workstation that keeps the project structure and behaviour outlined in the original brief while remaining fully executable inside an offline test harness.  The repository ships with lightweight, in-repo stand-ins for FastAPI, NiceGUI, SQLAlchemy, structlog, and other third-party dependencies so the end-to-end flow (resume upload → job creation → tailored DOCX artifact) can be exercised without network access or external wheels.  The public API and module layout mirror the intended production stack, which makes it straightforward to swap the stubs for the real libraries in a fully provisioned environment.

## Features

- **Unified UI blueprint**: NiceGUI page modules and a shared backend bridge illustrate the intended dashboard, resume manager, job board, runs, scheduler, and artifact screens.  The offline harness exposes them through no-op UI primitives while preserving the page contracts.
- **Resume intelligence**: DOCX resumes are parsed via a tiny ZIP/XML reader and recorded alongside hashes in a SQLite database (initialised from `db/init.sql`).
- **Job ingestion**: Create postings manually or via CSV import; jobs remain associated with companies for richer context.
- **AI tailoring**: Two-step plan + render prompting with an OpenAI-compatible interface.  Without an API key the project falls back to a deterministic mock that clearly annotates its output.
- **Artifact pipeline**: DOCX artifacts are rendered using handcrafted Office Open XML templates—no binary assets required—and accompanied by structured metadata.
- **Automation ready**: A lightweight scheduler facade mirrors the APScheduler API so manual triggers and bookkeeping continue to work inside the harness.
- **Testing**: Pytest covers the critical resume → job → tailor path using the mock rewrite service.

## Project Layout

```
fitresume/
  backend/
    main.py                # FastAPI + NiceGUI entrypoint
    config.py              # Environment-driven settings
    db.py                  # SQLite session helper that initialises db/init.sql on demand
    models.py              # Dataclasses describing persisted records
    crud.py                # Data access helpers layered on sqlite3
    schemas.py             # Lightweight dataclass-based request/response models
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
    init.sql               # SQLite-compatible schema
  templates/
    (runtime generated resume template)
  artifacts/               # Generated resumes (gitignored, contains .gitkeep)
  uploads/                 # Uploaded resumes (created automatically)
  tests/
    test_resume_flow.py
  requirements.txt
  README.md
```

## Prerequisites

- Python 3.11 or newer
- (Optional) OpenAI API key for real rewriting when running outside the test harness

## Setup

1. **Clone and enter the project**
   ```bash
   git clone <repo-url>
   cd FitResumePY
   ```

2. **(Optional) Create a virtual environment and install pytest for local test runs**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the automated tests**
   ```bash
   pytest
   ```

4. **Environment configuration**
   ```bash
   export DATABASE_URL=sqlite:///./fitresume.db   # default
   export ARTIFACTS_ROOT=./artifacts
   export OPENAI_API_KEY=sk-...                   # omit for mock mode
   ```

5. **Production deployment**

   The codebase is structured so real FastAPI, NiceGUI, SQLAlchemy, APScheduler, and docx/docxtpl dependencies can replace the bundled stubs.  Install the official packages, remove the in-repo shims, and the application can be served via `uvicorn backend.main:app --reload` as originally specified.

## Usage Highlights

- **Resume Manager**: Upload DOCX/PDF files and preview the parsed text.
- **Job Board**: Create postings manually or import CSVs, pick a base resume, and tailor instantly.
- **Artifacts**: Tailored DOCX files land under `artifacts/<Company>__<JobKey>/` with accompanying `meta.json`.
- **Scheduler**: Define cron expressions (stored in the database) and trigger them manually through the stub scheduler service.
- **Mock vs OpenAI**: When `OPENAI_API_KEY` is unset, the mock rewrite service produces clearly labeled `[MOCK OUTPUT]` resumes, ensuring deterministic tests and offline usability.

## Testing

Run the automated suite (uses SQLite + mock AI under the hood):

```bash
pytest
```

## Notes

- The included `db/init.sql` schema is SQLite-friendly for the offline harness.  Swap it for a PostgreSQL script if you integrate the real database stack.
- Generated artifacts and uploads remain on disk to support the UI download experience.
- The DOCX template is generated on demand at runtime, so no binary files need to be tracked in version control.
- The scheduler facade executes jobs immediately when triggered; replace it with APScheduler for production cron support.
=======
# FitResumePY

This project now generates its DOCX resume template at runtime. The
`ArtifactService` will automatically create `templates/resume_template.docx`
whenever it is missing, so no binary templates need to be stored in version
control.

