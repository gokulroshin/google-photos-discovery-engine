import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List
import structlog
from backend.adapters.base import SourceAdapter, RawRecord
from backend.services.preprocessing_service import PreprocessingService

logger = structlog.get_logger(__name__)


class YouTubeAdapter(SourceAdapter):
    """
    Adapter for gathering comments and transcript snippets from YouTube videos
    addressing Google Photos search, organization, and retrieval troubleshooting.
    
    Terms of Service:
    - Queries public comments using YouTube Data API v3 or mock fallback.
    - Used for user sentiment and failure mode identification.
    """
    platform_name = "youtube"
    tos_status = "open"

    async def fetch(self, config: Dict[str, Any]) -> List[RawRecord]:
        api_key = config.get("api_key")
        video_id = config.get("video_id", "mock_video_search_tips")
        limit = min(config.get("limit", 50), 200)

        if not api_key or config.get("mock_mode", False):
            return self._generate_mock_records(limit)

        records: List[RawRecord] = []
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(limit, 100),
            "key": api_key,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                        text = snippet.get("textDisplay", "").strip()
                        if not text:
                            continue
                        author = snippet.get("authorDisplayName", "youtube_user")
                        pub_at = snippet.get("publishedAt")
                        comment_date = (
                            datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
                            if pub_at
                            else datetime.now(timezone.utc)
                        )
                        records.append(
                            RawRecord(
                                raw_content=text,
                                source_platform=self.platform_name,
                                source_url=f"https://www.youtube.com/watch?v={video_id}&lc={item.get('id')}",
                                source_date=comment_date,
                                author_handle=author,
                                collection_method="youtube_data_api_v3",
                                metadata={"likeCount": snippet.get("likeCount", 0), "videoId": video_id},
                            )
                        )
                    return records
            except Exception as exc:
                logger.warning("youtube_api_error_fallback", error=str(exc))

        return self._generate_mock_records(limit)

    def normalize(self, raw: RawRecord) -> Dict[str, Any]:
        return PreprocessingService.preprocess_raw_record(raw)

    def _generate_mock_records(self, limit: int) -> List[RawRecord]:
        sample_comments = [
            ("I watched this entire video hoping it would show how to find photos when I only recall who was in the background, but the advice was just 'make albums manually'. Who has time to tag 50,000 photos?", "2024-03-01"),
            ("Searched 'white boat blue sails' because I took a photo during our vacation in Greece. It showed me pictures of blue sky and white snow back home in Ohio.", "2024-03-25"),
            ("The worst part is when you know a photo exists from 5 years ago, you search 10 different combinations of words, nothing shows up, and then you stumble upon it by accident under the wrong date.", "2024-04-12"),
        ]
        records = []
        for i in range(min(limit, len(sample_comments))):
            text, date_str = sample_comments[i]
            records.append(
                RawRecord(
                    raw_content=text,
                    source_platform=self.platform_name,
                    source_url=f"https://youtube.com/watch?v=demo_video&lc=mock_yt_{i+1}",
                    source_date=datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc),
                    author_handle=f"yt_user_{i+1}",
                    collection_method="mock_fixture",
                    metadata={"is_mock": True},
                )
            )
        return records
