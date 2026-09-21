import pytest
from pydantic import ValidationError
from backend.gemini.schemas import (
    RelevanceFilterOutput,
    EvidenceExtraction,
    RetrievalOutcome,
    MemoryCues,
    TaxonomyClusterOutput,
    OpportunityScoreOutput,
)


def test_relevance_filter_schema_valid():
    data = {
        "is_relevant": True,
        "confidence": 0.88,
        "rationale": "Clear photo retrieval memory cue failure",
        "is_genuine_experience": True,
        "tone_flags": ["frustration", "user_complaint"],
    }
    obj = RelevanceFilterOutput.model_validate(data)
    assert obj.is_relevant is True
    assert obj.confidence == 0.88
    assert obj.is_genuine_experience is True
    assert "frustration" in obj.tone_flags


def test_relevance_filter_schema_out_of_range_confidence():
    with pytest.raises(ValidationError):
        RelevanceFilterOutput(
            is_relevant=True,
            confidence=1.5,  # Must be between 0.0 and 1.0
            rationale="Test out of range",
        )

    with pytest.raises(ValidationError):
        RelevanceFilterOutput(
            is_relevant=True,
            confidence=-0.1,  # Must be between 0.0 and 1.0
            rationale="Test negative",
        )


def test_memory_cues_schema_partial():
    cues = MemoryCues(place="Paris", visual="red dress at sunset")
    assert cues.place == "Paris"
    assert cues.visual == "red dress at sunset"
    assert cues.person is None
    assert cues.time is None


def test_evidence_extraction_valid():
    data = {
        "relevance_labels": ["vague_visual_memory", "missing_temporal_context"],
        "retrieval_scenario": "User searching for vacation photo in Greece",
        "memory_cues": {"place": "Greece", "visual": "white boat with blue sails"},
        "missing_information": "Exact calendar date or geotag",
        "search_behavior": "Entered multi-word keyword query",
        "retrieval_outcome": "abandoned",
        "failure_points": ["Visual tagger missed boat color", "No episodic semantic matching"],
        "user_segment": "casual_photographer",
        "evidence_excerpt": "Searched 'white boat blue sails' because I took a photo during our vacation in Greece",
        "confidence_score": 0.92,
        "rationale": "High confidence extraction based on verbatim user quote",
        "is_genuine_experience": True,
    }
    extracted = EvidenceExtraction.model_validate(data)
    assert extracted.retrieval_outcome == RetrievalOutcome.ABANDONED
    assert extracted.confidence_score == 0.92
    assert len(extracted.failure_points) == 2


def test_evidence_extraction_invalid_outcome():
    with pytest.raises(ValidationError):
        EvidenceExtraction(
            retrieval_scenario="Test scenario",
            retrieval_outcome="unsupported_outcome_type",
            confidence_score=0.8,
            rationale="Test",
        )


def test_taxonomy_cluster_schema_validation():
    data = {
        "name": "Episodic Recollection Mismatches",
        "definition": "Users recall narrative aspects of photos instead of searchable metadata tags.",
        "user_segment": "Casual family photographers",
        "common_memory_cues": {"visual": "clothing color", "event": "vacations"},
        "missing_information": "Filenames and calendar dates",
        "common_search_behavior": "Iterative keyword rephrasing",
        "failure_mechanism": "System tags image objects in isolation rather than relationship scenes.",
        "representative_excerpts": ["I searched for yellow raincoat dog in Chicago"],
        "open_questions": ["How can conversational queries disambiguate scenes?"],
        "product_implications": "Requires conversational retrieval interface.",
    }
    cluster = TaxonomyClusterOutput.model_validate(data)
    assert cluster.name == "Episodic Recollection Mismatches"
    assert len(cluster.representative_excerpts) == 1


def test_opportunity_score_schema_validation():
    data = {
        "user_impact_score": 8.5,
        "abandonment_rate": 0.40,
        "workaround_exists": True,
        "strategic_relevance": 9.0,
        "problem_clarity": 8.0,
        "potential_reach": "High mobile reach",
        "validation_effort": "medium",
        "scoring_methodology": "Derived from high abandonment rates and lack of workarounds.",
    }
    score = OpportunityScoreOutput.model_validate(data)
    assert score.user_impact_score == 8.5
    assert score.abandonment_rate == 0.40
    assert score.validation_effort == "medium"
