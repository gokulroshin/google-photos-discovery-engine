# Context: AI-Powered Photo Retrieval Discovery Engine

> **Source:** Problem_Statement.docx
> **Implementation Stack:** Gemini LLM · Vercel (Frontend) · Railway (Backend)
> **Role:** Product Manager / User Researcher / AI Systems Architect -- Google Photos Core Experience Team

---

## 1. Background & Business Objective

Google Photos users accumulate thousands of photos, videos, screenshots, and visual memories over years. Retrieval is easy when users know metadata (date, location, album, keywords), but **breaks down when users remember the experience or visual memory without knowing the exact descriptor**.

**Examples of the core failure:**
- *I remember a small café we visited during our Goa trip, but I do not remember the date, café name, or album.*
- *I remember taking a picture of the medicine I used when I was sick last year, but I do not remember when I took it or the exact medicine name.*

**Strategic goal:** Increase the percentage of users who successfully retrieve a photo they remember but cannot precisely describe when they begin searching.

> **Scope:** This is NOT a general search-improvement project. Focus exclusively on retrieval failures caused by **incomplete, uncertain, contextual, episodic, or visually-based memory**.

---

## 2. Primary Product Problem

Users remember photos through **contextual, emotional, visual, or episodic** information rather than structured metadata. They may recall a person, place, event, object, approximate time period, purpose, or experience -- while forgetting exact dates, locations, album names, text, filenames, or searchable keywords.

This creates a gap between **human memory representation** and the **retrieval mechanisms** supported by the product. The discovery engine must investigate this gap using evidence from real users, not assumptions.

---

## 3. Project Objectives

| # | Objective |
|---|-----------|
| 1 | Collect publicly available discussions related to photo retrieval |
| 2 | Identify user experiences involving difficulty retrieving old or remembered photos |
| 3 | Separate retrieval problems from general Google Photos complaints |
| 4 | Extract the memory cues users rely on and the information they lack |
| 5 | Analyze search strategies and workarounds users attempt |
| 6 | Cluster distinct retrieval failure patterns |
| 7 | Compare problem areas using transparent, evidence-based criteria |
| 8 | Produce traceable insights, user segments, and opportunity areas for further validation |

---

## 4. Technology Architecture

### 4.1 LLM: Google Gemini
- Primary model for classification, extraction, clustering, summarization, synthesis, and research assistance
- Accessed via **secure server-side API calls** (never exposed in frontend)
- Prompts as modular, version-controlled templates
- Structured JSON outputs with confidence scores, evidence references, and uncertainty fields
- Retry handling, rate-limit handling, and graceful fallback for malformed responses
- **Never fabricate** user quotes, URLs, evidence counts, or findings

### 4.2 Frontend: Vercel + Next.js (TypeScript)
- Clean, professional research dashboard for Product Managers and User Researchers
- Responsive for desktop and tablet
- Modular, reusable components
- Loading states, empty states, error states, and progress indicators
- No secrets, scraping credentials, or privileged backend logic in frontend code

### 4.3 Backend: Railway + Python/FastAPI
- Handles data ingestion, preprocessing, storage, Gemini API calls, analysis workflows, and API endpoints
- All secrets via environment variables
- Structured logging, error handling, health checks, and background processing
- Ingestion/analysis jobs do not block UI requests
- Authenticated/protected endpoints for sensitive operations

### 4.4 Supporting Components
| Component | Purpose |
|-----------|---------|
| PostgreSQL | Source records, extracted attributes, analysis outputs, job status |
| Vector DB / pgvector | Semantic retrieval and RAG (optional) |
| Object storage | Imported datasets |
| Source adapter architecture | Plug-in new sources without rewriting the system |

---

## 5. Data Sources

All data must be **publicly available** and comply with each platform's terms of service, privacy requirements, and robots policies.

- Google Play Store reviews for Google Photos
- Apple App Store reviews for Google Photos
- Reddit discussions and relevant communities
- Google Photos Help Community and support discussions
- Public social media conversations
- YouTube comments on Google Photos-related videos
- Public technology forums, blogs, and discussion threads

> Where automated access is restricted, support **manual upload or structured import** of legally obtained data. Always preserve source URLs, dates, platform information, and collection metadata.

---

## 6. Discovery Engine Workflow

`
Define research questions
        ↓
Generate targeted search queries (Gemini + query templates)
        ↓
Collect / import source content (approved methods)
        ↓
Normalize and deduplicate records
        ↓
Classify content for relevance (incomplete-memory retrieval)
        ↓
Extract retrieval scenarios, memory cues, missing info, search behavior, outcomes
        ↓
Embed / index relevant content (semantic retrieval)
        ↓
Cluster related retrieval problems
        ↓
Compare problem areas (transparent evidence-based dimensions)
        ↓
Generate research reports, dashboards, and exportable datasets
        ↓
Allow inspection of evidence behind every major insight
`

---

## 7. Core Research Framework

### 7.1 Retrieval Scenarios
Travel photos · Restaurant/café photos · Screenshots · Medical/health documents · Receipts · Academic documents · Work images · People · Events · Products · Memes · Other personal memories
*(Allow new categories to emerge from data)*

### 7.2 Memory Cues (what the user remembers)
- Person
- Place
- Approximate time
- Event or activity
- Object
- Visual appearance
- Text visible in the image
- Emotional or social context
- Purpose of capturing or saving the image
- Source of the image (camera, download, screenshot, shared media)

### 7.3 Missing or Uncertain Information
What the user has forgotten, never knew, cannot specify accurately, or believes may be missing from the system. *(Do not infer when the source does not state it.)*

### 7.4 Search Behavior
Initial queries · Query reformulations · Natural-language searches · Keyword searches · Timeline browsing · Album browsing · Screenshot/document searches · Use of external tools · Requests for help · Abandonment
*(If exact query unavailable, mark as unknown)*

### 7.5 Retrieval Outcomes
| Outcome | Description |
|---------|-------------|
| Successfully retrieved | Found on first attempt |
| Retrieved after multiple attempts | Eventually found |
| Retrieved through manual browsing | Scrolled to find |
| Retrieved via alternative method | External tool, shared link, etc. |
| Not retrieved | Could not find |
| Abandoned | Gave up searching |
| Unclear | Outcome not stated |

### 7.6 Failure Points
1. User cannot translate memory into search terms
2. System does not understand contextual or natural-language descriptions
3. User remembers only approximate information
4. Metadata is inaccurate or missing
5. Image content is not recognized
6. Results are too broad or irrelevant
7. Relevant results are omitted
8. User does not know which search capability to use
9. User cannot distinguish between captured, downloaded, and screenshotted content
10. Large libraries create browsing overload
11. User does not know how to refine the search
12. User loses confidence and abandons the attempt

---

## 8. AI Classification & Extraction (per source item)

| Field | Description |
|-------|-------------|
| Relevance label(s) | Why this item is relevant |
| Retrieval scenario | Type of photo/memory |
| Memory cues | What the user remembers |
| Missing or uncertain information | What they forgot/lack |
| Search behavior | How they tried to find it |
| Retrieval outcome | Result of the attempt |
| Failure point(s) | Where the retrieval broke down |
| User segment | Who the user is |
| Evidence excerpt | Direct quote from source |
| Confidence score | Model confidence (0-1) |
| Rationale | Why this classification was assigned |
| Source identifier and URL | Traceability link |

- Support **multi-label classification**
- Store original source text separately from generated fields
- Use **deterministic validation** after each Gemini response
- Flag records requiring human review

---

## 9. Retrieval Problem Taxonomy

Build an evidence-based taxonomy of distinct retrieval problems. For every category provide:

- Problem name and definition
- User situation or segment
- Memory cues involved
- Missing information
- Common search behavior
- Failure mechanism
- Evidence count
- Source diversity
- Representative excerpts
- Confidence level
- Open questions and validation needs
- Potential product implications *(without prescribing a final solution)*

---

## 10. Opportunity Area Comparison Framework

Compare opportunity areas transparently. **Do not rank by mention count alone.**

| Dimension | Notes |
|-----------|-------|
| Evidence frequency | How often does this appear? |
| Evidence diversity across platforms | Does it appear in multiple sources? |
| User impact | How severe is the frustration? |
| Retrieval failure or abandonment | Does it lead to giving up? |
| Availability of current workarounds | Can users solve it another way? |
| Strategic relevance | Is it on-scope for incomplete-memory retrieval? |
| Problem clarity | Is the problem well-defined? |
| Potential reach | How many users are affected? |
| Validation effort required | How hard to validate further? |

> If scores are used: define the scoring methodology, show underlying evidence, and separate **observed data** from **analyst judgment**. Researcher makes the final decision.

---

## 11. Evidence Quality & Research Integrity

- Every major insight must link to supporting source items
- Preserve original URLs and timestamps whenever available
- Display excerpts without unnecessary personal information
- Show source count and source diversity
- Identify contradictory or alternative evidence
- Label confidence and limitations
- Distinguish: **direct evidence → observed patterns → interpretations → hypotheses → opportunities**
- **Never fabricate** quotes, sources, evidence counts, or user motivations
- Do not treat model confidence as statistical certainty
- Allow human review and correction of AI-generated classifications

---

## 12. Frontend Dashboard Views

| View | Contents |
|------|----------|
| Overview | Total records, relevant records, sources, processing status, problem categories |
| Data Explorer | Filter by source, date, relevance, scenario, segment, outcome, confidence |
| Evidence Viewer | Original content, source metadata, extracted fields, Gemini rationale |
| Problem Taxonomy | Definitions, evidence counts, examples, unresolved questions |
| Opportunity Comparison | Configurable dimensions, transparent scoring details |
| Search & Discovery | Semantic search for related evidence |
| Research Report | Export or present findings |
| Human Review Queue | Low-confidence or conflicting records |
| Job Monitoring | Ingestion → preprocessing → Gemini processing → clustering → report generation |

> Interface priority: **clarity, traceability, and research usability** over decorative complexity.

---

## 13. Backend API Endpoints

- Create and manage research projects
- Upload or import datasets
- Start ingestion and analysis jobs
- Check job status and errors
- List and filter source records
- Retrieve individual evidence records
- Run classification and extraction
- Generate clusters and taxonomy categories
- Compare opportunity areas
- Generate reports and export structured data

**Data model entities:** source records · extracted evidence · classifications · taxonomy categories · opportunity areas · model runs · human review decisions

---

## 14. Research Questions to Answer

1. What kinds of old photos do users struggle to retrieve?
2. What information do users remember most frequently?
3. What information do users most frequently forget?
4. Do users remember experiences more often than metadata?
5. Which memories are difficult to express as search queries?
6. How do users formulate initial searches?
7. How do users modify queries after failure?
8. Do users use natural language, keywords, dates, locations, or visual descriptors?
9. Which retrieval scenarios lead to repeated attempts or abandonment?
10. What workarounds do users use outside Google Photos?
11. Which problems occur across multiple sources?
12. Which problems appear severe but lack sufficient evidence?
13. Which opportunity areas require additional primary research?

---

## 15. Security, Privacy & Compliance

- Never expose Gemini API keys or secrets in frontend code
- Use environment variables and secure deployment configuration
- Do not collect unnecessary PII
- Anonymize usernames and personal references where possible
- Respect source terms of service and access restrictions
- Store source URLs and provenance for auditability
- Implement authentication and authorization for administrative workflows
- Avoid using private, leaked, or restricted user data
- Provide clear handling for deletion, correction, and data retention

---

## 16. Expected Deliverables

| # | Deliverable |
|---|-------------|
| 1 | Working Vercel frontend dashboard |
| 2 | Railway-hosted backend service |
| 3 | Gemini-powered classification and extraction pipeline |
| 4 | Data ingestion and import workflow |
| 5 | Structured database schema |
| 6 | Evidence explorer with source traceability |
| 7 | Retrieval problem taxonomy |
| 8 | Opportunity comparison framework |
| 9 | Research report generation and export |
| 10 | README (architecture, setup, env vars, deployment, limitations) |
| 11 | Sample dataset / mock data mode for testing without external APIs |
| 12 | Basic test coverage for core backend services and data validation |

---

## 17. Implementation Principles

1. **MVP first** -- start with a functional minimum viable discovery engine before adding advanced features
2. **Modular architecture** -- data sources, models, and analysis methods must be replaceable or extensible
3. **Evidence-first** -- use Gemini for reasoning/synthesis, but preserve raw evidence and validate structured outputs
4. **Transparent trails** -- prefer traceable evidence over polished but unsupported insights
5. **Explicit assumptions** -- make all assumptions visible
6. **Human-in-the-loop** -- use human review for low-confidence classifications and major conclusions
7. **No premature solutions** -- do not propose a final product solution until discovery identifies a sufficiently supported problem
8. **Resilient design** -- system must remain usable even when some data sources or APIs are unavailable
9. **Maintainability & observability** -- design for safe credential handling and operational visibility
10. **Documented limitations** -- note source coverage gaps, sampling bias, language bias, and platform bias

---

## 18. Final Directive

> Build the project as a **production-oriented research prototype** using Gemini as the LLM, Vercel for the frontend, and Railway for the backend.
>
> **Sequence:** Create architecture and implementation plan → scaffold the project → implement data model and backend APIs → connect Gemini via secure server-side calls → build the frontend research dashboard.
>
> **Do not** jump directly to a product feature recommendation. The output must be a **reliable, evidence-backed discovery system** that helps a Product Manager understand incomplete-memory photo retrieval problems and compare opportunity areas before deciding what to build.
>
> When implementation choices are ambiguous: choose the **simplest maintainable approach**, document the decision, and keep the architecture extensible.