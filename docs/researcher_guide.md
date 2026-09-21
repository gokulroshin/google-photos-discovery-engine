# Researcher Onboarding Guide: AI-Powered Photo Retrieval Discovery Engine

> **Audience:** Product Managers, UX Researchers, and Data Analysts on the Google Photos Core Experience Team.  
> **Purpose:** Step-by-step operational guide to conducting evidence-backed user discovery, classifying photo retrieval failure modes, evaluating opportunity areas, and exporting grounded research reports.

---

## Table of Contents

1. [Introduction & Core Philosophy](#1-introduction--core-philosophy)
2. [Step 1: Creating a Research Project](#2-step-1-creating-a-research-project)
3. [Step 2: Uploading & Ingesting User Feedback](#3-step-2-uploading--ingesting-user-feedback)
4. [Step 3: Running the Gemini Classification Pipeline](#4-step-3-running-the-gemini-classification-pipeline)
5. [Step 4: Managing the Human Review Queue](#5-step-4-managing-the-human-review-queue)
6. [Step 5: Understanding & Calibrating Confidence Scores](#6-step-5-understanding--calibrating-confidence-scores)
7. [Step 6: Exploring Problem Taxonomy & Opportunity Comparison](#7-step-6-exploring-problem-taxonomy--opportunity-comparison)
8. [Step 7: Synthesizing & Exporting Research Reports](#8-step-7-synthesizing--exporting-research-reports)
9. [FAQ & Troubleshooting](#9-faq--troubleshooting)

---

## 1. Introduction & Core Philosophy

The **AI-Powered Photo Retrieval Discovery Engine** is designed to surface and organize **evidence of user retrieval failures** driven by incomplete, uncertain, or episodic human memory.

### Core Tenets for Researchers:
- **Evidence-First, Never Fabricate:** The system never invents user pain points. Every category, opportunity score, and report claim must link back to a verified, verbatim excerpt from real user feedback.
- **Discovery, Not Solution Engineering:** The engine identifies *where* and *why* retrieval breaks down; it does not dictate the machine learning architecture or UI redesign.
- **Human-in-the-Loop Oversight:** AI classifications below standard confidence thresholds (0.70) are flagged for human review.

---

## 2. Step 1: Creating a Research Project

1. Log into the research dashboard (select your assigned role: `Researcher` or `PM Lead Admin`).
2. Navigate to **Projects** and click **"+ New Project"**.
3. Fill out the project creation form:
   - **Project Name:** e.g., *"Q3 Core Retrieval Memory Gap Analysis"*
   - **Description:** Outline the research goal and context.
   - **Research Questions:** Add 2–5 structured research inquiries (e.g., *"What episodic cues do users recall when searching for receipts or documents?"*).
4. Click **Create Project**. You will be redirected to the project Overview dashboard.

---

## 3. Step 2: Uploading & Ingesting User Feedback

You can ingest data via **Manual Upload (CSV/JSON)** or **Automated Platform Adapters**.

### Option A: Manual Dataset Import (Recommended for Curated Data)
1. On the project dashboard, go to the **Data Explorer** view and click **"Import Dataset"**.
2. Prepare your CSV or JSON file.

#### CSV Format Requirements:
| Column Header | Required? | Description / Example |
| :--- | :--- | :--- |
| `raw_content` | **Yes** | Full verbatim user review or forum post text. |
| `source_url` | **Yes** | Direct link to original post (or thread identifier). |
| `source_date` | **Yes** | ISO-8601 or standard date (e.g. `2024-03-15`). |
| `source_platform` | **Yes** | `play_store`, `app_store`, `reddit`, `youtube`, `forum`, or `survey`. |
| `author_handle` | Optional | User handle (automatically pseudonymized to `user_xxxxxx` at ingest). |
| `metadata` | Optional | JSON string of additional attributes (e.g., `{"rating": 1}`). |

3. Upload the file (up to 100MB per batch). The system automatically:
   - Strips dangerous HTML tags and normalizes whitespace.
   - Detects the text language (flags non-English content).
   - Computes a SHA-256 fingerprint to deduplicate identical content.
   - Replaces user identifiers with privacy-compliant pseudonyms.

### Option B: Automated Platform Adapters
1. Go to **Job Monitoring** (`/jobs`) and click **"New Ingestion Job"**.
2. Select the target source (`Google Play Store`, `Apple App Store`, `Reddit`, `YouTube`, `Support Forums`).
3. Configure query parameters, date ranges, or limit caps.
4. Click **Launch Job**. Progress and heartbeat metrics update live every 5 seconds.

---

## 4. Step 3: Running the Gemini Classification Pipeline

Once source records are ingested:
1. Navigate to the project **Overview** or **Evidence Viewer** and click **"Run Analysis"**.
2. The pipeline executes two stages asynchronously:
   - **Stage 1 (Relevance Filter):** Evaluates if the post represents a genuine user retrieval friction due to memory gaps (excluding app crashes, billing complaints, or spam).
   - **Stage 2 (Structured Extraction):** Extracts structured dimensions:
     - `retrieval_scenario` (e.g., *Searching for pet in winter clothing*)
     - `memory_cues` (Visual, Temporal, Spatial, Object, Text, Emotional)
     - `missing_information` (Exact date, album name, camera tag)
     - `search_behavior` (Keyword trial, timeline scroll)
     - `retrieval_outcome` (`abandoned`, `found_after_effort`, `found_by_accident`, `workaround_used`)
     - `failure_points` (Specific breakdown reasons)
     - `evidence_excerpt` (Verbatim substring quote)
     - `confidence_score` (0.00 – 1.00)
3. 768-dimensional text embeddings (`text-embedding-004`) are generated for semantic similarity matching.

---

## 5. Step 4: Managing the Human Review Queue

Records with model confidence below **0.70**, or where an extracted excerpt required validation, are automatically routed to the **Human Review Queue** (`/review`).

### Review Actions:
- **Approve:** Confirms the AI classification is accurate.
- **Correct:** Opens an inline editing modal allowing you to update any of the 12 extracted fields (e.g., adjusting retrieval scenario or outcome).
- **Reject:** Marks the record as non-relevant to photo retrieval failures.
- **Bulk Approve:** Select multiple high-confidence reviewed items to approve simultaneously.

---

## 6. Step 5: Understanding & Calibrating Confidence Scores

> [!IMPORTANT]
> **Confidence scores are model self-evaluations, not statistical probabilities.**

- **Green (> 0.70):** High confidence. The model identified explicit memory cues and clear retrieval intent directly from the text.
- **Amber (0.50 – 0.70):** Moderate confidence. Text is ambiguous or lacks explicit detail; routed to Human Review queue.
- **Red (< 0.50):** Low confidence or borderline relevance; requires mandatory researcher review before inclusion in reports.

---

## 7. Step 6: Exploring Problem Taxonomy & Opportunity Comparison

### Problem Taxonomy (`/taxonomy`)
- Displays clustered problem categories (e.g., *Incomplete Contextual & Visual Memory*, *OCR & Document Scene Misclassification*).
- Each category shows total evidence count, unique author count, and source platform diversity.
- Click any category to inspect representative verbatim excerpts, failure mechanisms, and open research questions.
- **Category Merging (Admin Only):** Merge overlapping categories into a unified cluster.

### Opportunity Comparison Matrix (`/opportunities`)
- Evaluates problem areas across 9 structured dimensions:
  1. **Evidence Frequency:** Number of supporting evidence items.
  2. **Evidence Diversity:** Spread across Play Store, App Store, Reddit, etc.
  3. **Unique Author Count:** Deduplicated contributors.
  4. **User Impact Score (0–10):** Severity of user friction.
  5. **Abandonment Rate (%):** Fraction of attempts ending in search failure.
  6. **Workaround Exists:** Whether users have accessible manual alternatives.
  7. **Strategic Relevance (0–10):** Alignment with Core Photos retrieval mission.
  8. **Problem Clarity (0–10):** How well-defined the problem is.
  9. **Validation Effort:** `low`, `medium`, or `high`.
- Click any cell to inspect the mathematical methodology and underlying evidence records.
- Researchers can override scores with mandatory `analyst_notes`.

---

## 8. Step 7: Synthesizing & Exporting Research Reports

### Generating a Synthesis Report (`/report`)
1. Ensure the project has at least 10 classified evidence records.
2. Click **"Generate Report"**.
3. Gemini synthesizes a comprehensive research document grounded in the taxonomy and evidence base.
4. Every claim is validated against existing source record IDs. Unsubstantiated claims are flagged with `[UNSUPPORTED — VERIFY]`.

### Exporting Data (`/explorer` & `/export`)
- **CSV Export:** Formatted with UTF-8 BOM for Microsoft Excel compatibility, full quoting, and pseudonymized author handles (`user_xxxxxxxx`).
- **JSON Export:** Structured JSON schema containing all extracted metadata, memory cues, and scoring rationale.

---

## 9. FAQ & Troubleshooting

### Q1: What should I do if the Gemini API is rate-limited or temporarily unavailable?
The engine uses built-in exponential backoff (1s, 2s, 4s). If an outage persists, analysis workers pause automatically without data loss. Once connectivity is restored, click **"Resume Job"** in Job Monitoring.

### Q2: Why was my CSV upload rejected?
Check that all 4 required columns (`raw_content`, `source_url`, `source_date`, `source_platform`) are present in the header row. Ensure the file encoding is UTF-8.

### Q3: How are duplicate posts handled?
If a user posts identical text to multiple subreddits or review sites, the deduplication engine retains the first instance and links additional URLs in `metadata.alternate_urls`.

### Q4: Can I search evidence using natural language?
Yes! Use the **Semantic Search** view (`/search`). Enter queries like *"can't find dog wearing sweater"* or *"receipt on table in Seattle"* to perform cosine similarity searches over 768-dimensional embeddings.

---

*For further technical details, see [`architecture.md`](file:///d:/3.%20Career/Product%20Management/IDE/Google%20Photos/docs/architecture.md) and [`edge_case.md`](file:///d:/3.%20Career/Product%20Management/IDE/Google%20Photos/docs/edge_case.md).*
