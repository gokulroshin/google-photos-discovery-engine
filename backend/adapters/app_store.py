import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List
import structlog
from backend.adapters.base import SourceAdapter, RawRecord
from backend.services.preprocessing_service import PreprocessingService

logger = structlog.get_logger(__name__)


class AppStoreAdapter(SourceAdapter):
    """
    Adapter for Apple App Store customer reviews for Google Photos iOS (App ID: 962194608).
    Uses public iTunes RSS Customer Reviews endpoint with rate limiting and retry backoff.
    
    Terms of Service:
    - Queries public Apple RSS customer reviews API.
    - Used for product discovery & research purposes.
    """
    platform_name = "app_store"
    tos_status = "open"
    DEFAULT_APP_ID = "962194608"

    async def fetch(self, config: Dict[str, Any]) -> List[RawRecord]:
        app_id = config.get("app_id", self.DEFAULT_APP_ID)
        country = config.get("country", "us")
        limit = min(config.get("limit", 100), 500)
        filter_query = config.get("query")
        max_retries = 4
        backoff_delays = [1, 2, 4, 8]

        if config.get("mock_mode", False):
            return self._generate_mock_records(limit)

        url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
        records: List[RawRecord] = []

        async with httpx.AsyncClient(timeout=15.0) as client:
            for attempt in range(max_retries):
                try:
                    response = await client.get(url, headers={"User-Agent": "PhotoDiscoveryEngine/1.0 (Research Bot)"})
                    if response.status_code == 429:
                        delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                        logger.warning("app_store_rate_limited", attempt=attempt + 1, delay=delay)
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()
                    data = response.json()
                    entries = data.get("feed", {}).get("entry", [])

                    for entry in entries:
                        content_dict = entry.get("content", {})
                        content = content_dict.get("label", "").strip() if isinstance(content_dict, dict) else str(content_dict).strip()
                        if not content:
                            continue

                        if filter_query and filter_query.lower() not in content.lower():
                            continue

                        author_info = entry.get("author", {}).get("name", {}).get("label", "ios_user")
                        review_id = entry.get("id", {}).get("label", "")
                        
                        # Parse date if available
                        updated_label = entry.get("updated", {}).get("label")
                        review_date = datetime.now(timezone.utc)
                        if updated_label:
                            try:
                                dt = datetime.fromisoformat(updated_label.replace("Z", "+00:00"))
                                review_date = dt
                            except Exception:
                                pass

                        rating_str = entry.get("im:rating", {}).get("label", "0")
                        title = entry.get("title", {}).get("label", "")

                        records.append(
                            RawRecord(
                                raw_content=f"{title}: {content}" if title else content,
                                source_platform=self.platform_name,
                                source_url=f"https://apps.apple.com/app/id{app_id}?reviewId={review_id}",
                                source_date=review_date,
                                author_handle=author_info,
                                collection_method="itunes_rss_api",
                                metadata={
                                    "rating": int(rating_str) if rating_str.isdigit() else None,
                                    "reviewId": review_id,
                                    "title": title,
                                },
                            )
                        )
                        if len(records) >= limit:
                            break

                    logger.info("app_store_fetch_completed", count=len(records), app_id=app_id)
                    return records

                except Exception as exc:
                    delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                    logger.warning("app_store_fetch_retry", attempt=attempt + 1, delay=delay, error=str(exc))
                    if attempt == max_retries - 1:
                        logger.error("app_store_fetch_failed_using_mock", error=str(exc))
                        return self._generate_mock_records(limit)
                    await asyncio.sleep(delay)

        return records

    def normalize(self, raw: RawRecord) -> Dict[str, Any]:
        return PreprocessingService.preprocess_raw_record(raw)

    def _generate_mock_records(self, limit: int) -> List[RawRecord]:
        sample_texts = [
            ("Impossible to find old car lease documents I photographed 3 years ago because optical character recognition completely missed the blurry vehicle identification number.", "2024-02-14"),
            ("Trying to find photos from a road trip where we stopped at a restaurant with red neon sign and green chairs. Typed 'restaurant red neon sign' and found nothing.", "2024-03-22"),
            ("When I search for 'concert with purple lights', it gives me photos of flowers. I spent 45 minutes manually scrolling through 10,000 photos.", "2024-04-10"),
            ("The search doesn't understand context. I wanted photos of my wife wearing her graduation gown, but searching 'graduation' gave me every friend's graduation ceremony instead.", "2024-05-18"),
        ]
        records = []
        for i in range(min(limit, len(sample_texts))):
            text, date_str = sample_texts[i]
            records.append(
                RawRecord(
                    raw_content=text,
                    source_platform=self.platform_name,
                    source_url=f"https://apps.apple.com/app/id{self.DEFAULT_APP_ID}?reviewId=mock_ios_{i+1}",
                    source_date=datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc),
                    author_handle=f"ios_user_{i+1}",
                    collection_method="mock_fixture",
                    metadata={"rating": 1, "is_mock": True},
                )
            )
        return records
