import pytest
from backend.gemini.prompts import render_prompt


def test_render_relevance_filter_prompt():
    rendered = render_prompt("relevance_filter", raw_content="I can't find photos of my dog in Chicago.")
    assert "You are an expert research analyst" in rendered
    assert "I can't find photos of my dog in Chicago." in rendered
    assert "<source_text>" in rendered
    assert "</source_text>" in rendered


def test_render_extraction_prompt():
    rendered = render_prompt("extraction", raw_content="Searched for birthday cake blue banner.")
    assert "Extract ONLY what is explicitly stated" in rendered
    assert "Searched for birthday cake blue banner." in rendered
    assert "evidence_excerpt" in rendered


def test_render_taxonomy_cluster_prompt():
    records = [
        {
            "retrieval_scenario": "Cannot find receipt",
            "evidence_excerpt": "receipt OCR failed",
            "failure_points": ["OCR missing"],
            "memory_cues": {"text": "receipt"},
        }
    ]
    rendered = render_prompt("taxonomy_cluster", records=records)
    assert "Principal Product Manager" in rendered
    assert "receipt OCR failed" in rendered


def test_render_opportunity_score_prompt():
    rendered = render_prompt(
        "opportunity_score",
        category_name="Vague Visual Memory",
        definition="User remembers only colors and visual vibe",
        evidence_count=24,
        source_diversity={"reddit": 14, "play_store": 10},
        failure_mechanism="Semantic tag mismatch",
    )
    assert "Vague Visual Memory" in rendered
    assert "user_impact_score" in rendered


def test_render_query_generation_prompt():
    rendered = render_prompt(
        "query_generation",
        retrieval_scenario="Looking for wedding dance",
        memory_cues={"event": "wedding", "person": "bride"},
        missing_information="Date",
    )
    assert "Looking for wedding dance" in rendered
    assert "queries" in rendered


def test_render_summary_synthesis_prompt():
    rendered = render_prompt(
        "summary_synthesis",
        project_name="Core Retrieval Study",
        total_evidence=50,
        categories=[{"name": "Temporal Amnesia", "evidence_count": 20, "definition": "Forgotten dates", "representative_excerpts": ["forgot 2019"]}],
    )
    assert "Core Retrieval Study" in rendered
    assert "Temporal Amnesia" in rendered
