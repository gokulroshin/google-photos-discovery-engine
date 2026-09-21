from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class RetrievalOutcome(str, Enum):
    FOUND_IMMEDIATELY = "found_immediately"
    FOUND_AFTER_EFFORT = "found_after_effort"
    FOUND_BY_ACCIDENT = "found_by_accident"
    ABANDONED = "abandoned"
    WORKAROUND_USED = "workaround_used"
    FOUND_OUTSIDE_GOOGLE_PHOTOS = "found_outside_google_photos"
    UNRESOLVED = "unresolved"


class RelevanceFilterOutput(BaseModel):
    is_relevant: bool = Field(
        ...,
        description="True if the text describes a user struggling to find photos due to incomplete/uncertain memory.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0.",
    )
    rationale: str = Field(
        ...,
        description="Clear explanation of why this record is or is not relevant to retrieval failures.",
    )
    is_genuine_experience: bool = Field(
        default=True,
        description="False if the post appears fictional, satirical, hypothetical, or spam.",
    )
    tone_flags: List[str] = Field(
        default_factory=list,
        description="Flags such as 'sarcasm', 'hypothetical', 'fictional', 'feature_request', 'bug_report'.",
    )


class MemoryCues(BaseModel):
    person: Optional[str] = Field(None, description="Who was in the photo or event")
    place: Optional[str] = Field(None, description="Where the photo was taken or location clues")
    time: Optional[str] = Field(None, description="Temporal clues (e.g. season, year, relative time)")
    event: Optional[str] = Field(None, description="Event or activity context (e.g. wedding, trip, birthday)")
    object: Optional[str] = Field(None, description="Physical objects or items recalled")
    visual: Optional[str] = Field(None, description="Colors, lighting, clothing, visual aesthetic clues")
    text: Optional[str] = Field(None, description="Text, signs, labels, or documents within the photo")
    emotion: Optional[str] = Field(None, description="Feelings, moods, or emotional atmosphere")
    purpose: Optional[str] = Field(None, description="Why the photo was taken or needed")
    source: Optional[str] = Field(None, description="Device, app, camera, or sharing source")


class EvidenceExtraction(BaseModel):
    relevance_labels: List[str] = Field(
        default_factory=list,
        description="High-level category tags (e.g. 'vague_visual', 'missing_metadata', 'face_tagging_error', 'ocr_failure').",
    )
    retrieval_scenario: str = Field(
        ...,
        description="Concise description of the specific photo retrieval attempt and intent.",
    )
    memory_cues: MemoryCues = Field(
        default_factory=MemoryCues,
        description="Specific memory dimensions the user recalled.",
    )
    missing_information: Optional[str] = Field(
        None,
        description="What key metadata the user forgot or could not specify (e.g. exact date, folder name).",
    )
    search_behavior: Optional[str] = Field(
        None,
        description="Actions the user took to search (e.g. query terms tried, manual scrolling, filtering).",
    )
    retrieval_outcome: RetrievalOutcome = Field(
        default=RetrievalOutcome.UNRESOLVED,
        description="The ultimate result of the retrieval attempt.",
    )
    failure_points: List[str] = Field(
        default_factory=list,
        description="Specific breakdown points where Google Photos failed the user.",
    )
    user_segment: Optional[str] = Field(
        None,
        description="Identified user segment (e.g. 'casual_photographer', 'parent', 'power_searcher', 'professional').",
    )
    evidence_excerpt: Optional[str] = Field(
        None,
        description="Verbatim exact quote from the source text demonstrating the retrieval difficulty.",
    )
    confidence_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Model confidence score in the accuracy of this extraction.",
    )
    rationale: str = Field(
        ...,
        description="Reasoning explaining the structured breakdown.",
    )
    is_genuine_experience: bool = Field(
        default=True,
        description="Whether this represents a real user experience.",
    )

    @field_validator("failure_points", "relevance_labels", mode="before")
    @classmethod
    def ensure_list(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return []


def validate_excerpt_in_content(excerpt: Optional[str], raw_content: str) -> Optional[str]:
    """
    Verifies that the extracted excerpt is a verbatim substring of raw_content.
    If the excerpt is slightly modified or fabricated, returns None to uphold evidence integrity.
    """
    if not excerpt or not excerpt.strip() or not raw_content:
        return None

    clean_excerpt = excerpt.strip()
    clean_raw = raw_content.strip()

    # Exact substring check
    if clean_excerpt in clean_raw:
        return clean_excerpt

    # Case-insensitive substring check
    lower_raw = clean_raw.lower()
    lower_exc = clean_excerpt.lower()
    idx = lower_raw.find(lower_exc)
    if idx != -1:
        # Return the actual casing from raw_content
        return clean_raw[idx : idx + len(clean_excerpt)]

    return None


class TaxonomyClusterOutput(BaseModel):
    name: str = Field(..., description="Short, descriptive category title (3-6 words)")
    definition: str = Field(..., description="Precise definition of this specific retrieval failure pattern (2-3 sentences)")
    user_segment: Optional[str] = Field(None, description="Primary user segment affected")
    common_memory_cues: Dict[str, Any] = Field(default_factory=dict, description="Memory cues most commonly present")
    missing_information: Optional[str] = Field(None, description="Information typically missing or imprecise")
    common_search_behavior: Optional[str] = Field(None, description="Typical user actions that fail")
    failure_mechanism: str = Field(..., description="Technical or experiential reason retrieval fails")
    representative_excerpts: List[str] = Field(default_factory=list, description="3-5 verbatim evidence excerpts")
    open_questions: List[str] = Field(default_factory=list, description="2-4 open research questions for PMs")
    product_implications: Optional[str] = Field(None, description="Strategic product implications")


class OpportunityScoreOutput(BaseModel):
    user_impact_score: float = Field(..., ge=0.0, le=10.0, description="Estimated severity of failure mode on user satisfaction (0-10)")
    abandonment_rate: float = Field(..., ge=0.0, le=1.0, description="Estimated fraction of attempts ending in abandonment (0.0-1.0)")
    workaround_exists: bool = Field(..., description="Whether users have viable manual workarounds")
    strategic_relevance: float = Field(..., ge=0.0, le=10.0, description="Strategic importance to core Photos mission (0-10)")
    problem_clarity: float = Field(..., ge=0.0, le=10.0, description="How well-defined and measurable the problem is (0-10)")
    potential_reach: str = Field(..., description="Qualitative estimate of user population affected")
    validation_effort: str = Field(..., description="low, medium, or high effort to prototype and validate")
    scoring_methodology: str = Field(..., description="Transparent narrative explaining how scores were derived")

