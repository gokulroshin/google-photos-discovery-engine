import pytest
from datetime import datetime, timezone, timedelta
from backend.services.preprocessing_service import PreprocessingService
from backend.adapters.base import RawRecord


def test_clean_html():
    raw_html = "<p>I cannot find my <b>receipt</b> from &amp; Walmart &lt;2023&gt;.</p>"
    cleaned = PreprocessingService.clean_html(raw_html)
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "&amp;" not in cleaned
    assert "&" in cleaned
    assert "<2023>" in cleaned
    assert "receipt" in cleaned


def test_normalize_whitespace():
    messy = "  Can't   find   photos    \r\n\r\n\r\n\r\n  from    Chicago \t trip   "
    normalized = PreprocessingService.normalize_whitespace(messy)
    assert "   " not in normalized
    assert "\t" not in normalized
    assert normalized == "Can't find photos\n\nfrom Chicago trip"


def test_truncate_content():
    short_text = "This is a normal length query."
    proc_text, is_trunc, orig_len = PreprocessingService.truncate_content(short_text, max_chars=100)
    assert not is_trunc
    assert proc_text == short_text
    assert orig_len == len(short_text)

    long_text = "x" * 200
    proc_text, is_trunc, orig_len = PreprocessingService.truncate_content(long_text, max_chars=50)
    assert is_trunc
    assert orig_len == 200
    assert len(proc_text) > 50  # Includes truncation note
    assert "[TRUNCATED DUE TO LENGTH]" in proc_text


def test_validate_source_date_valid():
    valid_dt = datetime(2023, 5, 15, 12, 0, 0, tzinfo=timezone.utc)
    sanitized, warning = PreprocessingService.validate_source_date(valid_dt)
    assert sanitized == valid_dt
    assert warning is None


def test_validate_source_date_pre_2015():
    old_dt = datetime(2012, 4, 1, tzinfo=timezone.utc)
    sanitized, warning = PreprocessingService.validate_source_date(old_dt)
    assert sanitized == old_dt
    assert warning is not None
    assert "prior to Google Photos launch" in warning


def test_validate_source_date_future():
    future_dt = datetime.now(timezone.utc) + timedelta(days=30)
    sanitized, warning = PreprocessingService.validate_source_date(future_dt)
    assert sanitized == future_dt
    assert warning is not None
    assert "in the future" in warning


def test_pseudonymize_author():
    anon_pseudo, orig = PreprocessingService.pseudonymize_author(None)
    assert anon_pseudo == "anonymous_user"
    assert orig is None

    pseudo, orig = PreprocessingService.pseudonymize_author("Gokul_Researcher_99")
    assert pseudo.startswith("user_")
    assert len(pseudo) == 13  # "user_" + 8 hex chars
    assert orig == "Gokul_Researcher_99"


def test_preprocess_raw_record_end_to_end():
    raw = RawRecord(
        raw_content="<div>Searched for <b>dog on beach</b>, found nothing.</div>",
        source_platform="reddit",
        source_url="https://reddit.com/r/googlephotos/test",
        source_date=datetime(2024, 1, 10, tzinfo=timezone.utc),
        author_handle="JohnDoe123",
        collection_method="reddit_json_api",
        metadata={"subreddit": "googlephotos"},
    )
    result = PreprocessingService.preprocess_raw_record(raw)

    assert result["source_platform"] == "reddit"
    assert result["source_url"] == "https://reddit.com/r/googlephotos/test"
    assert "<div>" not in result["raw_content"]
    assert "Searched for dog on beach, found nothing." in result["raw_content"]
    assert result["author_handle"].startswith("user_")
    assert result["metadata_json"]["original_handle"] == "JohnDoe123"
    assert result["metadata_json"]["subreddit"] == "googlephotos"
    assert len(result["dedup_hash"]) == 64
