import pytest
from backend.gemini.schemas import validate_excerpt_in_content


def test_excerpt_valid_exact_substring():
    raw_content = "I searched for my dog wearing a yellow raincoat in Chicago back in 2021."
    excerpt = "dog wearing a yellow raincoat"

    validated = validate_excerpt_in_content(excerpt, raw_content)
    assert validated == excerpt


def test_excerpt_valid_case_insensitive_substring():
    raw_content = "I searched for my DOG WEARING A YELLOW RAINCOAT in Chicago."
    excerpt = "dog wearing a yellow raincoat"

    validated = validate_excerpt_in_content(excerpt, raw_content)
    assert validated is not None
    assert "RAINCOAT" in validated or "raincoat" in validated.lower()


def test_excerpt_hallucinated_invalid_substring():
    raw_content = "I searched for my dog wearing a yellow raincoat in Chicago."
    hallucinated_excerpt = "The user explicitly mentioned blue umbrella in Seattle."

    validated = validate_excerpt_in_content(hallucinated_excerpt, raw_content)
    assert validated is None


def test_excerpt_empty_or_whitespace():
    raw_content = "I searched for my dog."
    assert validate_excerpt_in_content("", raw_content) is None
    assert validate_excerpt_in_content("   ", raw_content) is None
    assert validate_excerpt_in_content(None, raw_content) is None
