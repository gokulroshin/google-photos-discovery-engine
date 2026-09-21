# AI-Powered Photo Retrieval Discovery Engine

> A research-grade data intelligence platform built to help Product Managers at Google Photos identify, classify, synthesize, and compare user-reported photo retrieval failures driven by incomplete, ambiguous, or uncertain episodic memory.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14%2B-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Pro-8E75B2.svg)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/License-Internal%20Research-red.svg)](#-license--compliance)

---

## 📑 Table of Contents
1. [Executive Summary & Core Value Proposition](#-executive-summary--core-value-proposition)
2. [System Architecture & Data Flow](#-system-architecture--data-flow)
3. [Quick Start (Local Development in <5 Commands)](#-quick-start-local-development)
4. [Environment Variables Reference](#-environment-variables-reference)
5. [Mock Data Mode](#-mock-data-mode)
6. [Deployment Guide (Railway + Vercel)](#-deployment-guide)
7. [Database Migrations (Alembic)](#-database-migrations-alembic)
8. [Testing & Verification](#-testing--verification)
9. [Researcher & PM Onboarding](#-researcher--pm-onboarding)
10. [Known System Boundaries & Limitations](#-known-system-boundaries--limitations)
11. [Contributing Guidelines](#-contributing-guidelines)
12. [License & Compliance](#-license--compliance)

---

## 🔭 Executive Summary & Core Value Proposition

When users attempt to search their photo libraries using vague or partial memories (*e.g., "my dog in that yellow raincoat in Chicago in 2021"*, *"receipt from Home Depot on the glass coffee table"*), standard keyword indexing and single-object recognition models frequently fail.

The **AI-Powered Photo Retrieval Discovery Engine** transforms unstructured feedback across app stores, customer forums, Reddit, and user interviews into actionable, structured product intelligence:

```
Unstructured User Feedback (Play Store, App Store, Forums, Reddit, CSVs)
                                 │
                                 ▼
         ┌─────────────────────────────────────────────────┐
         │     Automated Preprocessing & Deduplication     │
         │   (SHA-256 Hashing, Length Filters, PII Scrub)  │
         └───────────────────────┬─────────────────────────┘
                                 │
                                 ▼
         ┌─────────────────────────────────────────────────┐
         │     Gemini 1.5 Pro Classification Pipeline      │
         │  (Scenario, Outcome, Failure Point, Confidence) │
         └───────────────────────┬─────────────────────────┘
                                 │
        ┌────────────────────────┴────────────────────────┐
        ▼                                                 ▼
┌───────────────────────────────┐     ┌───────────────────────────────────┐
│     Semantic Vector Index     │     │      Human Review Triage Queue    │
│  (768-dim Embeddings/Cosine)  │     │   (Confidence < 0.70 / Low Agree) │
└───────────────┬───────────────┘     └─────────────────┬─────────────────┘
                │                                       │
                └───────────────────┬───────────────────┘
                                    ▼
         ┌─────────────────────────────────────────────────┐
         │      Versioned Problem Taxonomy Synthesizer     │
         │ (K-Means Clustering + Gemini Cluster Extraction)│
         └───────────────────────┬─────────────────────────┘
                                 │
                                 ▼
         ┌─────────────────────────────────────────────────┐
         │      Opportunity Area 9-Dimension Scoring       │
         │ (Impact, Effort, Abandonment, Feasibility, etc.)│
         └───────────────────────┬─────────────────────────┘
                                 │
                                 ▼
         ┌─────────────────────────────────────────────────┐
         │      Grounded Research Report Synthesis         │
         │  (Direct Verbatim Evidence Citations & Export)  │
         └─────────────────────────────────────────────────┘
```

---

## 🏛️ System Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Client Layer [Next.js 14 Frontend / Browser]
        UI[PM Dashboard & Discovery Workspace]
        RQ[TanStack Query Cache]
        ZS[Zustand Filter & Selection State]
        UI --> RQ
        UI --> ZS
    end

    subgraph API Layer [FastAPI Backend]
        GW[FastAPI Gateway / JWT Auth / Rate Limiting]
        ROUTER[Modular Routers: Projects, Evidence, Taxonomy, Opportunities, Reports, Exports]
        GW --> ROUTER
    end

    subgraph Processing Layer [Async Workers & AI Engine]
        INGEST[Ingestion Worker & Delimiter Sniffer]
        ANALYZE[Analysis Worker & Batch Pipeline]
        GEMINI[Google Gemini 1.5 Pro & Text-Embedding-004]
        DEDUP[SHA-256 Deduplication & Content Sanitizer]
    end

    subgraph Persistence Layer [Storage & Vector Search]
        PG[(PostgreSQL + pgvector / SQLite Async)]
        VEC[768-dim Embedding Vector Index]
    end

    RQ -->|Async REST / SSE| GW
    ROUTER --> INGEST
    ROUTER --> ANALYZE
    ANALYZE --> GEMINI
    INGEST --> DEDUP
    INGEST --> PG
    ANALYZE --> PG
    ANALYZE --> VEC
```

---

## 🚀 Quick Start (Local Development)

Launch both backend and frontend locally in less than 5 commands:

```bash
# 1. Clone & Enter Repository
git clone https://github.com/google/photo-retrieval-discovery-engine.git && cd photo-retrieval-discovery-engine

# 2. Setup & Start Backend (runs in Mock Mode by default with zero setup required)
cd backend && python -m venv .venv && source .venv/bin/activate  # (On Windows: .venv\Scripts\activate)
pip install -r requirements.txt && uvicorn main:app --reload --port 8000 &

# 3. Setup & Start Frontend
cd ../frontend && npm install && npm run dev
```

- **Frontend App:** [http://localhost:3000](http://localhost:3000)
- **Backend Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check:** [http://localhost:8000/v1/health](http://localhost:8000/v1/health)

---

## ⚙️ Environment Variables Reference

Copy `.env.example` to `.env` in your root or `backend/` directory:

### Backend Variables

| Variable | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `DATABASE_URL` | String | `sqlite+aiosqlite:///./test.db` | PostgreSQL connection string (`postgresql+asyncpg://user:pass@host:5432/dbname`) or local SQLite. |
| `GEMINI_API_KEY` | String | `""` | Google AI Studio API key for Gemini 1.5 Pro and `text-embedding-004`. |
| `JWT_SECRET_KEY` | String | `secret-key-...` | Secret used to sign HMAC-SHA256 JWT tokens. |
| `JWT_ALGORITHM` | String | `HS256` | Token signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Int | `1440` | Token expiration lifetime in minutes (default: 24h). |
| `MOCK_DATA_MODE` | Boolean | `true` | When `true`, enables zero-API-cost mode with deterministic classifications & mock embeddings. |
| `LOG_LEVEL` | String | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `CORS_ORIGINS` | String | `http://localhost:3000,http://localhost:8000` | Comma-separated list of allowed CORS origins. |
| `ENVIRONMENT` | String | `development` | Runtime environment (`development`, `staging`, `production`). |
| `PORT` | Int | `8000` | HTTP port for Uvicorn server. |

### Frontend Variables

| Variable | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | String | `http://localhost:8000/v1` | URL pointing to the FastAPI backend `/v1` prefix. |

---

## 🎭 Mock Data Mode

The discovery engine includes a built-in **Mock Data Mode** enabled via `MOCK_DATA_MODE=true` in `backend/config.py` / `.env`.

### Benefits:
1. **Zero External API Costs**: Perform full development, testing, and UI reviews without consuming Gemini API tokens.
2. **Instant Offline Development**: Works seamlessly on airplanes, low-connectivity environments, or CI runners.
3. **Deterministic Results**: Uses scenario-specific keyword pattern matching to produce consistent failure categorizations, sentiment scores, and synthetic 768-dimensional embeddings.

To switch to production mode with live Gemini 1.5 Pro:
```env
MOCK_DATA_MODE=false
GEMINI_API_KEY=AIzaSy...your-gemini-key
DATABASE_URL=postgresql+asyncpg://postgres:password@ep-host.railway.app:5432/railway
```

---

## 🚢 Deployment Guide

### 1. Deploy Backend on Railway

1. **Create Railway Project**: Connect your GitHub repository to [Railway](https://railway.app).
2. **Add PostgreSQL with pgvector**:
   - In your Railway project, click **New** -> **Database** -> **Add PostgreSQL**.
   - Ensure the `vector` extension is enabled by connecting to the DB and executing: `CREATE EXTENSION IF NOT EXISTS vector;`.
3. **Deploy Backend Service**:
   - Set the root directory to `/backend` or use the provided `backend/Dockerfile`.
   - Set the start command: `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT`.
   - Configure environment variables in Railway:
     - `DATABASE_URL`: `${{Postgres.DATABASE_URL}}` (ensure protocol is `postgresql+asyncpg://`).
     - `GEMINI_API_KEY`: Your live Google AI Studio API key.
     - `JWT_SECRET_KEY`: A high-entropy 256-bit string (`openssl rand -hex 32`).
     - `MOCK_DATA_MODE`: `false`.
     - `ENVIRONMENT`: `production`.
     - `CORS_ORIGINS`: `https://your-frontend-domain.vercel.app`.

### 2. Deploy Frontend on Vercel

1. **Import Project into Vercel**: Connect your GitHub repository to [Vercel](https://vercel.com).
2. **Configure Build Settings**:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
3. **Set Environment Variables**:
   - `NEXT_PUBLIC_API_BASE_URL`: `https://your-railway-backend.up.railway.app/v1`
4. **Deploy**: Vercel handles automated branch previews and edge CDN caching.

---

## 🗄️ Database Migrations (Alembic)

The backend uses **Alembic** for asynchronous schema evolution and version tracking.

```bash
cd backend

# Apply all pending migrations to the database
alembic upgrade head

# Rollback the last migration
alembic downgrade -1

# Generate a new migration after editing models in backend/models/
alembic revision --autogenerate -m "add_new_feature_table"
```

---

## 🧪 Testing & Verification

The repository includes a comprehensive, automated test suite covering unit logic, integration flows, and end-to-end user lifecycles with **100% test pass rate** (109/109 tests passing, ≥75% code coverage).

### Running Backend Tests
```bash
cd backend

# Run all 109 backend tests
pytest tests/ -v

# Run with test coverage report
pytest tests/ --cov=backend --cov-report=term-missing

# Run the complete E2E smoke test
pytest tests/test_smoke_e2e.py -v
```

### Running Frontend Validation
```bash
cd frontend

# TypeScript strict type checking (0 errors)
node ./node_modules/typescript/bin/tsc --noEmit

# Production Next.js bundle compilation
npm run build
```

---

## 📖 Researcher & PM Onboarding

For detailed operational guidance on:
- Designing and running discovery research studies
- Formatting and uploading custom review datasets
- Interpreting the 9-dimension Opportunity Scoring Matrix
- Reviewing and validating low-confidence Gemini classifications
- Exporting publication-ready discovery briefs for leadership

👉 **Read the complete [Researcher & PM Onboarding Guide](file:///d:/3.%20Career/Product%20Management/IDE/Google%20Photos/docs/researcher_guide.md).**

---

## ⚠️ Known System Boundaries & Limitations

As documented in `docs/architecture.md §18`, the engine operates with the following intentional boundaries:

1. **Ingestion File Size Limits**:
   - Maximum CSV upload size is **50 MB** per batch (approx. 50,000 raw feedback records).
   - Datasets exceeding 50 MB should be split across multiple imports or ingested via streaming pipelines.
2. **Gemini Rate Limiting & Backoff**:
   - Live Gemini 1.5 Pro processing operates with exponential backoff and jitter. In high-throughput scenarios exceeding API tier quotas (e.g., >360 requests/minute), workers pause and can be resumed via the `/model-runs/{run_id}/resume` endpoint.
3. **Vector Similarity Fallbacks**:
   - In SQLite / Mock Mode, semantic search computes in-memory cosine similarities across 768-dimensional synthetic embeddings. In PostgreSQL production, HNSW / IVFFlat indexes in `pgvector` are utilized.
4. **Citation Integrity Guarantee**:
   - Every generated report claim is strictly validated against source record substrings. Hallucinated quotes that do not exist verbatim in the underlying dataset are automatically rejected.

---

## 🤝 Contributing Guidelines

1. **Branch Conventions**:
   - Feature branches: `feat/feature-name`
   - Bug fixes: `fix/issue-description`
   - Documentation & Tests: `docs/topic-name` or `test/topic-name`
2. **Pull Request Validation Checklist**:
   - [ ] All 109 backend tests pass (`pytest backend/tests`).
   - [ ] Code coverage remains ≥ 70%.
   - [ ] TypeScript compiler passes with 0 errors (`node ./node_modules/typescript/bin/tsc --noEmit`).
   - [ ] No plaintext secrets or API keys committed to Git.
   - [ ] PII scrubbers tested on any new data ingestion sources.
3. **Code Style**:
   - Python: Clean, asynchronous PEP 8 standards with type hints.
   - TypeScript/React: Functional components, TanStack Query hooks, CSS module tokens.

---

## 🛡️ License & Compliance

Built for the **Google Photos Core Experience Team**. All user reviews and survey data ingested into this engine must adhere to Google Privacy principles. PII (names, phone numbers, emails) is automatically sanitized at the ingestion boundary.
