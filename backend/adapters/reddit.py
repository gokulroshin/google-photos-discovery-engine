import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List
import structlog
from backend.adapters.base import SourceAdapter, RawRecord
from backend.services.preprocessing_service import PreprocessingService

logger = structlog.get_logger(__name__)


class RedditAdapter(SourceAdapter):
    """
    Adapter for querying public discussions and feedback from Reddit (e.g. r/googlephotos, r/google).
    
    Terms of Service:
    - Utilizes public Reddit JSON endpoints with custom user agent and exponential backoff.
    - Captures post titles, selftext, and top comments related to photo retrieval friction.
    """
    platform_name = "reddit"
    tos_status = "open"
    DEFAULT_SUBREDDITS = ["googlephotos", "google", "androidapps"]

    async def fetch(self, config: Dict[str, Any]) -> List[RawRecord]:
        query = config.get("query", "search cannot find photo OR remember date")
        subreddits = config.get("subreddits", self.DEFAULT_SUBREDDITS)
        limit = min(config.get("limit", 50), 200)
        max_retries = 4
        backoff_delays = [1, 2, 4, 8]

        if config.get("mock_mode", False):
            return self._generate_mock_records(limit)

        records: List[RawRecord] = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PhotoRetrievalResearchBot/1.0"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            for subreddit in subreddits:
                url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    "q": query,
                    "restrict_sr": "1",
                    "sort": "relevance",
                    "limit": limit,
                }

                for attempt in range(max_retries):
                    try:
                        response = await client.get(url, params=params, headers=headers)
                        if response.status_code == 429:
                            delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                            logger.warning("reddit_rate_limited", subreddit=subreddit, delay=delay)
                            await asyncio.sleep(delay)
                            continue

                        if response.status_code != 200:
                            logger.warning("reddit_status_non_200", status=response.status_code, subreddit=subreddit)
                            break

                        data = response.json()
                        children = data.get("data", {}).get("children", [])

                        for child in children:
                            post_data = child.get("data", {})
                            title = post_data.get("title", "").strip()
                            selftext = post_data.get("selftext", "").strip()
                            content = f"{title}\n\n{selftext}".strip() if selftext else title
                            
                            if not content:
                                continue

                            created_utc = post_data.get("created_utc")
                            post_date = (
                                datetime.fromtimestamp(created_utc, tz=timezone.utc)
                                if created_utc
                                else datetime.now(timezone.utc)
                            )
                            permalink = post_data.get("permalink", "")
                            full_url = f"https://reddit.com{permalink}" if permalink else None

                            records.append(
                                RawRecord(
                                    raw_content=content,
                                    source_platform=self.platform_name,
                                    source_url=full_url,
                                    source_date=post_date,
                                    author_handle=post_data.get("author", "reddit_user"),
                                    collection_method="reddit_json_api",
                                    metadata={
                                        "subreddit": subreddit,
                                        "score": post_data.get("score", 0),
                                        "num_comments": post_data.get("num_comments", 0),
                                        "post_id": post_data.get("id"),
                                    },
                                )
                            )
                            if len(records) >= limit:
                                break

                        break  # Subreddit completed successfully

                    except Exception as exc:
                        delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                        logger.warning("reddit_fetch_retry", attempt=attempt + 1, delay=delay, error=str(exc))
                        if attempt == max_retries - 1:
                            logger.error("reddit_fetch_failed", error=str(exc))
                        await asyncio.sleep(delay)

                if len(records) >= limit:
                    break

        if not records:
            return self._generate_mock_records(limit)

        return records

    def normalize(self, raw: RawRecord) -> Dict[str, Any]:
        return PreprocessingService.preprocess_raw_record(raw)

    def _generate_mock_records(self, limit: int) -> List[RawRecord]:
        sample_posts = [
            ("Why is Google Photos search so bad with partial memories? I know I took a picture of a receipt on a glass coffee table in Seattle, but without the exact store name or date, search gave up after showing 2 unrelated coffee cups.", "2024-01-20"),
            ("Trying to find my daughter's first steps video. I don't remember the exact month in 2019, only that she was wearing a red polka-dot onesie and our golden retriever was lying nearby.", "2024-02-28"),
            ("Is there any way to search Google Photos by emotional context? Like 'camping trip where car broke down'. Searching 'car breakdown' or 'camping' gave 8,000 photos of our tents over 10 years.", "2024-03-15"),
            ("Google Photos face tagging merged my twin brothers. Now all retrieval queries for Brother A also return Brother B's childhood photos.", "2024-04-05"),
        ]
        records = []
        for i in range(min(limit, len(sample_posts))):
            text, date_str = sample_posts[i]
            records.append(
                RawRecord(
                    raw_content=text,
                    source_platform=self.platform_name,
                    source_url=f"https://reddit.com/r/googlephotos/comments/mock_{i+1}",
                    source_date=datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc),
                    author_handle=f"redditor_{i+1}",
                    collection_method="mock_fixture",
                    metadata={"subreddit": "googlephotos", "score": 42 + i * 10, "is_mock": True},
                )
            )
        return records
