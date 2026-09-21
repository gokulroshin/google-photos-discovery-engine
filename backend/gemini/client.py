import asyncio
import time
import json
import hashlib
from typing import Optional, Type, TypeVar, Any, List, Dict
from pydantic import BaseModel
import structlog
from backend.config import get_settings
from backend.gemini.schemas import (
    RelevanceFilterOutput,
    EvidenceExtraction,
    RetrievalOutcome,
    MemoryCues,
)

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class GeminiUnavailableError(Exception):
    """Raised when the Google Gemini API is unreachable, rate-limited, or encountering persistent outages."""
    pass


class GeminiClient:
    """
    Client for interacting with Google Gemini models for structured classification,
    evidence extraction, taxonomy clustering, and vector embeddings.
    """

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GEMINI_API_KEY
        self.model_name = self.settings.GEMINI_MODEL
        self.embedding_model_name = self.settings.GEMINI_EMBEDDING_MODEL
        self.mock_mode = (
            self.settings.MOCK_DATA_MODE
            or self.settings.ENVIRONMENT in ["test", "testing"]
            or not self.api_key
            or not HAS_GENAI
        )

        if HAS_GENAI and self.api_key and not self.mock_mode:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                logger.warning("gemini_configure_failed", error=str(e))
                self.mock_mode = True

    async def call_gemini(
        self,
        prompt: str,
        schema: Optional[Type[T]] = None,
        system_instruction: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> Any:
        """
        Executes a Gemini inference call with structured JSON validation, retry backoff,
        and fallback mock mode support.
        """
        if self.mock_mode:
            return self._generate_mock_response(prompt, schema)

        backoff_delays = [1.0, 2.0, 4.0]
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction,
                    generation_config={"response_mime_type": "application/json"} if schema else None,
                )

                # Execute synchronous SDK call in thread executor with timeout
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: model.generate_content(prompt)),
                    timeout=timeout,
                )

                latency = time.time() - start_time
                response_text = response.text.strip()

                logger.info(
                    "gemini_call_success",
                    model=self.model_name,
                    latency=round(latency, 3),
                    attempt=attempt + 1,
                    schema=schema.__name__ if schema else None,
                )

                if schema:
                    try:
                        return schema.model_validate_json(response_text)
                    except Exception as val_err:
                        # Attempt to extract JSON if markdown fences exist
                        cleaned_json = self._extract_json_block(response_text)
                        return schema.model_validate_json(cleaned_json)

                return response_text

            except asyncio.TimeoutError:
                logger.warning("gemini_timeout", attempt=attempt + 1, timeout=timeout)
                if attempt == max_retries - 1:
                    raise GeminiUnavailableError(f"Gemini API timed out after {max_retries} attempts.")
            except Exception as exc:
                err_str = str(exc)
                logger.warning(
                    "gemini_call_retry",
                    attempt=attempt + 1,
                    error=err_str,
                    model=self.model_name,
                )
                # Check for rate limit or server error
                if attempt == max_retries - 1:
                    raise GeminiUnavailableError(f"Gemini API failed after {max_retries} attempts: {err_str}")

                delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                await asyncio.sleep(delay)

        raise GeminiUnavailableError("Gemini API call failed unexpectedly.")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a 768-dimensional embedding vector using text-embedding-004.
        """
        if not text or not text.strip():
            return [0.0] * 768

        if self.mock_mode:
            return self._generate_mock_embedding(text)

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model=self.embedding_model_name,
                    content=text,
                    task_type="retrieval_document",
                ),
            )
            embedding = result.get("embedding", [])
            if isinstance(embedding, list) and len(embedding) == 768:
                return embedding
            return self._generate_mock_embedding(text)
        except Exception as exc:
            logger.warning("gemini_embedding_failed_fallback_to_mock", error=str(exc))
            return self._generate_mock_embedding(text)

    async def check_health(self) -> bool:
        """Checks if the Gemini API is reachable."""
        if self.mock_mode:
            return True
        try:
            res = await self.call_gemini("Respond with: ok", timeout=10.0, max_retries=1)
            return True
        except Exception:
            return False

    @staticmethod
    def _extract_json_block(text: str) -> str:
        """Extracts JSON substring from markdown backticks or raw content."""
        if "```json" in text:
            return text.split("```json")[1].split("```")[0].strip()
        if "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def _generate_mock_response(self, prompt: str, schema: Optional[Type[BaseModel]]) -> Any:
        """Generates deterministic, schema-compliant mock responses for tests and offline mode."""
        source_text = prompt
        if "<source_text>" in prompt and "</source_text>" in prompt:
            source_text = prompt.split("<source_text>")[1].split("</source_text>")[0]
        source_text_lower = source_text.lower()

        if schema == RelevanceFilterOutput:
            # Check keywords in the source text to decide relevance
            keywords = ["find", "search", "receipt", "dog", "wedding", "photo", "picture", "lost", "remember", "face", "sunset", "greece", "color", "pier", "tent", "boat", "yosemite", "ocr", "camera", "album", "bicycle", "cat"]
            is_rel = any(kw in source_text_lower for kw in keywords) and "crash" not in source_text_lower
            return RelevanceFilterOutput(
                is_relevant=is_rel,
                confidence=0.92 if is_rel else 0.85,
                rationale="Mock evaluation: identified photo retrieval failure context." if is_rel else "Mock evaluation: unrelated content.",
                is_genuine_experience=True,
                tone_flags=["user_complaint"] if is_rel else [],
            )

        if schema == EvidenceExtraction:
            # Generate excerpt from source text if available
            excerpt = None
            if source_text and source_text.strip():
                clean_src = source_text.strip()
                # Take first sentence or substring
                first_sent = clean_src.split(".")[0].strip()
                if first_sent and len(first_sent) > 5 and first_sent in clean_src:
                    excerpt = first_sent
                else:
                    excerpt = clean_src[:80] if len(clean_src) >= 80 else clean_src

            return EvidenceExtraction(
                relevance_labels=["vague_visual_memory", "missing_temporal_context"],
                retrieval_scenario="User trying to locate a photo using partial visual or contextual memory",
                memory_cues=MemoryCues(
                    visual="color and lighting details",
                    time="approximate season or year",
                    event="travel or personal event",
                ),
                missing_information="Exact calendar date, album name, or file metadata",
                search_behavior="Tried descriptive keywords and manual timeline scrolling",
                retrieval_outcome=RetrievalOutcome.ABANDONED if "abandon" in source_text_lower or "gave up" in source_text_lower else RetrievalOutcome.FOUND_AFTER_EFFORT,
                failure_points=["Search keywords missed visual nuances", "No contextual semantic matching"],
                user_segment="casual_photographer",
                evidence_excerpt=excerpt,
                confidence_score=0.88,
                rationale="Mock extraction grounded in user feedback cues.",
                is_genuine_experience=True,
            )

        if schema and schema.__name__ == "TaxonomyClusterOutput":
            return schema(
                name="Incomplete Contextual & Visual Memory",
                definition="Users recall partial episodic or visual context (e.g. weather, color, companions) but lack searchable metadata.",
                user_segment="Casual photographers & family archivists",
                common_memory_cues={"visual": "clothing & colors", "time": "approximate season"},
                missing_information="Exact calendar date, album tag, or filename",
                common_search_behavior="Iterative query rephrasing and manual date timeline scrolling",
                failure_mechanism="Tag and OCR indexing does not map episodic memory to image features",
                representative_excerpts=["Searched for yellow raincoat dog in Chicago", "Cannot find receipt from Home Depot"],
                open_questions=["How frequently do users abandon multi-word episodic queries?"],
                product_implications="Opportunity for multi-modal contextual query expansion and conversational retrieval.",
            )

        if schema and schema.__name__ == "OpportunityScoreOutput":
            return schema(
                user_impact_score=8.5,
                abandonment_rate=0.38,
                workaround_exists=True,
                strategic_relevance=9.0,
                problem_clarity=8.0,
                potential_reach="High reach across casual and power mobile users",
                validation_effort="medium",
                scoring_methodology="Derived from high user friction in exploratory searches and high abandonment rate without clear workarounds.",
            )

        if schema:
            return schema.model_construct()

        return '{"status": "ok", "mock": true}'

    @staticmethod
    def _generate_mock_embedding(text: str) -> List[float]:
        """Generates a deterministic 768-dim float vector seeded by SHA-256 hash."""
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Generate 768 floats based on hash bytes
        vector = []
        for i in range(768):
            byte_val = h[i % len(h)]
            val = ((byte_val + i * 7) % 200 - 100) / 100.0
            vector.append(round(val, 6))
        # Normalize vector to unit length
        norm = sum(x * x for x in vector) ** 0.5 or 1.0
        return [round(x / norm, 6) for x in vector]


# Global singleton client
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
