import pytest
from unittest.mock import patch, MagicMock
from backend.gemini.client import GeminiClient, GeminiUnavailableError
from backend.gemini.schemas import (
    RelevanceFilterOutput,
    EvidenceExtraction,
    RetrievalOutcome,
    validate_excerpt_in_content,
)


@pytest.mark.asyncio
async def test_gemini_mock_relevance_filtering():
    client = GeminiClient()
    client.mock_mode = True

    relevant_prompt = "<source_text>I cannot find receipt from Walmart in 2022</source_text>"
    result: RelevanceFilterOutput = await client.call_gemini(relevant_prompt, schema=RelevanceFilterOutput)

    assert isinstance(result, RelevanceFilterOutput)
    assert result.is_relevant is True
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.rationale) > 0

    irrelevant_prompt = "<source_text>App crashes whenever I open settings menu.</source_text>"
    result_irr: RelevanceFilterOutput = await client.call_gemini(irrelevant_prompt, schema=RelevanceFilterOutput)
    assert isinstance(result_irr, RelevanceFilterOutput)
    assert result_irr.is_relevant is False


@pytest.mark.asyncio
async def test_gemini_mock_evidence_extraction():
    client = GeminiClient()
    client.mock_mode = True

    prompt = "<source_text>Tried searching for yellow raincoat dog in Chicago. It brought up zero results and I gave up searching.</source_text>"
    result: EvidenceExtraction = await client.call_gemini(prompt, schema=EvidenceExtraction)

    assert isinstance(result, EvidenceExtraction)
    assert result.retrieval_scenario is not None
    assert result.memory_cues is not None
    assert 0.0 <= result.confidence_score <= 1.0
    assert result.retrieval_outcome == RetrievalOutcome.ABANDONED
    assert len(result.failure_points) > 0


@pytest.mark.asyncio
async def test_gemini_embedding_generation():
    client = GeminiClient()
    client.mock_mode = True

    embedding = await client.generate_embedding("search photo by color and location")
    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)


def test_validate_excerpt_in_content():
    raw_text = "I tried searching for my lease documents but OCR completely missed the blurry vehicle identification number."
    
    # Verbatim exact match
    exact_excerpt = "OCR completely missed the blurry vehicle identification number"
    assert validate_excerpt_in_content(exact_excerpt, raw_text) == exact_excerpt

    # Case-insensitive match
    case_excerpt = "ocr completely missed the blurry vehicle identification number"
    assert validate_excerpt_in_content(case_excerpt, raw_text) == exact_excerpt

    # Fabricated / altered excerpt
    altered_excerpt = "Optical Character Recognition failed on vehicle documents"
    assert validate_excerpt_in_content(altered_excerpt, raw_text) is None

    # Empty inputs
    assert validate_excerpt_in_content("", raw_text) is None
    assert validate_excerpt_in_content(None, raw_text) is None


@pytest.mark.asyncio
async def test_gemini_unavailable_error_handling():
    client = GeminiClient()
    client.mock_mode = False  # Force non-mock mode with failing mock genai

    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("503 Service Unavailable: Gemini API overloaded")
        mock_model_cls.return_value = mock_instance

        with pytest.raises(GeminiUnavailableError) as exc_info:
            await client.call_gemini("Test prompt", schema=RelevanceFilterOutput, max_retries=2)
        assert "Gemini API failed" in str(exc_info.value)
