import pytest
import uuid
import io
import csv
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.tests.conftest import TestAsyncSessionLocal
from backend.workers.analysis_worker import AnalysisWorker


@pytest.mark.asyncio
async def test_full_discovery_engine_e2e_workflow(
    client: AsyncClient,
    admin_headers: dict,
    researcher_headers: dict,
):
    """
    Comprehensive End-to-End Smoke Test simulating a Product Manager's complete research journey:
    1. Project Creation
    2. CSV Dataset Ingestion & Preprocessing & Deduplication
    3. Gemini Classification Pipeline Execution
    4. Evidence Retrieval & Semantic Search
    5. Taxonomy Generation & Validation
    6. Opportunity Area Scoring on 9 Dimensions
    7. Grounded Research Report Synthesis
    8. CSV/JSON Data Exports
    9. Project Storage Usage Inspection
    """

    # -------------------------------------------------------------
    # 1. Create Research Project
    # -------------------------------------------------------------
    proj_payload = {
        "name": f"E2E Discovery Workflow Project {uuid.uuid4().hex[:6]}",
        "description": "End-to-end smoke test validating the complete discovery workflow.",
        "research_questions": [
            "What visual cues fail in multi-object search?",
            "What is the abandonment rate for blurry document photos?",
        ],
    }
    res_proj = await client.post("/v1/projects", json=proj_payload, headers=admin_headers)
    assert res_proj.status_code == 201
    project_data = res_proj.json()
    project_id = project_data["id"]
    assert project_data["name"] == proj_payload["name"]

    # -------------------------------------------------------------
    # 2. Upload CSV Dataset (12 diverse user reviews)
    # -------------------------------------------------------------
    csv_rows = [
        ["raw_content", "source_url", "source_date", "source_platform", "author_handle"],
        ["I searched for my dog wearing a yellow raincoat in Chicago back in 2021, but typing 'yellow raincoat dog' brought up hundreds of random outdoor shots and missed the exact one.", "https://play.google.com/review_1", "2024-03-10", "play_store", "alice_smith"],
        ["Search used to work better. Now I type 'receipt from Home Depot' and it shows me pictures of trees and screenshots of maps.", "https://play.google.com/review_2", "2024-03-11", "play_store", "bob_jones"],
        ["Why is Google Photos search so bad with partial memories? I know I took a picture of a receipt on a glass coffee table in Seattle, but without the exact store name or date, search gave up after showing 2 unrelated coffee cups.", "https://reddit.com/r/googlephotos/post_3", "2024-03-12", "reddit", "reddit_user_3"],
        ["Impossible to find old car lease documents I photographed 3 years ago because optical character recognition completely missed the blurry vehicle identification number.", "https://apps.apple.com/review_4", "2024-03-13", "app_store", "ios_user_4"],
        ["Face Recognition grouped distant cousin with stranger. I am trying to retrieve all photos of my cousin's wedding in Austin, but face clustering mixed up people and search by person returns hundreds of erroneous images.", "https://support.google.com/photos/thread_5", "2024-03-14", "forum", "community_user_5"],
        ["Searched 'white boat blue sails' because I took a photo during our vacation in Greece. It showed me pictures of blue sky and white snow back home in Ohio.", "https://youtube.com/comment_6", "2024-03-15", "youtube", "yt_user_6"],
        ["Trying to find my daughter's first steps video in 2019 wearing a red polka-dot onesie near our golden retriever. Search failed completely.", "https://reddit.com/r/googlephotos/post_7", "2024-03-16", "reddit", "family_dad"],
        ["Can't find pictures by describing what happened. I remember my kid blew out birthday candles next to a blue banner, but typing 'birthday candles blue banner' gives 0 results.", "https://play.google.com/review_8", "2024-03-17", "play_store", "mom_user_8"],
        ["I don't remember the exact month I visited the Grand Canyon, only that it was snowy and sunset. Google Photos makes me scroll through 4 years of photos.", "https://play.google.com/review_9", "2024-03-18", "play_store", "traveler_9"],
        ["When I search for 'concert with purple lights', it gives me photos of flowers. I spent 45 minutes manually scrolling through 10,000 photos.", "https://apps.apple.com/review_10", "2024-03-19", "app_store", "music_fan_10"],
        ["The search doesn't understand context. I wanted photos of my wife wearing her graduation gown, but searching 'graduation' gave me every friend's graduation ceremony instead.", "https://apps.apple.com/review_11", "2024-03-20", "app_store", "alumni_11"],
        ["The worst part is when you know a photo exists from 5 years ago, you search 10 different combinations of words, nothing shows up, and then you stumble upon it by accident under the wrong date.", "https://youtube.com/comment_12", "2024-03-21", "youtube", "yt_commenter_12"],
    ]
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerows(csv_rows)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    res_import = await client.post(
        f"/v1/projects/{project_id}/import",
        files={"file": ("dataset.csv", csv_bytes, "text/csv")},
        headers=researcher_headers,
    )
    if res_import.status_code != 200:
        print("IMPORT ERROR DETAIL:", res_import.json())
    assert res_import.status_code == 200
    import_data = res_import.json()
    assert import_data["records_accepted"] == 12
    assert import_data["records_failed"] == 0

    # -------------------------------------------------------------
    # 3. Trigger Classification Run & Execute Analysis Worker
    # -------------------------------------------------------------
    res_run = await client.post(
        f"/v1/projects/{project_id}/analyze",
        headers=researcher_headers,
    )
    assert res_run.status_code == 201
    run_id = res_run.json()["id"]

    # Execute analysis worker in background pipeline
    await AnalysisWorker.run_analysis_job(run_id, session_factory=TestAsyncSessionLocal)

    # Verify model run completion
    res_run_status = await client.get(
        f"/v1/projects/{project_id}/model-runs/{run_id}",
        headers=researcher_headers,
    )
    assert res_run_status.status_code == 200
    assert res_run_status.json()["status"] == "completed"
    assert res_run_status.json()["records_success"] == 12

    # -------------------------------------------------------------
    # 4. Query Evidence Records & Semantic Vector Search
    # -------------------------------------------------------------
    res_evidence = await client.get(
        f"/v1/projects/{project_id}/evidence",
        params={"page": 1, "page_size": 20},
        headers=researcher_headers,
    )
    assert res_evidence.status_code == 200
    evidence_list = res_evidence.json()
    assert evidence_list["total"] == 12

    # Perform semantic search for episodic recollection query
    res_search = await client.get(
        f"/v1/projects/{project_id}/evidence/search",
        params={"q": "dog in yellow raincoat in Chicago"},
        headers=researcher_headers,
    )
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert len(search_data["items"]) > 0

    # -------------------------------------------------------------
    # 5. Generate Problem Taxonomy
    # -------------------------------------------------------------
    res_tax = await client.post(
        f"/v1/projects/{project_id}/taxonomy/generate",
        headers=researcher_headers,
    )
    assert res_tax.status_code == 200
    taxonomy_data = res_tax.json()
    assert len(taxonomy_data["items"]) >= 1

    # -------------------------------------------------------------
    # 6. Generate Opportunity Areas
    # -------------------------------------------------------------
    res_opps = await client.post(
        f"/v1/projects/{project_id}/opportunities",
        headers=researcher_headers,
    )
    assert res_opps.status_code == 201
    opps_data = res_opps.json()
    assert len(opps_data["items"]) >= 1
    assert "user_impact_score" in opps_data["items"][0]
    assert "abandonment_rate" in opps_data["items"][0]

    # -------------------------------------------------------------
    # 7. Synthesize Grounded Research Report
    # -------------------------------------------------------------
    res_report = await client.post(
        f"/v1/projects/{project_id}/reports",
        headers=researcher_headers,
    )
    assert res_report.status_code == 200
    report_data = res_report.json()
    assert "id" in report_data
    assert report_data["evidence_count"] >= 10
    assert len(report_data["markdown"]) > 100

    # -------------------------------------------------------------
    # 8. Export Evidence & Taxonomy CSV / JSON
    # -------------------------------------------------------------
    res_exp_csv = await client.get(
        f"/v1/projects/{project_id}/export/evidence",
        params={"format": "csv"},
        headers=researcher_headers,
    )
    assert res_exp_csv.status_code == 200
    assert res_exp_csv.headers["content-type"].startswith("text/csv")
    assert "author_handle" in res_exp_csv.text

    res_exp_tax = await client.get(
        f"/v1/projects/{project_id}/export/taxonomy",
        params={"format": "json"},
        headers=researcher_headers,
    )
    assert res_exp_tax.status_code == 200
    assert isinstance(res_exp_tax.json(), list)

    # -------------------------------------------------------------
    # 9. Verify Project Storage Utilization Breakdown
    # -------------------------------------------------------------
    res_storage = await client.get(
        f"/v1/projects/{project_id}/storage",
        headers=researcher_headers,
    )
    assert res_storage.status_code == 200
    storage_info = res_storage.json()
    assert storage_info["project_id"] == project_id
    assert storage_info["total_bytes"] > 0
    assert storage_info["breakdown"]["source_records"]["count"] == 12
    assert storage_info["breakdown"]["evidence_records"]["count"] == 12
    assert storage_info["breakdown"]["reports"]["count"] >= 1
