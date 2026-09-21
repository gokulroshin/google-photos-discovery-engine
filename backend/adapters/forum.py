import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List
import structlog
from backend.adapters.base import SourceAdapter, RawRecord
from backend.services.preprocessing_service import PreprocessingService

logger = structlog.get_logger(__name__)

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


class ForumAdapter(SourceAdapter):
    """
    Adapter for scraping public support forum threads and help community questions
    regarding Google Photos retrieval failures and search issues.
    
    Terms of Service:
    - Scrapes public community forum threads.
    - Honors robots.txt and restricts request rate.
    """
    platform_name = "forum"
    tos_status = "open"

    async def is_url_allowed_by_robots(self, target_url: str, user_agent: str = "Mozilla/5.0") -> bool:
        """
        Parses the domain from target_url, retrieves robots.txt, and checks if scraping is permitted.
        """
        try:
            from urllib.parse import urlparse
            from urllib.robotparser import RobotFileParser

            parsed = urlparse(target_url)
            if not parsed.scheme or not parsed.netloc:
                return True

            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(robots_url, headers={"User-Agent": user_agent})
                if resp.status_code in [401, 403]:
                    logger.warning("robots_txt_access_denied", url=robots_url, status=resp.status_code)
                    return False
                if resp.status_code != 200:
                    # If robots.txt doesn't exist (404), scraping is generally allowed
                    return True

                rp = RobotFileParser()
                rp.parse(resp.text.splitlines())
                allowed = rp.can_fetch(user_agent, target_url)
                if not allowed:
                    logger.warning("robots_txt_disallowed_crawl", url=target_url, user_agent=user_agent)
                return allowed
        except Exception as e:
            logger.warning("robots_txt_check_error_permitting_crawl", error=str(e), url=target_url)
            return True

    async def fetch(self, config: Dict[str, Any]) -> List[RawRecord]:
        forum_url = config.get("forum_url")
        limit = min(config.get("limit", 20), 100)

        if not forum_url or not HAS_BS4 or config.get("mock_mode", False):
            return self._generate_mock_records(limit)

        user_agent = "Mozilla/5.0 (ResearchBot; GooglePhotosDiscovery/1.0)"

        # Check robots.txt compliance
        allowed = await self.is_url_allowed_by_robots(forum_url, user_agent=user_agent)
        if not allowed:
            logger.warning("forum_scraping_blocked_by_robots_txt", url=forum_url)
            return self._generate_mock_records(limit)

        records: List[RawRecord] = []
        max_retries = 3
        backoff_delays = [1, 2, 4]

        async with httpx.AsyncClient(timeout=15.0) as client:
            for attempt in range(max_retries):
                try:
                    response = await client.get(
                        forum_url,
                        headers={"User-Agent": user_agent},
                    )
                    if response.status_code == 429:
                        delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Generic forum thread extractor
                    threads = soup.find_all(["article", "div"], class_=lambda c: c and ("thread" in c or "post" in c or "question" in c))
                    for item in threads[:limit]:
                        text = item.get_text(separator=" ", strip=True)
                        if len(text) > 30:
                            records.append(
                                RawRecord(
                                    raw_content=text,
                                    source_platform=self.platform_name,
                                    source_url=forum_url,
                                    source_date=datetime.now(timezone.utc),
                                    author_handle="community_member",
                                    collection_method="forum_html_scraper",
                                    metadata={"forum_url": forum_url},
                                )
                            )
                    return records

                except Exception as exc:
                    delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                    logger.warning("forum_fetch_retry", attempt=attempt + 1, delay=delay, error=str(exc))
                    if attempt == max_retries - 1:
                        logger.error("forum_fetch_failed", error=str(exc))
                        return self._generate_mock_records(limit)
                    await asyncio.sleep(delay)

        return records

    def normalize(self, raw: RawRecord) -> Dict[str, Any]:
        return PreprocessingService.preprocess_raw_record(raw)

    def _generate_mock_records(self, limit: int) -> List[RawRecord]:
        sample_threads = [
            ("Thread: How do I find photos based on text in the image when OCR failed?\nI took a picture of my medical prescription on a kitchen counter in May 2022. Searching 'prescription' or 'amoxicillin' yields nothing because the bottle label was slightly slanted.", "2024-02-10"),
            ("Thread: Face Recognition grouped distant cousin with stranger\nI am trying to retrieve all photos of my cousin's wedding in Austin, but face clustering mixed up people and search by person returns hundreds of erroneous images.", "2024-03-18"),
            ("Thread: Can we search by visual vibe or color theme?\nI remember a sunset photo on a wooden pier where everything was amber and dark purple, but typing 'amber pier sunset' didn't match the image tags.", "2024-04-20"),
        ]
        records = []
        for i in range(min(limit, len(sample_threads))):
            text, date_str = sample_threads[i]
            records.append(
                RawRecord(
                    raw_content=text,
                    source_platform=self.platform_name,
                    source_url=f"https://support.google.com/photos/thread/mock_{i+1}",
                    source_date=datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc),
                    author_handle=f"community_user_{i+1}",
                    collection_method="mock_fixture",
                    metadata={"is_mock": True},
                )
            )
        return records
