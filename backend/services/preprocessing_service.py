import re
import html
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from backend.adapters.base import RawRecord
from backend.logger import logger

try:
    from langdetect import detect as _detect_lang, DetectorFactory
    DetectorFactory.seed = 0
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False


class PreprocessingService:
    """
    Handles normalization, cleaning, PII pseudonymization, language detection,
    and metadata validation for ingested user records before database storage.
    """

    GOOGLE_PHOTOS_LAUNCH_DATE = datetime(2015, 1, 1, tzinfo=timezone.utc)
    MAX_TOKENS = 8000
    APPROX_CHARS_PER_TOKEN = 4
    MAX_CHARACTERS = MAX_TOKENS * APPROX_CHARS_PER_TOKEN  # ~32,000 characters

    # Inline tags that can be safely removed without adding extra spacing
    INLINE_TAGS_PATTERN = re.compile(r"</?(?:b|i|u|span|a|strong|em|mark|small|del|ins|sub|sup)[^>]*>", re.IGNORECASE)
    # Block tags that should be replaced with a space or newline separator
    BLOCK_TAGS_PATTERN = re.compile(r"</?(?:p|div|br|hr|h[1-6]|li|ul|ol|tr|td|th|blockquote|section|article|header|footer)[^>]*>", re.IGNORECASE)
    # Remaining generic HTML tags
    GENERIC_TAGS_PATTERN = re.compile(r"<[^>]+>")

    @classmethod
    def clean_html(cls, text: str) -> str:
        """
        Strips HTML tags first (preserving escaped entities like &lt;2023&gt;),
        then unescapes HTML entities.
        """
        if not text:
            return ""
        # 1. Remove inline formatting tags without adding extra space
        text_no_inline = cls.INLINE_TAGS_PATTERN.sub("", text)
        # 2. Replace block tags with a space separator
        text_no_blocks = cls.BLOCK_TAGS_PATTERN.sub(" ", text_no_inline)
        # 3. Strip any remaining HTML tags
        cleaned_tags = cls.GENERIC_TAGS_PATTERN.sub(" ", text_no_blocks)
        # 4. Unescape HTML entities (&amp; -> &, &lt; -> <, etc.)
        unescaped = html.unescape(cleaned_tags)
        return unescaped

    @classmethod
    def normalize_whitespace(cls, text: str) -> str:
        """
        Collapses multiple consecutive spaces and empty newlines,
        trimming whitespace per line.
        """
        if not text:
            return ""
        # Normalize carriage returns
        normalized_crlf = text.replace("\r\n", "\n").replace("\r", "\n")
        # Process each line: collapse internal spaces/tabs and strip line ends
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized_crlf.split("\n")]
        # Rejoin with newlines
        rejoined = "\n".join(lines)
        # Collapse 3+ consecutive newlines into double newlines for paragraph separation
        collapsed = re.sub(r"\n{3,}", "\n\n", rejoined)
        return collapsed.strip()

    @classmethod
    def detect_language(cls, text: str) -> Optional[str]:
        """
        Detects the ISO language code of the text (e.g., 'en', 'es', 'fr', 'hi').
        Falls back gracefully if detection fails or text is too short.
        """
        if not text or len(text.strip()) < 10:
            return "en"
        if not HAS_LANGDETECT:
            return "en"
        try:
            sample = text[:1000]
            detected = _detect_lang(sample)
            return detected
        except Exception:
            return "unknown"

    @classmethod
    def truncate_content(cls, text: str, max_chars: Optional[int] = None) -> Tuple[str, bool, int]:
        """
        Truncates content exceeding the token/char safety threshold.
        Returns (processed_text, is_truncated, original_length).
        """
        limit = max_chars or cls.MAX_CHARACTERS
        original_length = len(text)
        if len(text) > limit:
            truncated = text[:limit] + "... [TRUNCATED DUE TO LENGTH]"
            return truncated, True, original_length
        return text, False, original_length

    @classmethod
    def validate_source_date(cls, dt: Optional[datetime]) -> Tuple[Optional[datetime], Optional[str]]:
        """
        Validates the source date against historical and future sanity boundaries.
        Returns (sanitized_datetime, warning_message_or_None).
        """
        if dt is None:
            return None, None

        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        warning = None

        if dt < cls.GOOGLE_PHOTOS_LAUNCH_DATE:
            warning = f"Source date ({dt.date()}) is prior to Google Photos launch in 2015."
        elif dt > (now + timedelta(days=1)):
            warning = f"Source date ({dt.date()}) is in the future."

        return dt, warning

    @classmethod
    def pseudonymize_author(cls, author_handle: Optional[str]) -> Tuple[str, Optional[str]]:
        """
        Pseudonymizes user handles into SHA-256 hashes for privacy compliance.
        Returns (pseudonym, original_handle).
        """
        if not author_handle or author_handle.strip().lower() in ["anonymous", "anonymous_user", "null", "none", ""]:
            return "anonymous_user", None

        clean_handle = author_handle.strip()
        handle_hash = hashlib.sha256(clean_handle.lower().encode("utf-8")).hexdigest()[:8]
        pseudonym = f"user_{handle_hash}"
        return pseudonym, clean_handle

    @classmethod
    def preprocess_raw_record(cls, raw: RawRecord) -> Dict[str, Any]:
        """
        Runs the complete preprocessing and normalization pipeline on a RawRecord.
        """
        # 1. Clean HTML and normalize whitespace
        cleaned_content = cls.clean_html(raw.raw_content)
        normalized_content = cls.normalize_whitespace(cleaned_content)

        # 2. Content truncation check
        final_content, is_truncated, orig_char_len = cls.truncate_content(normalized_content)

        # 3. Language detection
        detected_lang = cls.detect_language(final_content)

        # 4. Date validation
        source_date, date_warning = cls.validate_source_date(raw.source_date)

        # 5. Author pseudonymization
        pseudonym, original_handle = cls.pseudonymize_author(raw.author_handle)

        # 6. Metadata enrichment
        metadata = dict(raw.metadata or {})
        if is_truncated:
            metadata["is_truncated"] = True
            metadata["original_char_count"] = orig_char_len
        if date_warning:
            metadata["date_warning"] = date_warning
        if original_handle:
            metadata["original_handle"] = original_handle
        if detected_lang and detected_lang != "en":
            metadata["language"] = detected_lang
            metadata["language_flag"] = f"Non-English content ({detected_lang})"

        # 7. Compute deduplication hash on the normalized content
        normalized_hash = hashlib.sha256(normalized_content.strip().lower().encode("utf-8")).hexdigest()

        return {
            "source_platform": raw.source_platform,
            "source_url": raw.source_url,
            "source_date": source_date,
            "raw_content": final_content,
            "author_handle": pseudonym,
            "collection_method": raw.collection_method or "automated_adapter",
            "metadata_json": metadata,
            "language": detected_lang or "en",
            "dedup_hash": normalized_hash,
            "is_duplicate": False,
        }
