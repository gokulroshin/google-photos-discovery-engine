# Architecture: AI-Powered Photo Retrieval Discovery Engine

> **Version:** 1.0
> **Stack:** Gemini LLM · Next.js (Vercel) · FastAPI (Railway) · PostgreSQL
> **Last updated:** 2026-09-20

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture Diagram](#2-high-level-architecture-diagram)
3. [Component Breakdown](#3-component-breakdown)
4. [Data Model](#4-data-model)
5. [API Design](#5-api-design)
6. [Gemini Integration](#6-gemini-integration)
7. [Discovery Engine Pipeline](#7-discovery-engine-pipeline)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Backend Architecture](#9-backend-architecture)
10. [Infrastructure & Deployment](#10-infrastructure--deployment)
11. [Security Architecture](#11-security-architecture)
12. [Source Adapter System](#12-source-adapter-system)
13. [Job & Queue System](#13-job--queue-system)
14. [Observability & Monitoring](#14-observability--monitoring)
15. [Testing Strategy](#15-testing-strategy)
16. [Environment Variables Reference](#16-environment-variables-reference)
17. [Key Architectural Decisions](#17-key-architectural-decisions)
18. [Limitations & Known Gaps](#18-limitations--known-gaps)

---

## 1. System Overview

The Photo Retrieval Discovery Engine is a **research-grade data intelligence platform** built to help Product Managers at Google Photos identify, classify, and compare user-reported photo retrieval failures driven by incomplete or uncertain memory.

It is **not** a product feature. It is a structured discovery system that collects public evidence, runs AI-assisted classification through Google Gemini, and surfaces a traceable taxonomy of retrieval problems -- enabling evidence-backed product decisions.

### Design Pillars

| Pillar | Implication |
|--------|-------------|
| **Evidence-first** | Every insight links to a real source record. Nothing is fabricated. |
| **Modular** | Data sources, models, and analysis steps are swappable. |
| **Transparent** | Confidence scores, rationale, and source diversity are always shown. |
| **Human-in-the-loop** | Researchers can review, correct, or override AI classifications. |
| **Resilient** | System degrades gracefully when APIs or sources are unavailable. |

---

## 2. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------+
|                        RESEARCHER (Product Manager)                         |
+-----------------------------+-----------------------------------------------+
                              | HTTPS
                              v
+-----------------------------------------------------------------------------+
|                    FRONTEND  (Vercel / Next.js + TypeScript)                |
|                                                                             |
|  +----------------+  +-------------+  +--------------+  +----------------+ |
|  |    Overview    |  | Data Explorer|  |Evidence View |  |Problem Taxonomy| |
|  +----------------+  +-------------+  +--------------+  +----------------+ |
|  +----------------+  +-------------+  +--------------+  +----------------+ |
|  |  Opportunity   |  | Search/RAG  |  | Research Rpt |  |  Job Monitor   | |
|  |  Comparison    |  |  Discovery  |  |   & Export   |  |  Human Review  | |
|  +----------------+  +-------------+  +--------------+  +----------------+ |
+-----------------------------+-----------------------------------------------+
                              | REST API (HTTPS + JWT Auth)
                              v
+-----------------------------------------------------------------------------+
|                     BACKEND  (Railway / FastAPI + Python)                   |
|                                                                             |
|  +-----------------+  +--------------------+  +------------------------+   |
|  |   API Layer     |  |   Service Layer    |  |   Job / Task Queue     |   |
|  |   (FastAPI)     |  |  (Business Logic)  |  |  (Background Workers)  |   |
|  +--------+--------+  +---------+----------+  +----------+-------------+   |
|           |                     |                          |                |
|           +---------------------+--------------------------+                |
|                                 |                                           |
|                    +------------v--------------+                            |
|                    |   Data Access Layer (ORM) |                            |
|                    +------------+--------------+                            |
+----------------------------------------+------------------------------------+
                                         |
            +----------------------------+---------------------------+
            v                            v                           v
  +------------------+    +--------------------+    +--------------------+
  |   PostgreSQL     |    |  pgvector / Vector |    |  Object Storage    |
  |  (Primary DB)    |    |   Semantic Index   |    |  (Datasets/Files)  |
  +------------------+    +--------------------+    +--------------------+
                                         |
                                         v
                          +--------------------------+
                          |   Google Gemini API      |
                          |   (Server-side only)     |
                          +--------------------------+
```

---

## 3. Component Breakdown

### 3.1 Frontend (Vercel)

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| App shell | Next.js 14 + TypeScript | Routing, layouts, auth guard |
| UI library | Radix UI + custom CSS | Accessible component primitives |
| State management | Zustand | Global UI state, filters, session |
| Data fetching | TanStack Query (React Query) | API calls, caching, loading/error states |
| Charts & tables | Recharts / Tremor | Evidence frequency, opportunity scoring |
| Search UI | Custom + debounced API calls | Semantic and keyword discovery |
| Export | Client-side CSV/JSON | Structured data export for researchers |

### 3.2 Backend (Railway)

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| API framework | FastAPI (Python 3.11+) | REST endpoints, request validation, auth |
| ORM | SQLAlchemy 2.x + Alembic | Data models, migrations |
| Task queue | FastAPI BackgroundTasks (→ Celery at scale) | Async ingestion and analysis jobs |
| Gemini client | google-generativeai SDK | Prompt execution, retry, validation |
| Validation | Pydantic v2 | Schema enforcement for all model outputs |
| Auth | JWT (python-jose) | Stateless API authentication |
| Logging | structlog | Structured JSON logs for observability |

### 3.3 Storage

| Store | Technology | Contents |
|-------|-----------|----------|
| Primary DB | PostgreSQL 16 | All entities (see Section 4) |
| Vector index | pgvector extension | Embeddings for semantic search and RAG |
| File storage | Railway volumes or S3-compatible | Uploaded datasets, exported reports |

### 3.4 External Services

| Service | Purpose | Access Point |
|---------|---------|-------------|
| Google Gemini API | Classification, extraction, clustering, summarization | Backend only (env var key) |
| Public data sources | Reddit, App Stores, YouTube, forums | Source adapters (backend only) |

---

## 4. Data Model

### Entity Relationship Overview

```
ResearchProject
    +-- DataSourceConfig (1:N)
    +-- IngestionJob (1:N)
            +-- SourceRecord (1:N)        <- raw collected content
                    +-- EvidenceRecord (1:1)   <- AI-extracted structured fields
                            +-- Classification (1:N)  <- relevance labels
                            +-- HumanReview (0:1)     <- researcher override
TaxonomyCategory
    +-- EvidenceRecord (M:N via mapping table)
OpportunityArea
    +-- TaxonomyCategory (M:N)
    +-- OpportunityScore (1:N)            <- per dimension
ModelRun
    +-- EvidenceRecord (1:N)              <- which model run produced which records
```

### Core Table Schemas

#### `research_projects`
```sql
id                  UUID PRIMARY KEY
name                TEXT NOT NULL
description         TEXT
research_questions  JSONB          -- list of question strings
status              TEXT           -- draft | active | archived
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

#### `source_records`
```sql
id                  UUID PRIMARY KEY
project_id          UUID REFERENCES research_projects
source_platform     TEXT           -- reddit | play_store | app_store | youtube | forum | manual
source_url          TEXT           -- original URL (preserved for auditability)
source_date         TIMESTAMPTZ    -- publish date of original content
raw_content         TEXT           -- original unmodified text
author_handle       TEXT           -- anonymized where possible
collection_method   TEXT           -- api | scrape | manual_import
collection_date     TIMESTAMPTZ
ingestion_job_id    UUID REFERENCES ingestion_jobs
is_duplicate        BOOLEAN DEFAULT FALSE
dedup_hash          TEXT           -- SHA-256 content fingerprint
metadata            JSONB          -- platform-specific extras (score, upvotes, etc.)
created_at          TIMESTAMPTZ
```

#### `evidence_records`
```sql
id                      UUID PRIMARY KEY
source_record_id        UUID REFERENCES source_records
model_run_id            UUID REFERENCES model_runs
is_relevant             BOOLEAN
relevance_labels        TEXT[]          -- multi-label array
retrieval_scenario      TEXT
memory_cues             JSONB           -- {person, place, time, event, object, visual,
                                        --  text_in_image, emotion, purpose, image_source}
missing_information     TEXT
search_behavior         TEXT
retrieval_outcome       TEXT            -- successfully_retrieved | multiple_attempts |
                                        -- manual_browse | alternative | not_retrieved |
                                        -- abandoned | unclear
failure_points          TEXT[]
user_segment            TEXT
evidence_excerpt        TEXT
confidence_score        FLOAT           -- 0.0 to 1.0
rationale               TEXT
needs_human_review      BOOLEAN DEFAULT FALSE
embedding               vector(768)     -- pgvector field for semantic search
created_at              TIMESTAMPTZ
updated_at              TIMESTAMPTZ
```

#### `taxonomy_categories`
```sql
id                      UUID PRIMARY KEY
project_id              UUID REFERENCES research_projects
name                    TEXT
definition              TEXT
user_segment            TEXT
common_memory_cues      JSONB
missing_information     TEXT
common_search_behavior  TEXT
failure_mechanism       TEXT
evidence_count          INTEGER
source_diversity        JSONB           -- {platform: count}
representative_excerpts TEXT[]
confidence_level        TEXT            -- high | medium | low
open_questions          TEXT[]
product_implications    TEXT
created_at              TIMESTAMPTZ
updated_at              TIMESTAMPTZ
```

#### `opportunity_areas`
```sql
id                      UUID PRIMARY KEY
project_id              UUID REFERENCES research_projects
name                    TEXT
description             TEXT
evidence_frequency      INTEGER
evidence_diversity      JSONB
user_impact_score       FLOAT
abandonment_rate        FLOAT
workaround_exists       BOOLEAN
strategic_relevance     FLOAT
problem_clarity         FLOAT
potential_reach         TEXT
validation_effort       TEXT            -- low | medium | high
scoring_methodology     TEXT
analyst_notes           TEXT
status                  TEXT            -- draft | validated | rejected
created_at              TIMESTAMPTZ
```

#### `model_runs`
```sql
id              UUID PRIMARY KEY
project_id      UUID REFERENCES research_projects
model_name      TEXT                -- e.g. gemini-1.5-pro
prompt_version  TEXT
parameters      JSONB               -- temperature, top_p, etc.
status          TEXT                -- running | completed | failed
records_total   INTEGER
records_success INTEGER
records_failed  INTEGER
error_log       JSONB
started_at      TIMESTAMPTZ
completed_at    TIMESTAMPTZ
```

#### `human_reviews`
```sql
id                  UUID PRIMARY KEY
evidence_record_id  UUID REFERENCES evidence_records
reviewer_id         UUID
action              TEXT    -- approved | corrected | rejected
corrections         JSONB   -- field-level overrides
reviewer_notes      TEXT
reviewed_at         TIMESTAMPTZ
```

#### `ingestion_jobs`
```sql
id              UUID PRIMARY KEY
project_id      UUID REFERENCES research_projects
source_type     TEXT
status          TEXT    -- queued | running | completed | failed | cancelled
config          JSONB   -- source-specific params (subreddit, query, date range)
records_found   INTEGER
records_stored  INTEGER
error_details   JSONB
started_at      TIMESTAMPTZ
completed_at    TIMESTAMPTZ
```

---

## 5. API Design

### Base URL
```
Production:  https://api.photodiscovery.railway.app/v1
Development: http://localhost:8000/v1
```

### Authentication
All endpoints (except `GET /health` and `POST /auth/login`) require a Bearer JWT token:
```
Authorization: Bearer <token>
```

### Endpoint Reference

#### Projects
```
POST   /projects                    Create a new research project
GET    /projects                    List all projects
GET    /projects/{id}               Get project details
PATCH  /projects/{id}               Update project metadata
DELETE /projects/{id}               Archive a project
```

#### Data Ingestion
```
POST   /projects/{id}/jobs                  Start an ingestion job
GET    /projects/{id}/jobs                  List jobs for a project
GET    /projects/{id}/jobs/{job_id}         Get job status and error log
DELETE /projects/{id}/jobs/{job_id}         Cancel a running job
POST   /projects/{id}/import                Upload a dataset file (CSV/JSON)
```

#### Source Records
```
GET    /projects/{id}/records               List records (filters: platform, date, is_duplicate)
GET    /projects/{id}/records/{record_id}   Get individual source record
DELETE /projects/{id}/records/{record_id}   Delete a source record
```

#### Evidence & Classification
```
POST   /projects/{id}/analyze               Start classification run on unprocessed records
GET    /projects/{id}/evidence              List evidence (filters: scenario, outcome, confidence)
GET    /projects/{id}/evidence/{ev_id}      Get evidence record with full Gemini rationale
GET    /projects/{id}/evidence/search       Semantic search over evidence (?q=query)
```

#### Taxonomy
```
POST   /projects/{id}/taxonomy/generate     Trigger taxonomy clustering from evidence
GET    /projects/{id}/taxonomy              List taxonomy categories
GET    /projects/{id}/taxonomy/{cat_id}     Get category with evidence and open questions
PATCH  /projects/{id}/taxonomy/{cat_id}     Update category (human refinement)
```

#### Opportunity Areas
```
POST   /projects/{id}/opportunities         Create or generate opportunity areas
GET    /projects/{id}/opportunities         List with all scoring dimensions
GET    /projects/{id}/opportunities/{op_id} Get opportunity detail with evidence trail
PATCH  /projects/{id}/opportunities/{op_id} Update analyst notes or scores
```

#### Human Review
```
GET    /projects/{id}/review/queue          List records flagged for review
POST   /projects/{id}/review/{ev_id}        Submit review action (approve/correct/reject)
```

#### Reports & Export
```
POST   /projects/{id}/reports               Generate a research report
GET    /projects/{id}/reports               List generated reports
GET    /projects/{id}/reports/{rpt_id}      Get report (JSON or Markdown)
GET    /projects/{id}/export/evidence       Export evidence as CSV/JSON
GET    /projects/{id}/export/taxonomy       Export taxonomy as CSV/JSON
```

#### System
```
GET    /health                              Health check (no auth required)
POST   /auth/login                          Obtain JWT token
GET    /auth/me                             Current user info
```

---

## 6. Gemini Integration

### Architecture Principles
- All Gemini calls are made **server-side only** from the Railway backend
- API key stored in `GEMINI_API_KEY` environment variable; never in code or frontend
- Prompts are version-controlled Jinja2 templates stored in `backend/prompts/`
- Responses are validated against Pydantic schemas before storage
- Failed or malformed responses are flagged for human review, not silently discarded

### Prompt Templates

| Template | File | Purpose |
|----------|------|---------|
| Relevance filter | `relevance_filter.j2` | Decide if a record is about incomplete-memory photo retrieval |
| Extraction | `extraction.j2` | Extract all 12 structured fields from relevant records |
| Taxonomy clustering | `taxonomy_cluster.j2` | Group evidence into distinct retrieval problem categories |
| Opportunity scoring | `opportunity_score.j2` | Score opportunity areas across 9 dimensions |
| Query generation | `query_generation.j2` | Generate targeted search queries from research questions |
| Summary synthesis | `summary_synthesis.j2` | Generate human-readable research report sections |

### Gemini Call Flow

```
BackgroundWorker
    |
    +-- Load source record (raw_content)
    +-- Render Jinja2 prompt template with record context
    +-- Call Gemini API (gemini-1.5-pro, response_mime_type="application/json")
    |       +-- Retry on 429 / 503 (exponential backoff, max 3 attempts)
    |       +-- On persistent failure: mark record status=failed, log error
    +-- Parse JSON response
    +-- Validate against Pydantic schema
    |       +-- On schema violation: flag needs_human_review=True, store raw response
    +-- Store EvidenceRecord in PostgreSQL
    +-- Generate embedding (Gemini text-embedding-004) -> store in pgvector
```

### Pydantic Output Schema

```python
class RetrievalOutcome(str, Enum):
    SUCCESSFULLY_RETRIEVED = "successfully_retrieved"
    MULTIPLE_ATTEMPTS      = "multiple_attempts"
    MANUAL_BROWSE          = "manual_browse"
    ALTERNATIVE_METHOD     = "alternative_method"
    NOT_RETRIEVED          = "not_retrieved"
    ABANDONED              = "abandoned"
    UNCLEAR                = "unclear"

class MemoryCues(BaseModel):
    person:            str | None = None
    place:             str | None = None
    approximate_time:  str | None = None
    event_or_activity: str | None = None
    object:            str | None = None
    visual_appearance: str | None = None
    text_in_image:     str | None = None
    emotional_context: str | None = None
    capture_purpose:   str | None = None
    image_source:      str | None = None

class EvidenceExtraction(BaseModel):
    is_relevant:          bool
    relevance_labels:     list[str]
    retrieval_scenario:   str | None = None
    memory_cues:          MemoryCues | None = None
    missing_information:  str | None = None
    search_behavior:      str | None = None
    retrieval_outcome:    RetrievalOutcome | None = None
    failure_points:       list[str] = []
    user_segment:         str | None = None
    evidence_excerpt:     str | None = None
    confidence_score:     float           # 0.0 - 1.0
    rationale:            str
    needs_human_review:   bool = False
```

---

## 7. Discovery Engine Pipeline

### Stage 1 -- Research Setup
```
Researcher creates a project
    -> defines research questions
    -> configures data source targets
```

### Stage 2 -- Query Generation
```
Research questions + Gemini (query_generation prompt)
    -> targeted search queries per source platform
    -> stored in DataSourceConfig for each adapter
```

### Stage 3 -- Ingestion
```
Source Adapters fetch/receive content:
    +-- RedditAdapter        -> PRAW API
    +-- PlayStoreAdapter     -> google-play-scraper
    +-- AppStoreAdapter      -> iTunes RSS / scraper
    +-- YouTubeAdapter       -> YouTube Data API v3
    +-- ForumAdapter         -> requests + BeautifulSoup (rate-limited)
    +-- ManualImportAdapter  -> CSV/JSON file upload (MVP default)

Each adapter:
    -> normalize to SourceRecord schema
    -> compute SHA-256 dedup hash
    -> skip duplicates
    -> store SourceRecord to PostgreSQL
```

### Stage 4 -- Relevance Filtering
```
For each SourceRecord (status=new):
    -> Gemini (relevance_filter prompt)
    -> {is_relevant: bool, confidence: float}

    If is_relevant=True         -> proceed to Stage 5
    If is_relevant=False        -> mark as irrelevant, skip
    If confidence < 0.7         -> flag needs_human_review=True
```

### Stage 5 -- Extraction & Classification
```
For each relevant SourceRecord:
    -> Gemini (extraction prompt)
    -> EvidenceExtraction (Pydantic-validated)
    -> Generate text embedding (Gemini text-embedding-004)
    -> Store EvidenceRecord with embedding in pgvector
```

### Stage 6 -- Taxonomy Clustering
```
All EvidenceRecords
    -> Cluster by failure_points + retrieval_scenario + memory_cues
    +-- Semantic clustering via pgvector cosine similarity
    +-- Gemini (taxonomy_cluster prompt) -> human-readable category definitions
    -> Store TaxonomyCategory records
```

### Stage 7 -- Opportunity Comparison
```
TaxonomyCategories
    -> Gemini (opportunity_score prompt)
    -> OpportunityArea records with scores on 9 dimensions:
        evidence_frequency, evidence_diversity, user_impact,
        abandonment_rate, workaround_exists, strategic_relevance,
        problem_clarity, potential_reach, validation_effort
    -> Researcher can adjust scores + add analyst notes
    -> Side-by-side comparison view in dashboard
```

### Stage 8 -- Report Generation
```
Researcher triggers report
    -> Gemini (summary_synthesis prompt) over selected evidence + taxonomy
    -> Markdown research report with:
        - Executive summary
        - Retrieval problem taxonomy with evidence counts
        - Opportunity area comparison with scoring methodology
        - Full evidence trail and source citations
        - Confidence ratings and named limitations
        - Open questions for primary research follow-up
```

---

## 8. Frontend Architecture

### Directory Structure

```
frontend/
+-- app/
|   +-- layout.tsx                  # Root layout + auth provider
|   +-- page.tsx                    # Redirect to /projects
|   +-- (auth)/
|   |   +-- login/page.tsx
|   +-- projects/
|       +-- page.tsx                # Project list
|       +-- [id]/
|           +-- page.tsx            # Overview dashboard
|           +-- explorer/           # Data explorer (filter by source/date/label)
|           +-- evidence/           # Evidence viewer
|           +-- taxonomy/           # Problem taxonomy view
|           +-- opportunities/      # Opportunity comparison matrix
|           +-- search/             # Semantic discovery interface
|           +-- report/             # Research report & export
|           +-- review/             # Human review queue
|           +-- jobs/               # Job monitoring
+-- components/
|   +-- ui/                         # Base primitives (Button, Table, Badge, etc.)
|   +-- evidence/                   # EvidenceCard, ExcerptViewer, ConfidenceBadge
|   +-- taxonomy/                   # CategoryCard, EvidenceLink, OpenQuestions
|   +-- opportunity/                # OpportunityMatrix, ScoreBar, DimensionTable
|   +-- jobs/                       # JobStatusBadge, ProgressBar, JobLog
|   +-- layout/                     # Sidebar, Header, Breadcrumbs
+-- lib/
|   +-- api.ts                      # Typed API client (fetch wrapper + error handling)
|   +-- auth.ts                     # JWT handling, session management
|   +-- types.ts                    # Shared TypeScript interfaces
+-- hooks/
|   +-- useEvidence.ts              # TanStack Query hooks for evidence data
|   +-- useTaxonomy.ts
|   +-- useJobs.ts                  # Polls job status every 5s
+-- store/
    +-- filters.ts                  # Zustand store for active filter state
```

### Key Frontend Patterns

| Pattern | Detail |
|---------|--------|
| All API calls via `lib/api.ts` | Never raw `fetch` in components |
| Server Components for static content | Client Components only for interactive elements |
| TanStack Query for all data fetching | Caching, background refresh, loading/error/empty states |
| Optimistic updates | Human review queue actions update UI before server confirms |
| Job page polling | Every 5s via `refetchInterval` in useJobs hook |
| No secrets in frontend | JWT stored in httpOnly cookie; API URL via `NEXT_PUBLIC_API_URL` |

---

## 9. Backend Architecture

### Directory Structure

```
backend/
+-- main.py                         # FastAPI app factory + router registration
+-- config.py                       # Pydantic BaseSettings (reads env vars)
+-- database.py                     # SQLAlchemy engine + async session factory
+-- auth/
|   +-- router.py                   # POST /auth/login, GET /auth/me
|   +-- dependencies.py             # get_current_user FastAPI dependency
+-- routers/
|   +-- projects.py
|   +-- jobs.py
|   +-- records.py
|   +-- evidence.py
|   +-- taxonomy.py
|   +-- opportunities.py
|   +-- review.py
|   +-- reports.py
+-- models/                         # SQLAlchemy ORM models (one file per entity)
+-- schemas/                        # Pydantic request/response schemas
+-- services/
|   +-- ingestion_service.py        # Orchestrates adapters + dedup + storage
|   +-- analysis_service.py         # Orchestrates Gemini extraction pipeline
|   +-- taxonomy_service.py         # Clustering + taxonomy generation
|   +-- opportunity_service.py      # Opportunity scoring and comparison
|   +-- report_service.py           # Report generation + export
+-- adapters/
|   +-- base.py                     # Abstract SourceAdapter base class
|   +-- reddit.py
|   +-- play_store.py
|   +-- app_store.py
|   +-- youtube.py
|   +-- forum.py
|   +-- manual_import.py            # MVP default
+-- gemini/
|   +-- client.py                   # Gemini API wrapper (retry, validation, logging)
|   +-- prompts/                    # Jinja2 .j2 prompt templates (version-controlled)
|   +-- schemas.py                  # Pydantic schemas for all Gemini outputs
+-- workers/
|   +-- ingestion_worker.py         # Background task: run ingestion job end-to-end
|   +-- analysis_worker.py          # Background task: run Gemini analysis on records
+-- migrations/                     # Alembic migration files
+-- tests/
    +-- fixtures/                   # Mock data for MOCK_DATA_MODE
    +-- test_adapters.py
    +-- test_gemini_schemas.py
    +-- test_services.py
    +-- test_api.py
```

---

## 10. Infrastructure & Deployment

### Frontend -- Vercel

| Setting | Value |
|---------|-------|
| Framework preset | Next.js (auto-detected) |
| Build command | `npm run build` |
| Output directory | `.next` |
| Environment variables | `NEXT_PUBLIC_API_URL`, `NEXTAUTH_SECRET` |
| Deploy trigger | Push to `main` branch |
| Preview deployments | Auto-generated per PR |

### Backend -- Railway

| Setting | Value |
|---------|-------|
| Runtime | Python 3.11 (Nixpacks auto-detected) |
| Start command | `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `GET /health` |
| Database | Railway PostgreSQL plugin (auto-provisioned, connection via `DATABASE_URL`) |
| Persistent volume | `/data` mounted for file uploads and exports |

### CI/CD (GitHub Actions)

```yaml
on: [pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=. --cov-report=xml
        env:
          MOCK_DATA_MODE: "true"
          DATABASE_URL: "sqlite+aiosqlite:///:memory:"

  frontend-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run type-check
      - run: npm run lint
```

---

## 11. Security Architecture

| Concern | Mitigation |
|---------|-----------|
| API key exposure | `GEMINI_API_KEY` only in Railway env vars; never in source code or frontend |
| Authentication | JWT Bearer tokens with configurable expiry; refresh token pattern |
| Authorization | Role-based: `admin` (full access), `researcher` (read + review only) |
| Input validation | Pydantic on all incoming request bodies; parameterized SQL via SQLAlchemy |
| CORS | Vercel domain explicitly whitelisted; no wildcard `*` origin in production |
| PII handling | Usernames anonymized before storage; no unnecessary personal data collected |
| Data provenance | Source URLs + collection timestamps always stored and preserved |
| Secret management | No hardcoded credentials anywhere; `.env` in `.gitignore` |
| Audit trail | All Gemini model runs and human review actions logged with timestamps |
| Rate limiting | FastAPI middleware enforces req/min per authenticated user |
| Dependency security | `pip audit` and `npm audit` in CI pipeline |

---

## 12. Source Adapter System

### Abstract Interface

```python
from abc import ABC, abstractmethod
import hashlib

class SourceAdapter(ABC):

    @abstractmethod
    async def fetch(self, config: dict) -> list[RawRecord]:
        """Fetch raw records from the source platform."""
        ...

    @abstractmethod
    def normalize(self, raw: RawRecord) -> SourceRecordCreate:
        """Normalize a raw record into the standard SourceRecord schema."""
        ...

    def compute_dedup_hash(self, content: str) -> str:
        """SHA-256 fingerprint for deduplication."""
        return hashlib.sha256(content.strip().encode()).hexdigest()
```

### Adding a New Source (4 steps)
1. Create `backend/adapters/new_source.py` implementing `SourceAdapter`
2. Register in `backend/adapters/__init__.py` adapter registry
3. Add the new platform name to the `source_platform` enum
4. Add an Alembic migration for any new platform-specific metadata fields

### Adapter Roadmap

| Adapter | Method | Priority |
|---------|--------|----------|
| Manual Import | CSV / JSON file upload | **MVP** |
| Google Play Store | google-play-scraper library | Phase 2 |
| Apple App Store | iTunes RSS + scraper | Phase 2 |
| Reddit | PRAW API | Phase 2 |
| YouTube | YouTube Data API v3 | Phase 3 |
| Public Forums | requests + BeautifulSoup | Phase 3 |

---

## 13. Job & Queue System

### Job Lifecycle

```
POST /projects/{id}/jobs
    -> Create IngestionJob record (status=queued)
    -> Enqueue FastAPI BackgroundTask

BackgroundTask (ingestion_worker.py)
    -> Update status=running
    -> Fetch records in batches (batch_size=50)
    -> Update records_found, records_stored after each batch
    -> On error: update status=failed, write error_details
    -> On success: update status=completed, completed_at

GET /projects/{id}/jobs/{job_id}
    -> Poll status + progress + error log
```

### Job Types

| Job Type | Trigger Endpoint | Worker Module |
|----------|-----------------|---------------|
| `ingest_source` | `POST /jobs` with source config | `ingestion_worker.py` |
| `analyze_records` | `POST /analyze` | `analysis_worker.py` |
| `generate_taxonomy` | `POST /taxonomy/generate` | `taxonomy_service.py` |
| `generate_report` | `POST /reports` | `report_service.py` |

### Scaling Path
For MVP: use FastAPI `BackgroundTasks` (in-process, simple).
When job volume grows: replace with **Celery + Redis** on Railway.
The worker interface (`async def run_job(job_id)`) remains identical -- no API contract changes needed.

---

## 14. Observability & Monitoring

| Signal | Implementation | Where visible |
|--------|---------------|---------------|
| Structured logs | `structlog` JSON to stdout | Railway log drain |
| Health check | `GET /health` -> `{status, db, gemini}` | Railway health monitor |
| Job progress | `records_found` / `records_stored` updated per batch | Frontend Job Monitor |
| Gemini errors | Logged to `model_runs.error_log` with raw response | Frontend Job Monitor |
| Human review backlog | Count from `GET /review/queue` | Overview dashboard |
| Confidence distribution | Histogram of `confidence_score` across evidence | Overview dashboard |
| Source diversity | Platform breakdown per insight | Evidence Viewer, Taxonomy |

---

## 15. Testing Strategy

### Backend Tests

| Layer | Type | What is tested |
|-------|------|---------------|
| Pydantic schemas | Unit | Gemini output validation, edge cases, enum handling |
| Service logic | Unit (mocked Gemini + DB) | Ingestion, dedup, classification, clustering |
| API endpoints | Integration (FastAPI TestClient) | All CRUD + auth flows + error codes |
| Source adapters | Unit (mocked HTTP responses) | Normalization and deduplication logic |

### Frontend Tests

| Layer | Type |
|-------|------|
| TypeScript types | Static analysis (`tsc --noEmit`) |
| Component rendering | React Testing Library |
| API integration | MSW (Mock Service Worker) intercepts |

### Mock Data Mode
Set `MOCK_DATA_MODE=true` to run the full system using fixture data from `backend/tests/fixtures/`.
No Gemini API key or live data sources required. Used in CI and for demos.

---

## 16. Environment Variables Reference

### Backend (Railway)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-pro
GEMINI_EMBEDDING_MODEL=text-embedding-004

# Authentication
JWT_SECRET_KEY=your_jwt_secret_key_min_32_chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
MOCK_DATA_MODE=false
ALLOWED_ORIGINS=https://your-app.vercel.app

# File Storage (optional)
STORAGE_BACKEND=local          # local | s3
S3_BUCKET=your-bucket-name
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_ENDPOINT_URL=...            # for non-AWS S3-compatible stores
```

### Frontend (Vercel)

```env
NEXT_PUBLIC_API_URL=https://api.photodiscovery.railway.app/v1
NEXTAUTH_SECRET=your_nextauth_secret_min_32_chars
```

---

## 17. Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | Google Gemini | Mandated by problem statement; native JSON mode; strong structured output |
| Backend framework | FastAPI | Async-native, Pydantic-native, excellent for AI/ML pipelines; auto OpenAPI docs |
| Frontend framework | Next.js + TypeScript | Mandated (Vercel-optimized); App Router for server components; type safety |
| Database | PostgreSQL + pgvector | Single store for relational data AND semantic search; avoids dual-DB complexity |
| Job queue | BackgroundTasks (MVP) then Celery | Simple to start; worker interface is identical when swapping |
| Prompt storage | Jinja2 templates in codebase | Version-controlled, reviewable, testable, parameterized |
| Authentication | JWT stateless | No session store needed for single-service backend |
| Deduplication | SHA-256 hash of raw content | Deterministic, fast, zero external dependency |
| Source adapters | Abstract base class | Add new sources without modifying the core pipeline |
| Mock data mode | Env flag + fixtures directory | Full system demo without live APIs; safe for CI |
| Confidence threshold | 0.7 (configurable) | Records below threshold auto-flagged for human review |
| Embeddings | Gemini text-embedding-004 via pgvector | Same vendor as classification; no additional infra |

---

## 18. Limitations & Known Gaps

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Public data only | Private support tickets and internal research are invisible | Document coverage gap explicitly in every generated report |
| English-language bias | Non-English user retrieval problems are underrepresented | Flag in all reports; recommend multilingual expansion in future |
| Platform sampling bias | Reddit skews technical users; App Store skews disengaged users | Show per-platform source diversity breakdown on every insight |
| Gemini confidence is not statistical certainty | Model may be confidently wrong | Always pair with human review queue; researcher sign-off before publishing |
| Batch ingestion only | No real-time or streaming data | Acceptable for discovery research; not a live monitoring tool |
| No primary user research | All evidence is indirect (public posts, reviews) | System explicitly identifies low-evidence areas needing primary research |
| API rate limits | Gemini and source platforms have rate limits | Exponential backoff + resumable jobs + batch size controls |
| Source ToS restrictions | Some platforms restrict automated access | Default to manual import; document ToS status per source |
| No multilingual support | Non-English posts may be missed or misclassified | Language detection field in SourceRecord; filter in UI |

---

*This document should be updated whenever significant structural changes are made to the system.*
