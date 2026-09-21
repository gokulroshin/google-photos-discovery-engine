# Implementation Plan
## AI-Powered Photo Retrieval Discovery Engine

> **Version:** 1.0
> **Stack:** Gemini LLM · Next.js (Vercel) · FastAPI (Railway) · PostgreSQL + pgvector
> **Owner:** Google Photos Core Experience Team
> **Last updated:** 2026-09-20

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Guiding Principles](#2-guiding-principles)
3. [Phase Overview & Timeline](#3-phase-overview--timeline)
4. [Phase 0 — Project Setup & Scaffolding](#4-phase-0--project-setup--scaffolding)
5. [Phase 1 — Data Model & Backend Foundation](#5-phase-1--data-model--backend-foundation)
6. [Phase 2 — Data Ingestion & Source Adapters](#6-phase-2--data-ingestion--source-adapters)
7. [Phase 3 — Gemini Classification Pipeline](#7-phase-3--gemini-classification-pipeline)
8. [Phase 4 — Taxonomy & Opportunity Engine](#8-phase-4--taxonomy--opportunity-engine)
9. [Phase 5 — Frontend Research Dashboard](#9-phase-5--frontend-research-dashboard)
10. [Phase 6 — Semantic Search & RAG](#10-phase-6--semantic-search--rag)
11. [Phase 7 — Report Generation & Export](#11-phase-7--report-generation--export)
12. [Phase 8 — Security, Auth & Compliance](#12-phase-8--security-auth--compliance)
13. [Phase 9 — Testing, Hardening & Observability](#13-phase-9--testing-hardening--observability)
14. [Phase 10 — Deployment & Handoff](#14-phase-10--deployment--handoff)
15. [Dependency Map](#15-dependency-map)
16. [Risk Register](#16-risk-register)
17. [Definition of Done](#17-definition-of-done)
18. [Open Questions](#18-open-questions)

---

## 1. Executive Summary

This plan describes the end-to-end implementation of the **AI-Powered Photo Retrieval Discovery Engine** — a production-oriented research prototype that collects publicly available user feedback, classifies it with Google Gemini, and surfaces an evidence-backed taxonomy of photo retrieval failures for a Product Manager at Google Photos.

**The system does not propose a product solution.** Its output is a reliable, traceable discovery system that enables evidence-backed decisions on where to invest next.

### Deliverables at Completion
| # | Deliverable |
|---|-------------|
| 1 | Working Vercel frontend dashboard (9 research views) |
| 2 | Railway-hosted FastAPI backend with full REST API |
| 3 | Gemini-powered classification and extraction pipeline |
| 4 | Manual import + automated source adapters |
| 5 | PostgreSQL + pgvector data model with migrations |
| 6 | Evidence explorer with full source traceability |
| 7 | Retrieval problem taxonomy with evidence counts |
| 8 | Opportunity area comparison framework |
| 9 | Research report generation and export |
| 10 | README with setup, architecture, env vars, and deployment |
| 11 | Mock data mode for testing without external APIs |
| 12 | Basic test coverage for core backend services |

---

## 2. Guiding Principles

These govern every implementation decision throughout the project:

1. **MVP first, then extend.** Build the smallest working system before adding advanced features.
2. **Evidence-first, never fabricate.** Every insight must link to a real source record. Gemini outputs are always validated.
3. **Modular by default.** Data sources, models, and analysis steps must be swappable without rewriting the core.
4. **Human-in-the-loop.** Low-confidence classifications are always flagged for researcher review, never silently accepted.
5. **Transparent over polished.** Confidence scores, evidence counts, and source diversity are always shown. Unsupported claims are never published.
6. **Secure from day one.** Secrets in env vars only. No PII in frontend. Auth on all sensitive endpoints.
7. **Fail gracefully.** The system must remain partially usable when Gemini, source APIs, or DB are unavailable.
8. **Document assumptions.** Every architectural choice is recorded with its rationale.

---

## 3. Phase Overview & Timeline

```
Week  1–2   Phase 0  — Project Setup & Scaffolding
Week  3–4   Phase 1  — Data Model & Backend Foundation
Week  5–6   Phase 2  — Data Ingestion & Source Adapters
Week  7–9   Phase 3  — Gemini Classification Pipeline
Week  10–11 Phase 4  — Taxonomy & Opportunity Engine
Week  12–14 Phase 5  — Frontend Research Dashboard
Week  15    Phase 6  — Semantic Search & RAG
Week  16    Phase 7  — Report Generation & Export
Week  17    Phase 8  — Security, Auth & Compliance
Week  18–19 Phase 9  — Testing, Hardening & Observability
Week  20    Phase 10 — Deployment & Handoff
```

> **Total estimated duration:** 20 weeks (~5 months)
> Phases 3, 5, and 9 are the most effort-intensive and overlap-adjacent phases.

---

## 4. Phase 0 — Project Setup & Scaffolding

**Goal:** A running skeleton for both frontend and backend with CI/CD, environment management, and project structure in place.

### 4.1 Repository Structure
```
photo-retrieval-discovery/
├── backend/                  # FastAPI application (Railway)
├── frontend/                 # Next.js application (Vercel)
├── .github/
│   └── workflows/
│       ├── backend-ci.yml    # pytest + coverage
│       └── frontend-ci.yml   # tsc + lint
├── docs/
│   ├── context.md
│   ├── architecture.md
│   ├── implementation_plan.md
│   └── edge_case.md
└── README.md
```

### 4.2 Backend Scaffold Tasks
- [ ] Initialise Python 3.11 project with `pyproject.toml` or `requirements.txt`
- [ ] Install core dependencies: `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `alembic`, `pydantic[email]`, `python-jose`, `structlog`, `google-generativeai`, `jinja2`, `httpx`, `pytest`, `pytest-asyncio`
- [ ] Create `backend/main.py` with FastAPI app factory pattern
- [ ] Create `backend/config.py` with Pydantic `BaseSettings` — read all env vars at startup; fail fast if required vars are missing
- [ ] Create `backend/database.py` with async SQLAlchemy engine and session factory
- [ ] Implement `GET /health` endpoint returning `{status, db, gemini, version}`
- [ ] Set up `structlog` for JSON structured logging
- [ ] Create `.env.example` with all required and optional variables documented

### 4.3 Frontend Scaffold Tasks
- [ ] Initialise Next.js 14 with TypeScript: `npx create-next-app@latest frontend --typescript --app --tailwind=false`
- [ ] Install dependencies: `@tanstack/react-query`, `zustand`, `recharts`, `radix-ui/*`, `jose`
- [ ] Create `frontend/lib/api.ts` — typed fetch wrapper with base URL, auth header injection, and error normalisation
- [ ] Create `frontend/lib/types.ts` — placeholder TypeScript interfaces matching backend Pydantic schemas
- [ ] Create `frontend/app/layout.tsx` with root providers (QueryClient, auth context)
- [ ] Create login page stub: `frontend/app/(auth)/login/page.tsx`
- [ ] Create `frontend/app/projects/page.tsx` stub (project list)

### 4.4 CI/CD Setup
- [ ] Create `.github/workflows/backend-ci.yml`:
  - Python 3.11, install deps, run `pytest tests/ --cov=. --cov-report=xml` with `MOCK_DATA_MODE=true`
- [ ] Create `.github/workflows/frontend-ci.yml`:
  - Node 20, `npm ci`, `tsc --noEmit`, `eslint .`
- [ ] Add `secrets-scanning` step to both workflows (detect-secrets or trufflehog)
- [ ] Configure Railway project (backend service + PostgreSQL plugin)
- [ ] Configure Vercel project (connect GitHub repo, set env vars)

### 4.5 Environment Variables
Set the following in Railway (backend) and Vercel (frontend) before any other phase begins:

**Railway (Backend):**
```
DATABASE_URL=postgresql+asyncpg://...   (auto-set by Railway PostgreSQL plugin)
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-1.5-pro
GEMINI_EMBEDDING_MODEL=text-embedding-004
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
ENVIRONMENT=production
LOG_LEVEL=INFO
MOCK_DATA_MODE=false
ALLOWED_ORIGINS=https://your-app.vercel.app
```

**Vercel (Frontend):**
```
NEXT_PUBLIC_API_URL=https://api.your-project.railway.app/v1
NEXTAUTH_SECRET=...
```

### 4.6 Phase 0 Acceptance Criteria
- [ ] `GET /health` returns `200 OK` with `{status: "ok"}` from Railway
- [ ] Next.js app deploys to Vercel and loads the login page
- [ ] Both CI pipelines pass on an empty test suite
- [ ] `.env.example` is committed; no real secrets in the repository

---

## 5. Phase 1 — Data Model & Backend Foundation

**Goal:** The complete PostgreSQL schema is in place with Alembic migrations, all ORM models are defined, and the core CRUD endpoints for projects are working.

### 5.1 Alembic Setup
- [ ] Initialise Alembic: `alembic init migrations`
- [ ] Configure `alembic/env.py` to use `DATABASE_URL` from env and import all ORM models
- [ ] Install `pgvector` PostgreSQL extension on Railway (run `CREATE EXTENSION IF NOT EXISTS vector;` in initial migration)

### 5.2 ORM Models
Implement the following SQLAlchemy models, each in its own file under `backend/models/`:

#### `backend/models/project.py`
```python
# Fields: id (UUID PK), name, description, research_questions (JSONB),
#         status (draft|active|archived), created_at, updated_at
```

#### `backend/models/source_record.py`
```python
# Fields: id, project_id (FK), source_platform, source_url, source_date,
#         raw_content, author_handle, collection_method, collection_date,
#         ingestion_job_id (FK), is_duplicate, dedup_hash, metadata (JSONB),
#         language, deleted_at, created_at
```

#### `backend/models/ingestion_job.py`
```python
# Fields: id, project_id (FK), source_type, status, config (JSONB),
#         records_found, records_stored, last_heartbeat_at,
#         error_details (JSONB), started_at, completed_at
```

#### `backend/models/model_run.py`
```python
# Fields: id, project_id (FK), model_name, prompt_version,
#         parameters (JSONB), status, records_total, records_success,
#         records_failed, error_log (JSONB), started_at, completed_at
```

#### `backend/models/evidence_record.py`
```python
# Fields: id, source_record_id (FK), model_run_id (FK), is_relevant,
#         relevance_labels (ARRAY), retrieval_scenario, memory_cues (JSONB),
#         missing_information, search_behavior, retrieval_outcome,
#         failure_points (ARRAY), user_segment, evidence_excerpt,
#         confidence_score (FLOAT), rationale, needs_human_review,
#         is_genuine_experience, embedding (vector(768)), created_at, updated_at
```

#### `backend/models/taxonomy_category.py`
```python
# Fields: id, project_id (FK), version (INT), name, definition,
#         user_segment, common_memory_cues (JSONB), missing_information,
#         common_search_behavior, failure_mechanism, evidence_count,
#         source_diversity (JSONB), representative_excerpts (ARRAY),
#         confidence_level, open_questions (ARRAY), product_implications,
#         created_at, updated_at
```

#### `backend/models/opportunity_area.py`
```python
# Fields: id, project_id (FK), name, description,
#         evidence_frequency, evidence_diversity (JSONB),
#         unique_author_count, user_impact_score, abandonment_rate,
#         workaround_exists, strategic_relevance, problem_clarity,
#         potential_reach, validation_effort, scoring_methodology,
#         analyst_notes, status (draft|validated|rejected), created_at
```

#### `backend/models/human_review.py`
```python
# Fields: id, evidence_record_id (FK), reviewer_id,
#         action (approved|corrected|rejected), corrections (JSONB),
#         reviewer_notes, reviewed_at
```

### 5.3 Pydantic Schemas
Create `backend/schemas/` — one file per entity with `Create`, `Update`, and `Response` schemas.

### 5.4 Migrations
- [ ] Write initial Alembic migration creating all tables
- [ ] Add IVFFlat index on `evidence_records.embedding` column
- [ ] Add unique constraint on `(project_id, dedup_hash)` in `source_records`
- [ ] Test migration: `alembic upgrade head` on a clean local database

### 5.5 Projects API
- [ ] `POST /v1/projects` — create project, validate name uniqueness
- [ ] `GET /v1/projects` — list projects with pagination
- [ ] `GET /v1/projects/{id}` — get project with aggregate stats (record count, evidence count, job status)
- [ ] `PATCH /v1/projects/{id}` — update name, description, research_questions, status
- [ ] `DELETE /v1/projects/{id}` — soft-delete with cascade (block if active jobs exist)

### 5.6 Auth Stub
- [ ] Create `backend/auth/` with JWT encode/decode using `python-jose`
- [ ] `POST /v1/auth/login` — username + password → JWT token (hardcoded admin user is acceptable for MVP)
- [ ] `GET /v1/auth/me` — return current user from JWT
- [ ] Create `get_current_user` FastAPI dependency used on all protected endpoints

### 5.7 Phase 1 Acceptance Criteria
- [ ] `alembic upgrade head` runs cleanly on Railway PostgreSQL
- [ ] All 5 project CRUD endpoints return correct responses
- [ ] Auth endpoints issue and validate JWT tokens
- [ ] All tables visible in Railway DB console
- [ ] CI pipeline passes

---

## 6. Phase 2 — Data Ingestion & Source Adapters

**Goal:** Researchers can import data (manually or via adapters), have it normalised and deduplicated, and view source records through the API.

### 6.1 Source Adapter Base Class
```
backend/adapters/base.py
```
- [ ] Define `SourceAdapter` abstract base class with `fetch(config)`, `normalize(raw)`, and `compute_dedup_hash(content)` methods
- [ ] Define `RawRecord` dataclass: `{content, url, date, author, platform, metadata}`
- [ ] Register all adapters in `backend/adapters/__init__.py` as a `ADAPTER_REGISTRY` dict

### 6.2 Manual Import Adapter (MVP — implement first)
```
backend/adapters/manual_import.py
```
- [ ] Accept CSV or JSON file upload via `POST /v1/projects/{id}/import`
- [ ] Required CSV columns: `raw_content`, `source_url`, `source_date`, `source_platform`
- [ ] Optional columns: `author_handle`, `metadata`
- [ ] Validate schema before processing (reject entire file on missing required columns; return column-level errors)
- [ ] Process in batches of 500 rows
- [ ] Compute dedup hash per record; skip duplicates; log skip count
- [ ] Return `{records_accepted, records_skipped_duplicate, records_failed, validation_errors[]}`
- [ ] Enforce 100MB file size limit

### 6.3 Ingestion Job System
```
backend/workers/ingestion_worker.py
```
- [ ] `POST /v1/projects/{id}/jobs` — create `IngestionJob` record and enqueue background task
- [ ] Worker updates `status`, `records_found`, `records_stored`, `last_heartbeat_at` after each batch
- [ ] Implement watchdog: mark jobs as `failed` if `last_heartbeat_at` is stale > 2 minutes
- [ ] `GET /v1/projects/{id}/jobs` — list jobs with status, progress, timestamps
- [ ] `GET /v1/projects/{id}/jobs/{job_id}` — detailed status with error log
- [ ] `DELETE /v1/projects/{id}/jobs/{job_id}` — cancel a running job (set `status=cancelled`)
- [ ] Enforce maximum 3 concurrent jobs per project

### 6.4 Source Records API
- [ ] `GET /v1/projects/{id}/records` — list with pagination and filters: `platform`, `source_date_from`, `source_date_to`, `is_duplicate`, `language`
- [ ] Response includes `total_before_filters` and `applied_filters`
- [ ] `GET /v1/projects/{id}/records/{record_id}` — full record including `raw_content` and `metadata`
- [ ] `DELETE /v1/projects/{id}/records/{record_id}` — soft-delete (sets `deleted_at`)

### 6.5 Preprocessing Pipeline
```
backend/services/preprocessing_service.py
```
- [ ] Strip HTML tags and decode HTML entities from `raw_content`
- [ ] Normalise whitespace (collapse multiple spaces/newlines)
- [ ] Detect language using `langdetect` and store in `metadata.language`
- [ ] Truncate content exceeding 8,000 tokens (store `metadata.is_truncated=true`)
- [ ] Validate `source_date` range (flag dates before 2015 or in the future)

### 6.6 Live Source Adapters (Phase 2 — implement after manual import is stable)
Implement each adapter with stubbed `fetch()` first; real API integration in Phase 2b:

```
backend/adapters/play_store.py     # google-play-scraper
backend/adapters/app_store.py      # iTunes RSS + requests
backend/adapters/reddit.py         # PRAW API
backend/adapters/youtube.py        # YouTube Data API v3
backend/adapters/forum.py          # requests + BeautifulSoup
```

Each adapter must:
- [ ] Implement `fetch(config: dict) -> list[RawRecord]`
- [ ] Handle 429 rate limits with exponential backoff (1s, 2s, 4s, 8s, max 60s)
- [ ] Handle 4xx/5xx per-URL failures gracefully (log, skip, continue)
- [ ] Respect robots.txt and document platform ToS status
- [ ] Return results normalised to `RawRecord` schema

### 6.7 Phase 2 Acceptance Criteria
- [ ] Researcher can upload a CSV with 1,000 records; system ingests, deduplicates, and stores them
- [ ] Duplicate records are correctly identified and skipped (not double-counted)
- [ ] Ingestion job status updates are visible via `GET /jobs/{id}`
- [ ] Non-English records have `metadata.language` set
- [ ] Manual import correctly rejects files with missing required columns

---

## 7. Phase 3 — Gemini Classification Pipeline

**Goal:** Every relevant source record is classified and structured-data-extracted via Gemini. Results are stored in `evidence_records` and flagged for human review where confidence is low.

### 7.1 Gemini Client
```
backend/gemini/client.py
```
- [ ] Initialise `google-generativeai` SDK with `GEMINI_API_KEY` from env
- [ ] Implement `call_gemini(prompt: str, schema: type[BaseModel]) -> BaseModel` with:
  - `response_mime_type="application/json"` for structured output
  - Retry logic: 3 attempts with exponential backoff on 429/503
  - Timeout: 30 seconds per call
  - On persistent failure: raise `GeminiUnavailableError`
- [ ] Log every call: model name, prompt version, token usage, latency, success/fail
- [ ] Filter all sensitive headers from logs (`Authorization`, `*_KEY`, `*_SECRET`)

### 7.2 Prompt Templates
```
backend/gemini/prompts/
├── relevance_filter.j2
├── extraction.j2
├── taxonomy_cluster.j2
├── opportunity_score.j2
├── query_generation.j2
└── summary_synthesis.j2
```

**`relevance_filter.j2`** — determines if a source record is about incomplete-memory photo retrieval:
```
You are a research assistant analysing user feedback about Google Photos.

Your task is to determine whether the following source text describes a REAL USER
experiencing difficulty retrieving a photo because they cannot accurately describe
the photo's date, location, album, filename, or searchable metadata.

Scope:
- IN SCOPE: retrieval failures caused by incomplete, uncertain, contextual, episodic,
  or visually-based memory.
- OUT OF SCOPE: general app crashes, storage issues, billing, unrelated complaints,
  feature requests with no retrieval failure context, satirical or fictional posts.

<source_text>
{{ raw_content }}
</source_text>

Respond ONLY with valid JSON matching this schema:
{
  "is_relevant": boolean,
  "confidence": float (0.0-1.0),
  "rationale": string,
  "is_genuine_experience": boolean,
  "tone_flags": string[] (e.g. ["sarcasm", "hypothetical", "fictional"])
}
```

**`extraction.j2`** — extracts all 12 structured fields from a relevant record:
```
You are a research assistant extracting structured data from user feedback
about Google Photos photo retrieval.

RULES:
- Extract ONLY what is explicitly stated in the source text.
- Do NOT infer, hypothesise, or fill in gaps.
- Do NOT fabricate quotes. evidence_excerpt must be a verbatim substring of the source text.
- If a field cannot be determined from the source text, set it to null.
- Assign failure_points only if they are directly evidenced in the text.

<source_text>
{{ raw_content }}
</source_text>

Respond ONLY with valid JSON matching the EvidenceExtraction schema.
```

### 7.3 Pydantic Output Schemas
```
backend/gemini/schemas.py
```
- [ ] `RelevanceFilterOutput`: `is_relevant`, `confidence`, `rationale`, `is_genuine_experience`, `tone_flags`
- [ ] `MemoryCues`: 10 optional string fields (person, place, time, event, object, visual, text, emotion, purpose, source)
- [ ] `RetrievalOutcome` enum: 7 values
- [ ] `EvidenceExtraction`: all 12 extraction fields with types and constraints
- [ ] Post-extraction validation hook: verify `evidence_excerpt` is a substring of `raw_content`

### 7.4 Analysis Worker
```
backend/workers/analysis_worker.py
```
- [ ] `POST /v1/projects/{id}/analyze` — start analysis job (reject if one already running)
- [ ] Worker queries `source_records` where no matching `evidence_records.source_record_id` exists and `deleted_at IS NULL`
- [ ] For each unprocessed record:
  1. Run `relevance_filter.j2` → store `is_relevant`, `confidence`, `tone_flags`
  2. If `is_relevant=True` AND `confidence >= 0.7`: run `extraction.j2` → store `EvidenceRecord`
  3. If `confidence < 0.7` OR validation fails: flag `needs_human_review=True`
  4. Validate `evidence_excerpt` against `raw_content` (substring check)
  5. Generate and store embedding (see Phase 6)
- [ ] Commit after every 50 records (checkpoint pattern)
- [ ] Update `model_run.records_success`, `records_failed` per record
- [ ] On `GeminiUnavailableError`: pause job, set `status=paused`, allow manual resume
- [ ] Skip already-classified records (idempotent re-runs)

### 7.5 Evidence Records API
- [ ] `GET /v1/projects/{id}/evidence` — list with pagination and filters:
  - `scenario`, `outcome`, `confidence_min`, `confidence_max`, `label`, `needs_review`, `failure_point`
  - Response includes `total_before_filters`, `applied_filters`
- [ ] `GET /v1/projects/{id}/evidence/{ev_id}` — full record with `raw_content`, Gemini rationale, model version, all extracted fields
- [ ] Mock data mode: if `MOCK_DATA_MODE=true`, return fixture data from `backend/tests/fixtures/evidence.json`

### 7.6 Phase 3 Acceptance Criteria
- [ ] 100-record test dataset classified end-to-end with no crashes
- [ ] `evidence_excerpt` is always a verbatim substring of `raw_content` (or null)
- [ ] Confidence scores are always between 0.0 and 1.0
- [ ] Records with confidence < 0.7 appear in human review queue
- [ ] Analysis job is idempotent (re-running does not create duplicate records)
- [ ] Gemini API outage causes job to pause, not crash, and allows resume

---

## 8. Phase 4 — Taxonomy & Opportunity Engine

**Goal:** Classified evidence is clustered into a retrieval problem taxonomy. Opportunity areas are scored on 9 dimensions and can be compared side-by-side.

### 8.1 Taxonomy Service
```
backend/services/taxonomy_service.py
```
- [ ] `POST /v1/projects/{id}/taxonomy/generate` — triggers taxonomy generation job
- [ ] Step 1 — Semantic clustering:
  - Query all `evidence_records` with `embedding IS NOT NULL` and `is_relevant=True` and `needs_human_review=False`
  - Use pgvector cosine similarity to group records (IVFFlat k-means clustering with k=5-15, configurable)
  - Fallback: if embeddings unavailable, cluster by `failure_points[]` + `retrieval_scenario` using keyword overlap
- [ ] Step 2 — Gemini category definition:
  - For each cluster, run `taxonomy_cluster.j2` with a sample of 10 representative records
  - Extract: name, definition, user_segment, memory_cues, missing_information, failure_mechanism, open_questions, product_implications
- [ ] Step 3 — Post-clustering validation:
  - Enforce minimum 3 and maximum 15 categories
  - Flag categories with `evidence_count < 3` as `confidence_level=low`
  - Compute pairwise cosine similarity between category definitions; flag pairs > 0.85 as potential duplicates
  - Count `unique_author_count` per category (deduplicated by anonymised `author_handle`)
- [ ] Taxonomy versioning: each generation creates a new version (timestamp). Old versions preserved.
- [ ] Mark stale opportunity scores when taxonomy version changes

### 8.2 Taxonomy API
- [ ] `GET /v1/projects/{id}/taxonomy` — list all categories for latest version with evidence counts
- [ ] `GET /v1/projects/{id}/taxonomy/{cat_id}` — full category with representative excerpts, open questions, evidence list
- [ ] `PATCH /v1/projects/{id}/taxonomy/{cat_id}` — researcher updates definition, merges categories, renames

### 8.3 Opportunity Area Service
```
backend/services/opportunity_service.py
```
- [ ] `POST /v1/projects/{id}/opportunities` — trigger opportunity area generation from taxonomy
- [ ] For each taxonomy category, run `opportunity_score.j2` to generate an `OpportunityArea` record
- [ ] Score each area on 9 dimensions:
  | Dimension | Source |
  |-----------|--------|
  | `evidence_frequency` | `evidence_count` from taxonomy |
  | `evidence_diversity` | `source_diversity` breakdown |
  | `user_impact_score` | Gemini estimation (0-10) |
  | `abandonment_rate` | % of records with `outcome=abandoned` |
  | `workaround_exists` | Boolean from evidence patterns |
  | `strategic_relevance` | Gemini estimation (0-10) |
  | `problem_clarity` | Gemini estimation (0-10) |
  | `potential_reach` | Gemini estimation (text + score) |
  | `validation_effort` | low / medium / high |
- [ ] Store `scoring_methodology` explaining how each score was derived
- [ ] Validate: opportunity areas with `evidence_frequency=0` → `status=speculative`
- [ ] Require `analyst_notes` for any manual score override (`PATCH` endpoint validation)

### 8.4 Opportunity API
- [ ] `GET /v1/projects/{id}/opportunities` — list with all scores for all dimensions
- [ ] `GET /v1/projects/{id}/opportunities/{op_id}` — detail with linked taxonomy category, evidence records, scoring rationale
- [ ] `PATCH /v1/projects/{id}/opportunities/{op_id}` — update `analyst_notes`, manual score adjustments (logged)

### 8.5 Phase 4 Acceptance Criteria
- [ ] Taxonomy generates 3–15 categories from a 100+ record evidence set
- [ ] Each category has `evidence_count`, `unique_author_count`, `source_diversity`, `representative_excerpts`
- [ ] Categories with `evidence_count < 3` are correctly labelled as low confidence
- [ ] Opportunity areas have all 9 dimensions scored with visible methodology
- [ ] Manual score overrides require `analyst_notes` and are logged

---

## 9. Phase 5 — Frontend Research Dashboard

**Goal:** A complete, professional research dashboard with all 9 required views, built in Next.js.

### 9.1 Design System & Shared Components
```
frontend/components/ui/
```
- [ ] `Button`, `Badge`, `Tooltip`, `Modal`, `Table`, `Pagination`, `Spinner`, `EmptyState`
- [ ] `ConfidenceBadge` — displays score with colour coding (red <0.5, amber 0.5-0.7, green >0.7)
- [ ] `SourceBadge` — platform icon + name (Reddit, Play Store, App Store, etc.)
- [ ] `OutcomeBadge` — colour-coded retrieval outcome
- [ ] `Alert` component for `is_partial_dataset`, `pending_review`, `stale_taxonomy` warnings

### 9.2 View 1: Overview Dashboard
```
frontend/app/projects/[id]/page.tsx
```
- [ ] Summary cards: Total Records, Relevant Records, Sources, Processing Status, Problem Categories
- [ ] Source diversity bar chart (records per platform)
- [ ] Confidence score histogram (distribution across evidence records)
- [ ] Human review queue depth with "Go to review" CTA
- [ ] Recent job activity (last 5 jobs with status)
- [ ] Active warnings banner: partial dataset, pending reviews, stale taxonomy
- [ ] Empty state: guided CTA to start first ingestion job

### 9.3 View 2: Data Explorer
```
frontend/app/projects/[id]/explorer/page.tsx
```
- [ ] Server-paginated table of source records (50 per page)
- [ ] Filter sidebar: platform, date range, language, is_duplicate
- [ ] Filter state persisted in URL query string
- [ ] Column: platform badge, date, content preview (100 chars), relevance status, confidence
- [ ] Click-through to Evidence Viewer for each record
- [ ] "Clear all filters" button with count of active filters

### 9.4 View 3: Evidence Viewer
```
frontend/app/projects/[id]/evidence/page.tsx
```
- [ ] Paginated evidence card grid (50 per page)
- [ ] Filter by: scenario, outcome, confidence range, failure point, label, `needs_review`
- [ ] Each card shows: evidence excerpt (truncated, expandable), confidence badge, scenario, outcome, failure points
- [ ] Click-through to full evidence detail modal/page:
  - Full original `raw_content` with excerpt highlighted
  - All 12 extracted fields displayed
  - Gemini rationale
  - Model version and prompt version used
  - Source metadata (platform, URL, date)
  - Human review history

### 9.5 View 4: Problem Taxonomy
```
frontend/app/projects/[id]/taxonomy/page.tsx
```
- [ ] Grid of taxonomy category cards
- [ ] Each card: name, definition summary, evidence count, unique author count, source diversity pills, confidence level badge
- [ ] Click-through to category detail:
  - Full definition
  - Memory cues and failure mechanism
  - Representative excerpts (3-5)
  - Open questions list
  - Product implications text
  - Evidence list (linked to Evidence Viewer)
  - "Merge with another category" action (admin only)
- [ ] Warning banner if categories with potential duplicates exist (cosine similarity > 0.85)
- [ ] Version selector if multiple taxonomy versions exist

### 9.6 View 5: Opportunity Comparison
```
frontend/app/projects/[id]/opportunities/page.tsx
```
- [ ] Side-by-side comparison matrix: rows = dimensions, columns = opportunity areas
- [ ] Colour-coded score cells (heat map)
- [ ] Sticky column headers (opportunity area names)
- [ ] "Show/hide dimensions" control
- [ ] Click any score cell → detail modal showing methodology and evidence sources
- [ ] Horizontal scroll for > 6 opportunity areas
- [ ] Speculative opportunities (zero evidence) shown in separate section with clear label
- [ ] Export comparison as CSV

### 9.7 View 6: Search & Semantic Discovery
```
frontend/app/projects/[id]/search/page.tsx
```
- [ ] Search input with debounce (300ms)
- [ ] Semantic search via `GET /evidence/search?q=...`
- [ ] Results ranked by cosine similarity score (shown alongside each result)
- [ ] Warning for queries < 5 words
- [ ] Zero-result state shows top-3 nearest records with "Low Confidence Matches" label
- [ ] Keyword search fallback when embeddings unavailable (full-text search on `raw_content`)

### 9.8 View 7: Research Report
```
frontend/app/projects/[id]/report/page.tsx
```
- [ ] "Generate Report" button — triggers `POST /reports` job
- [ ] Progress indicator while report is generating
- [ ] Rendered Markdown report with section navigation
- [ ] Warning banner if generated on partial data (`is_partial_dataset=true`)
- [ ] Warning banner if pending reviews exist at time of generation
- [ ] Export as Markdown file (client-side download)
- [ ] Export as JSON (structured data with evidence citations)

### 9.9 View 8: Human Review Queue
```
frontend/app/projects/[id]/review/page.tsx
```
- [ ] Queue list: records sorted by confidence (lowest first)
- [ ] Each item shows: evidence excerpt, current AI classification, confidence score, rationale
- [ ] Reviewer actions: Approve / Correct / Reject
- [ ] "Correct" action: inline form to edit any of the 12 extracted fields
- [ ] Bulk approve: select multiple records with checkbox → "Approve selected" (requires confirmation)
- [ ] Bulk action progress indicator ("Approving 200/1000...")
- [ ] Conflict badge: records with disagreeing reviewer decisions shown with escalation CTA

### 9.10 View 9: Job Monitoring
```
frontend/app/projects/[id]/jobs/page.tsx
```
- [ ] Live-updating job list (polls every 5s via `refetchInterval`)
- [ ] Each job: type, status badge, progress bar, records_found/stored, start time, duration
- [ ] Error log expandable section for failed jobs
- [ ] "Cancel" button for running jobs (with confirmation dialog)
- [ ] "Resume" button for paused jobs
- [ ] Completed jobs transition to done state within 5s of completion

### 9.11 Phase 5 Acceptance Criteria
- [ ] All 9 views load without errors on a project with mock data
- [ ] Filter state persists in URL and survives browser refresh
- [ ] All tables are server-paginated (no client-side loading of all records)
- [ ] Empty states are present on every view
- [ ] Job monitor updates within 5 seconds of job status change
- [ ] No PII rendered directly in any view (all `author_handle` values are anonymised)

---

## 10. Phase 6 — Semantic Search & RAG

**Goal:** Evidence records are embedded, stored in pgvector, and searchable by semantic similarity.

### 10.1 Embedding Generation
```
backend/gemini/client.py (extend)
```
- [ ] Add `generate_embedding(text: str) -> list[float]` method using `GEMINI_EMBEDDING_MODEL`
- [ ] Return a 768-dimension float vector
- [ ] Handle embedding API failures gracefully: store `embedding=NULL`, set `embedding_stale=True` flag
- [ ] Store `embedding_model_version` alongside each embedding

### 10.2 Embedding Integration in Analysis Worker
- [ ] After successful `EvidenceExtraction`, call `generate_embedding(evidence_excerpt or raw_content)`
- [ ] Store embedding in `evidence_records.embedding` (pgvector `vector(768)` column)
- [ ] Decouple embedding from classification: classification can succeed even if embedding fails

### 10.3 Re-Embedding Job
- [ ] `POST /v1/projects/{id}/jobs` with `source_type=reembed` — re-embeds all records where `embedding IS NULL` or `embedding_stale=True`
- [ ] Required when embedding model changes (detect via `embedding_model_version` mismatch)

### 10.4 Semantic Search Endpoint
```
backend/routers/evidence.py (extend)
```
- [ ] `GET /v1/projects/{id}/evidence/search?q={query}&limit=20&min_similarity=0.65`
- [ ] Generate embedding for query using same model
- [ ] Query pgvector: `SELECT * FROM evidence_records ORDER BY embedding <=> query_embedding LIMIT 20`
- [ ] Filter: `WHERE embedding IS NOT NULL AND is_relevant=True AND deleted_at IS NULL`
- [ ] Return results with `similarity_score` field
- [ ] Zero results → return top-3 nearest regardless of threshold with `low_confidence=true` flag
- [ ] Fallback: if embeddings unavailable, return keyword search results from `raw_content` full-text index

### 10.5 Phase 6 Acceptance Criteria
- [ ] Semantic search returns relevant evidence for natural-language queries
- [ ] Records with `embedding=NULL` are excluded from semantic search but visible in explorer
- [ ] Embedding failure does not block classification storage
- [ ] Re-embedding job runs cleanly on records with stale or null embeddings

---

## 11. Phase 7 — Report Generation & Export

**Goal:** Researchers can generate a structured Markdown research report grounded in evidence, and export all data as CSV/JSON.

### 11.1 Report Service
```
backend/services/report_service.py
```
- [ ] Require minimum 10 relevant evidence records before allowing report generation
- [ ] Block report generation if an analysis job is still running (return `409 Conflict`)
- [ ] Gather context: taxonomy categories, opportunity areas, top evidence records per category, source diversity stats
- [ ] Run `summary_synthesis.j2` prompt with gathered context
- [ ] Post-generation validation: every claim in report must cite a `source_record_id` that exists in the project
- [ ] Uncited claims flagged with `[UNSUPPORTED — VERIFY]` in report output
- [ ] Report metadata: timestamp, model version, prompt version, evidence count, pending review count
- [ ] Add warning banner text if `is_partial_dataset=True` or pending reviews > 0

### 11.2 Report API
- [ ] `POST /v1/projects/{id}/reports` — trigger report generation (async job; reject duplicate requests)
- [ ] `GET /v1/projects/{id}/reports` — list reports with status, creation time, evidence count
- [ ] `GET /v1/projects/{id}/reports/{rpt_id}` — return report as Markdown or JSON (via `Accept` header)
- [ ] Reports are append-only; no deletion (research audit trail)

### 11.3 Export Endpoints
- [ ] `GET /v1/projects/{id}/export/evidence?format=csv|json`
  - CSV: `csv.QUOTE_ALL` quoting, BOM header for Excel, `author_handle` anonymised
  - JSON: structured array with all evidence fields
  - Files > 50MB: async generation → pre-signed download URL (expires 24h)
- [ ] `GET /v1/projects/{id}/export/taxonomy?format=csv|json`
  - Includes all category fields + evidence counts + representative excerpts

### 11.4 Phase 7 Acceptance Criteria
- [ ] Report generated on 100+ evidence records in < 60 seconds
- [ ] Every cited `source_record_id` in the report exists in the database
- [ ] CSV export with commas, newlines, and quotes in content parses correctly in Excel
- [ ] Report generation blocked when analysis job is running
- [ ] Report includes warning banner when generated on partial data

---

## 12. Phase 8 — Security, Auth & Compliance

**Goal:** The system is secure by default with proper authentication, PII handling, and no secrets in code or frontend.

### 12.1 Authentication & Authorization
- [ ] Role-based access: `admin` (full access) and `researcher` (read + review)
- [ ] `require_role("admin")` FastAPI dependency on: project delete, bulk delete, taxonomy merge, schema changes
- [ ] `require_role("researcher")` FastAPI dependency on: all read + review endpoints
- [ ] Rate limit `POST /auth/login`: 10 attempts per IP per 15 minutes; log all failed attempts
- [ ] JWT expiry: 8 hours; include `role` and `user_id` claims
- [ ] Frontend: detect `401` responses → redirect to login with toast; preserve current URL for post-login redirect

### 12.2 PII Handling
- [ ] `author_handle` values are stored as SHA-256-based pseudonyms (`user_a3f2c`) at ingest time
- [ ] Original handles are never stored in the primary tables (stored only in `metadata.original_handle`, access-controlled)
- [ ] PII detection on `evidence_excerpt` before storage: flag emails, phone numbers, full names
- [ ] Detected PII replaced with `[REDACTED]` in UI rendering (not in DB)
- [ ] All CSV/JSON exports use pseudonymised `author_handle`

### 12.3 Secret Management
- [ ] All secrets in Railway env vars; no hardcoded values anywhere
- [ ] `detect-secrets` CI scan on every commit (fail build on new secrets detected)
- [ ] `backend/gemini/client.py` explicitly filters `Authorization` header from all logs
- [ ] Startup validation: fail if `ENVIRONMENT=production` and `MOCK_DATA_MODE=true`
- [ ] Startup validation: fail if `ALLOWED_ORIGINS=*` and `ENVIRONMENT=production`

### 12.4 CORS & Transport Security
- [ ] CORS: only `ALLOWED_ORIGINS` env var values accepted (no wildcard in production)
- [ ] All traffic over HTTPS (enforced by Vercel + Railway)
- [ ] `Strict-Transport-Security` header on all API responses

### 12.5 Source Terms of Service
- [ ] Document ToS status for each adapter in `backend/adapters/{platform}.py` as a class docstring
- [ ] Adapters with `tos_status=restricted` disabled by default; require `ENABLE_RESTRICTED_SOURCES=true` env flag (admin only)
- [ ] Robots.txt check before each crawl session in forum adapter

### 12.6 Phase 8 Acceptance Criteria
- [ ] A `researcher` role user cannot call any `admin`-only endpoint
- [ ] `GEMINI_API_KEY` does not appear in any log output
- [ ] All `author_handle` values in exports are pseudonymised
- [ ] CI pipeline fails if a secret pattern is detected in committed code
- [ ] App refuses to start if required env vars are missing

---

## 13. Phase 9 — Testing, Hardening & Observability

**Goal:** Core functionality is covered by automated tests; the system handles edge cases gracefully; observability is in place.

### 13.1 Backend Test Coverage

#### Unit Tests
- [ ] `test_gemini_schemas.py` — Pydantic schema validation for all Gemini output shapes including invalid, partial, and out-of-range values
- [ ] `test_preprocessing.py` — HTML stripping, language detection, truncation, date validation
- [ ] `test_adapters.py` — normalization and deduplication logic for each adapter (mocked HTTP)
- [ ] `test_dedup.py` — hash collision handling, near-duplicate detection, cross-project scoping
- [ ] `test_excerpt_validation.py` — substring check for `evidence_excerpt` against `raw_content`

#### Integration Tests (FastAPI TestClient)
- [ ] `test_projects_api.py` — full CRUD lifecycle
- [ ] `test_ingestion_api.py` — file upload, schema validation, dedup, job status updates
- [ ] `test_evidence_api.py` — classification, filtering, pagination, search
- [ ] `test_review_api.py` — approve, correct, reject, conflict detection
- [ ] `test_auth_api.py` — login, expired token, role enforcement, rate limiting

#### Edge Case Tests (from edge_case.md)
- [ ] Gemini returns empty JSON → record flagged for human review, job continues
- [ ] Gemini API 503 → retry 3 times → job paused (not crashed)
- [ ] `evidence_excerpt` not a substring of `raw_content` → field set to null, flagged
- [ ] CSV with missing required column → rejected with column-level errors
- [ ] Analysis job re-run → already-classified records skipped (idempotency)
- [ ] DB connection pool exhaustion → graceful 503 (not unhandled exception)
- [ ] Report generation blocked when analysis job running

### 13.2 Frontend Tests
- [ ] `tsc --noEmit` passes with zero type errors
- [ ] ESLint passes with zero warnings
- [ ] React Testing Library: render test for every view page component
- [ ] MSW: mock API responses for all 9 dashboard views
- [ ] Empty state rendering test for all 9 views

### 13.3 Mock Data Mode
- [ ] `backend/tests/fixtures/` contains:
  - `projects.json` — 2 sample projects
  - `source_records.json` — 200 sample records (mixed platforms, languages, dates)
  - `evidence.json` — 150 classified evidence records (varied confidence, outcomes, failure points)
  - `taxonomy.json` — 7 taxonomy categories with evidence links
  - `opportunities.json` — 5 opportunity areas with scores
  - `report.md` — sample generated report
- [ ] When `MOCK_DATA_MODE=true`: all service methods return fixture data; no DB or Gemini calls
- [ ] Frontend works identically in mock mode vs. live mode

### 13.4 Observability
- [ ] `GET /health` returns `{status, db_status, gemini_status, version, uptime}`
- [ ] `GET /v1/projects/{id}/storage` returns storage breakdown: source records size, evidence size, export files size
- [ ] structlog JSON logs include: `timestamp`, `level`, `service`, `request_id`, `user_id`, `duration_ms` on every request
- [ ] All Gemini calls logged with: `model`, `prompt_version`, `tokens_in`, `tokens_out`, `latency_ms`, `success`
- [ ] Job heartbeat mechanism: workers update `last_heartbeat_at` every 30s; watchdog marks stale jobs as failed

### 13.5 Performance Baselines
- [ ] `GET /evidence` with 50 results: < 200ms p95
- [ ] Semantic search: < 500ms p95 on 10,000 embedded records
- [ ] Dashboard Overview page load: < 2s p95 (all aggregate queries)
- [ ] Taxonomy generation: < 5 minutes for 1,000 evidence records

### 13.6 Phase 9 Acceptance Criteria
- [ ] Backend test coverage ≥ 70% on core services
- [ ] All critical edge cases from `edge_case.md` have corresponding test cases
- [ ] Mock data mode runs the full system with no external API calls
- [ ] Performance baselines met on Railway staging environment
- [ ] Zero type errors in TypeScript frontend

---

## 14. Phase 10 — Deployment & Handoff

**Goal:** The system is fully deployed, documented, and handed off to the PM team for research use.

### 14.1 Production Deployment
- [ ] Run `alembic upgrade head` on production Railway PostgreSQL
- [ ] Enable Railway PostgreSQL automatic backups
- [ ] Set all production env vars in Railway (using the reference in `architecture.md §16`)
- [ ] Enable Vercel analytics (basic performance monitoring)
- [ ] Verify `GET /health` returns `{status: ok, db: ok, gemini: ok}` on production
- [ ] Run smoke test: create project → import 10 records → classify → view evidence → generate report

### 14.2 README
Write `README.md` covering:
- [ ] Project overview and purpose (1 paragraph)
- [ ] System architecture diagram (reference `architecture.md`)
- [ ] Quick start (local development setup in < 5 commands)
- [ ] Environment variables reference (all variables, descriptions, required/optional)
- [ ] Backend setup: `pip install`, `alembic upgrade head`, `uvicorn main:app`
- [ ] Frontend setup: `npm install`, `npm run dev`
- [ ] Mock data mode: `MOCK_DATA_MODE=true` — how to use, what it returns
- [ ] Railway deployment steps (backend + PostgreSQL)
- [ ] Vercel deployment steps (frontend)
- [ ] Running tests: `pytest tests/` and `npm run test`
- [ ] Known limitations (verbatim from `architecture.md §18`)
- [ ] Contributing guide

### 14.3 Researcher Onboarding Guide
Write `docs/researcher_guide.md`:
- [ ] How to create a research project
- [ ] How to upload data (manual CSV import)
- [ ] How to start a classification run
- [ ] How to review the human review queue
- [ ] How to interpret confidence scores (include tooltip text explaining they are not statistical)
- [ ] How to read the taxonomy and opportunity comparison views
- [ ] How to generate and export a research report
- [ ] FAQ: what to do when the Gemini API is unavailable

### 14.4 Phase 10 Acceptance Criteria
- [ ] Production system accessible at Vercel URL with Railway backend
- [ ] `GET /health` returns all green on production
- [ ] README allows a new engineer to run the system locally in < 30 minutes
- [ ] Researcher guide allows a PM to complete a full discovery workflow without engineering support
- [ ] All env vars documented with no placeholders remaining

---

## 15. Dependency Map

```
Phase 0 (Scaffold)
    |
    +---> Phase 1 (Data Model & Auth)
                |
                +---> Phase 2 (Ingestion)
                            |
                            +---> Phase 3 (Gemini Classification)
                            |               |
                            |               +---> Phase 6 (Semantic Search)
                            |               |
                            |               +---> Phase 4 (Taxonomy & Opportunities)
                            |                               |
                            |                               +---> Phase 7 (Report Generation)
                            |
                            +---> Phase 5 (Frontend Dashboard) --------+
                                                                        |
                                            Phase 8 (Security) --------+
                                                    |
                                            Phase 9 (Testing & Hardening)
                                                    |
                                            Phase 10 (Deployment & Handoff)
```

**Critical Path:** Phase 0 → 1 → 2 → 3 → 4 → 7 → 9 → 10
**Parallelisable:** Phase 5 can begin after Phase 1 (backend stubs). Phase 6 can begin after Phase 3.

---

## 16. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | Gemini API rate limits throttle classification at scale | High | High | Exponential backoff, batch size tuning, paused-job resume |
| R2 | Public source platforms change API or block scraping | Medium | High | Manual import as primary MVP path; adapters as optional enhancements |
| R3 | Gemini returns ungrounded or fabricated evidence excerpts | Medium | Critical | Substring validation post-extraction; human review queue |
| R4 | Evidence base skewed by single prolific user | High | Medium | `unique_author_count` metric; pseudonym-based dedup in frequency counts |
| R5 | Railway OOM during large analysis runs | Medium | High | Batch processing (50 records), async sessions, memory-bounded workers |
| R6 | PII inadvertently exposed in frontend | Low | Critical | Pseudonymisation at ingest, PII detection before display, no raw handles in API responses |
| R7 | Taxonomy clustering produces unhelpful single mega-cluster | Medium | High | Min/max cluster count enforcement; sub-clustering on oversized clusters |
| R8 | PM interprets Gemini confidence as statistical significance | High | High | UI tooltips, report disclaimers, researcher guide, naming convention (avoid "significance") |
| R9 | Incomplete dataset used for published research | Medium | High | `is_partial_dataset` warning banner on all views and reports; cannot be dismissed |
| R10 | JWT secret rotation causes total session loss | Low | Medium | Grace period with dual-key support; advance user notification |

---

## 17. Definition of Done

A phase is **Done** when all of the following are true:

- [ ] All tasks in the phase checklist are checked off
- [ ] All acceptance criteria for the phase are met
- [ ] CI pipeline passes (backend tests + frontend type checks)
- [ ] No `TODO` or `FIXME` comments remain in newly written code
- [ ] No hardcoded secrets, API keys, or credentials in any committed file
- [ ] Code reviewed by at least one other engineer (or PM, for research-facing content)
- [ ] New endpoints are documented in the OpenAPI spec (auto-generated by FastAPI)
- [ ] Edge cases relevant to the phase (from `edge_case.md`) have test coverage

A feature is **Done** when:
- [ ] It works in mock data mode (`MOCK_DATA_MODE=true`)
- [ ] It works with live Railway + Gemini on staging
- [ ] It handles the empty state and error state gracefully
- [ ] It does not expose PII or secrets

---

## 18. Open Questions

| # | Question | Impact | Owner | Status |
|---|----------|--------|-------|--------|
| Q1 | Which Gemini model version should be used for production? (`gemini-1.5-pro` vs `gemini-2.0-flash` — tradeoff: quality vs. cost/latency) | Medium | Engineering | Open |
| Q2 | Should Railway use Celery + Redis for the job queue from day one, or start with FastAPI BackgroundTasks? | Medium | Engineering | Recommend BackgroundTasks for MVP |
| Q3 | What is the acceptable confidence threshold for auto-approval vs. human review? (Currently 0.7 — tunable) | High | PM + Engineering | Open |
| Q4 | Do we need multilingual support in v1? Non-English records are currently flagged but not translated. | Medium | PM | Open |
| Q5 | Should `source_url` always be required? Some scraped data may not have stable URLs. | Low | Engineering | Open |
| Q6 | What user authentication system is used? (Currently JWT with hardcoded admin user — sufficient for MVP internal tool?) | Medium | PM | Open |
| Q7 | Is there a maximum project lifetime or data retention policy required? | Low | PM + Legal | Open |
| Q8 | Should the human review queue support assignment (which reviewer handles which records)? | Medium | PM | Open |
| Q9 | Should reports be version-controlled within the project, or is one active report per project sufficient? | Low | PM | Recommend multiple report versions |
| Q10 | Is there a budget cap for Gemini API usage per project? Should we estimate and display token costs? | High | PM | Open |

---

*This implementation plan should be updated at the end of each phase with actual progress, blockers, and any scope changes.*
