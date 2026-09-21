import pytest
import json
from backend.adapters import get_adapter, list_supported_adapters, ADAPTER_REGISTRY
from backend.adapters.manual_import import ManualImportAdapter, ManualImportError
from backend.adapters.play_store import GooglePlayStoreAdapter
from backend.adapters.app_store import AppStoreAdapter
from backend.adapters.reddit import RedditAdapter
from backend.adapters.youtube import YouTubeAdapter
from backend.adapters.forum import ForumAdapter


def test_adapter_registry():
    supported = list_supported_adapters()
    assert "manual_import" in supported
    assert "play_store" in supported
    assert "app_store" in supported
    assert "reddit" in supported
    assert "youtube" in supported
    assert "forum" in supported

    adapter = get_adapter("play_store")
    assert isinstance(adapter, GooglePlayStoreAdapter)

    unknown = get_adapter("non_existent_source")
    assert unknown is None


def test_dedup_hash_stability():
    adapter = ManualImportAdapter()
    content1 = "  Cannot find  receipt from Home Depot 2022  "
    content2 = "cannot find receipt from home depot 2022"
    hash1 = adapter.compute_dedup_hash(content1)
    hash2 = adapter.compute_dedup_hash(content2)
    assert hash1 == hash2
    assert len(hash1) == 64


@pytest.mark.asyncio
async def test_manual_import_csv_valid():
    adapter = ManualImportAdapter()
    csv_content = """raw_content,source_url,source_date,source_platform,author_handle,metadata
"Searched for dog in snow, got cats",https://example.com/1,2024-01-15,reddit,user123,"{""score"": 10}"
"Face recognition missed my sister",https://example.com/2,2024-02-20,play_store,user456,"{""rating"": 2}"
"""
    records = await adapter.fetch({"file_content": csv_content, "file_format": "csv"})
    assert len(records) == 2
    assert records[0].raw_content == "Searched for dog in snow, got cats"
    assert records[0].source_platform == "reddit"
    assert records[0].author_handle == "user123"
    assert records[0].metadata["score"] == 10
    assert records[1].source_platform == "play_store"


@pytest.mark.asyncio
async def test_manual_import_csv_missing_required_columns():
    adapter = ManualImportAdapter()
    # Missing source_url and source_date
    invalid_csv = """raw_content,source_platform
"Looking for wedding photos",reddit
"""
    with pytest.raises(ManualImportError) as exc_info:
        await adapter.fetch({"file_content": invalid_csv, "file_format": "csv"})
    
    assert "Missing required CSV columns" in str(exc_info.value)
    assert any("source_url" in err for err in exc_info.value.errors)
    assert any("source_date" in err for err in exc_info.value.errors)


@pytest.mark.asyncio
async def test_manual_import_json_valid():
    adapter = ManualImportAdapter()
    json_data = {
        "records": [
            {
                "raw_content": "Cannot find pictures from sunset in Maui",
                "source_url": "https://example.com/maui",
                "source_date": "2024-03-01T10:00:00Z",
                "source_platform": "forum",
                "author_handle": "traveler_99",
                "metadata": {"topic": "search_failure"}
            }
        ]
    }
    records = await adapter.fetch({"file_content": json.dumps(json_data), "file_format": "json"})
    assert len(records) == 1
    assert "sunset in Maui" in records[0].raw_content
    assert records[0].source_platform == "forum"
    assert records[0].metadata["topic"] == "search_failure"


@pytest.mark.asyncio
async def test_manual_import_file_size_limit():
    adapter = ManualImportAdapter()
    # Mock huge content
    adapter.MAX_FILE_SIZE_BYTES = 500  # set low limit for test
    oversized = "raw_content,source_url,source_date,source_platform\n" + ("x" * 600)
    with pytest.raises(ManualImportError) as exc_info:
        await adapter.fetch({"file_content": oversized, "file_format": "csv"})
    assert "maximum allowed size" in str(exc_info.value)


@pytest.mark.asyncio
async def test_play_store_adapter_mock_fetch():
    adapter = GooglePlayStoreAdapter()
    records = await adapter.fetch({"mock_mode": True, "limit": 3})
    assert len(records) == 3
    assert all(r.source_platform == "play_store" for r in records)
    assert all(r.metadata.get("is_mock") is True for r in records)


@pytest.mark.asyncio
async def test_app_store_adapter_mock_fetch():
    adapter = AppStoreAdapter()
    records = await adapter.fetch({"mock_mode": True, "limit": 2})
    assert len(records) == 2
    assert all(r.source_platform == "app_store" for r in records)


@pytest.mark.asyncio
async def test_reddit_adapter_mock_fetch():
    adapter = RedditAdapter()
    records = await adapter.fetch({"mock_mode": True, "limit": 4})
    assert len(records) == 4
    assert all(r.source_platform == "reddit" for r in records)


@pytest.mark.asyncio
async def test_youtube_adapter_mock_fetch():
    adapter = YouTubeAdapter()
    records = await adapter.fetch({"mock_mode": True, "limit": 2})
    assert len(records) == 2
    assert all(r.source_platform == "youtube" for r in records)


@pytest.mark.asyncio
async def test_forum_adapter_mock_fetch():
    adapter = ForumAdapter()
    records = await adapter.fetch({"mock_mode": True, "limit": 3})
    assert len(records) == 3
    assert all(r.source_platform == "forum" for r in records)
