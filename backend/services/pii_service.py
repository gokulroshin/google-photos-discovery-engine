import re
from typing import List, Dict, Any, Tuple


class PIIService:
    """
    Service for detecting, flagging, and redacting Personally Identifiable Information (PII)
    including email addresses, phone numbers, SSNs, and payment card numbers.
    """

    # Compiled regex patterns for PII entities
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    )
    PHONE_PATTERN = re.compile(
        r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b'
    )
    SSN_PATTERN = re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b'
    )
    CREDIT_CARD_PATTERN = re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
    )

    @classmethod
    def detect_pii(cls, text: str) -> List[Dict[str, Any]]:
        """
        Detects PII occurrences in a text string.
        Returns a list of detected entities with entity_type and matched span.
        """
        if not text:
            return []

        entities = []

        for match in cls.EMAIL_PATTERN.finditer(text):
            entities.append({
                "type": "email",
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })

        for match in cls.PHONE_PATTERN.finditer(text):
            entities.append({
                "type": "phone",
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })

        for match in cls.SSN_PATTERN.finditer(text):
            entities.append({
                "type": "ssn",
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })

        for match in cls.CREDIT_CARD_PATTERN.finditer(text):
            entities.append({
                "type": "credit_card",
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })

        return entities

    @classmethod
    def redact_pii(cls, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Redacts all detected PII entities in a text string with replacement token.
        """
        if not text:
            return ""

        redacted = text
        redacted = cls.EMAIL_PATTERN.sub(replacement, redacted)
        redacted = cls.PHONE_PATTERN.sub(replacement, redacted)
        redacted = cls.SSN_PATTERN.sub(replacement, redacted)
        redacted = cls.CREDIT_CARD_PATTERN.sub(replacement, redacted)
        return redacted

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """Returns True if the text contains any detected PII entity."""
        return len(cls.detect_pii(text)) > 0
