from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import hashlib
import re


@dataclass
class RawRecord:
    raw_content: str
    source_platform: str
    source_url: Optional[str] = None
    source_date: Optional[datetime] = None
    author_handle: Optional[str] = None
    collection_method: str = "automated_adapter"
    metadata: Dict[str, Any] = field(default_factory=dict)


class SourceAdapter(ABC):
    """
    Abstract base class for all data source adapters.
    Each adapter provides platform-specific retrieval and normalisation.
    """
    platform_name: str = "unknown"
    tos_status: str = "open"  # "open" | "restricted" | "requires_auth"

    @abstractmethod
    async def fetch(self, config: Dict[str, Any]) -> List[RawRecord]:
        """
        Fetches raw records from the external source platform using the given configuration.
        Must handle errors, rate limits, and platform-specific pagination gracefully.
        """
        pass

    @abstractmethod
    def normalize(self, raw: RawRecord) -> Dict[str, Any]:
        """
        Normalizes a RawRecord into standard fields matching SourceRecord DB/schema.
        """
        pass

    def compute_dedup_hash(self, content: str) -> str:
        """
        Computes a SHA-256 fingerprint from cleaned content for deduplication.
        Collapses whitespace to avoid duplicate entries due to formatting variance.
        """
        normalized_content = re.sub(r"\s+", " ", content.strip()).lower()
        return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
