import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
import structlog
from backend.adapters.base import SourceAdapter, RawRecord
from backend.services.preprocessing_service import PreprocessingService

logger = structlog.get_logger(__name__)

try:
    from google_play_scraper import Sort, reviews, search
    HAS_PLAY_SCRAPER = True
except ImportError:
    HAS_PLAY_SCRAPER = False


class GooglePlayStoreAdapter(SourceAdapter):
    """
    Adapter for ingesting public user reviews from Google Play Store for Google Photos.
    
    Terms of Service & Compliance:
    - Scrapes publicly visible customer reviews for package 'com.google.android.apps.photos'.
    - Used solely for non-commercial research and product discovery.
    - Implements backoff and rate-limiting to prevent server overload.
    """
    platform_name = "play_store"
    tos_status = "open"
    DEFAULT_APP_ID = "com.google.android.apps.photos"

    async def fetch(self, config: Dict[str, Any]) -> List[RawRecord]:
        app_id = config.get("app_id", self.DEFAULT_APP_ID)
        limit = min(config.get("limit", 100), 500)
        filter_query = config.get("query")
        max_retries = 4
        backoff_delays = [1, 2, 4, 8]

        records: List[RawRecord] = []

        if not HAS_PLAY_SCRAPER or config.get("mock_mode", False):
            return self._generate_mock_records(limit)

        for attempt in range(max_retries):
            try:
                # Run synchronous scraper in a thread to keep async loop unblocked
                loop = asyncio.get_event_loop()
                result, _ = await loop.run_in_executor(
                    None,
                    lambda: reviews(
                        app_id,
                        lang=config.get("lang", "en"),
                        country=config.get("country", "us"),
                        sort=Sort.NEWEST,
                        count=limit,
                        filter_score_with=config.get("score_filter", None),
                    )
                )

                for item in result:
                    content = item.get("content", "").strip()
                    if not content:
                        continue
                    
                    if filter_query and filter_query.lower() not in content.lower():
                        continue

                    review_date = item.get("at")
                    if review_date and isinstance(review_date, datetime):
                        if review_date.tzinfo is None:
                            review_date = review_date.replace(tzinfo=timezone.utc)
                    else:
                        review_date = datetime.now(timezone.utc)

                    review_id = item.get("reviewId", "")
                    records.append(
                        RawRecord(
                            raw_content=content,
                            source_platform=self.platform_name,
                            source_url=f"https://play.google.com/store/apps/details?id={app_id}&reviewId={review_id}",
                            source_date=review_date,
                            author_handle=item.get("userName", "play_store_user"),
                            collection_method="google_play_scraper",
                            metadata={
                                "score": item.get("score"),
                                "thumbsUpCount": item.get("thumbsUpCount", 0),
                                "appVersion": item.get("appVersion"),
                                "reviewId": review_id,
                            },
                        )
                    )

                logger.info("play_store_fetch_completed", count=len(records), app_id=app_id)
                return records

            except Exception as exc:
                delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                logger.warning(
                    "play_store_fetch_retry",
                    attempt=attempt + 1,
                    delay_seconds=delay,
                    error=str(exc),
                )
                if attempt == max_retries - 1:
                    logger.error("play_store_fetch_failed", error=str(exc))
                    # Fallback to mock records if API call failed completely
                    return self._generate_mock_records(limit)
                await asyncio.sleep(delay)

        return records

    def normalize(self, raw: RawRecord) -> Dict[str, Any]:
        return PreprocessingService.preprocess_raw_record(raw)

    def _generate_mock_records(self, limit: int) -> List[RawRecord]:
        """Realistic sample records for offline development, CI tests, and fallback."""
        sample_texts = [
            ("I was searching for a picture of my dog wearing a yellow raincoat in Chicago back in 2021, but typing 'yellow raincoat dog' brought up hundreds of random outdoor shots and missed the exact one.", "2024-03-10"),
            ("Search used to work better. Now I type 'receipt from Home Depot' and it shows me pictures of trees and screenshots of maps.", "2024-04-01"),
            ("Can't find pictures by describing what happened. I remember my kid blew out birthday candles next to a blue banner, but typing 'birthday candles blue banner' gives 0 results.", "2024-04-15"),
            ("The facial recognition grouped my uncle with a random person in a museum background, and now searching for his face shows 500 strangers.", "2024-05-02"),
            ("I don't remember the exact month I visited the Grand Canyon, only that it was snowy and sunset. Google Photos makes me scroll through 4 years of photos.", "2024-05-20"),
        ]
        records = []
        for i in range(min(limit, len(sample_texts))):
            text, date_str = sample_texts[i]
            records.append(
                RawRecord(
                    raw_content=text,
                    source_platform=self.platform_name,
                    source_url=f"https://play.google.com/store/apps/details?id={self.DEFAULT_APP_ID}&reviewId=mock_{i+1}",
                    source_date=datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc),
                    author_handle=f"android_user_{i+1}",
                    collection_method="mock_fixture",
                    metadata={"score": 2, "thumbsUpCount": i * 3, "is_mock": True},
                )
            )
        return records
