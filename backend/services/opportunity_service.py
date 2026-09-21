from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from backend.models.opportunity_area import OpportunityArea
from backend.models.taxonomy_category import TaxonomyCategory
from backend.models.evidence_record import EvidenceRecord
from backend.models.source_record import SourceRecord
from backend.models.project import ResearchProject
from backend.gemini.client import get_gemini_client
from backend.gemini.prompts import render_prompt

logger = structlog.get_logger(__name__)


class OpportunityScoreOutput(BaseModel):
    user_impact_score: float = Field(default=7.0, ge=0.0, le=10.0)
    abandonment_rate: float = Field(default=0.3, ge=0.0, le=1.0)
    workaround_exists: bool = False
    strategic_relevance: float = Field(default=8.0, ge=0.0, le=10.0)
    problem_clarity: float = Field(default=7.5, ge=0.0, le=10.0)
    potential_reach: str = Field(default="High reach across casual and power users")
    validation_effort: str = Field(default="medium", pattern="^(low|medium|high)$")
    scoring_methodology: str = Field(..., description="Justification of scores grounded in evidence")


class OpportunityService:
    """
    Generates and evaluates Opportunity Areas from taxonomy problem categories,
    scoring each area across 9 strategic dimensions.
    """

    @classmethod
    async def generate_opportunities(
        cls,
        db: AsyncSession,
        project_id: str,
    ) -> List[OpportunityArea]:
        """
        Generates OpportunityArea records for all categories in the latest taxonomy version.
        """
        # 1. Verify project
        proj_stmt = select(ResearchProject).where(
            ResearchProject.id == project_id,
            ResearchProject.deleted_at.is_(None),
        )
        project = (await db.execute(proj_stmt)).scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )

        # 2. Fetch latest taxonomy categories
        version_stmt = select(func.max(TaxonomyCategory.version)).where(TaxonomyCategory.project_id == project_id)
        latest_version = (await db.execute(version_stmt)).scalar()
        if not latest_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No taxonomy categories found. Please generate a taxonomy first before creating opportunity areas.",
            )

        cat_stmt = select(TaxonomyCategory).where(
            TaxonomyCategory.project_id == project_id,
            TaxonomyCategory.version == latest_version,
        )
        categories = list((await db.execute(cat_stmt)).scalars().all())

        if not categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No taxonomy categories found for latest version.",
            )

        # 3. Calculate project-level empirical abandonment and workaround rates
        abandonment_stmt = select(func.count(EvidenceRecord.id)).join(
            SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id
        ).where(
            SourceRecord.project_id == project_id,
            EvidenceRecord.is_relevant == True,
            EvidenceRecord.retrieval_outcome == "abandoned",
        )
        abandoned_count = (await db.execute(abandonment_stmt)).scalar() or 0

        workaround_stmt = select(func.count(EvidenceRecord.id)).join(
            SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id
        ).where(
            SourceRecord.project_id == project_id,
            EvidenceRecord.is_relevant == True,
            EvidenceRecord.retrieval_outcome == "workaround_used",
        )
        workaround_count = (await db.execute(workaround_stmt)).scalar() or 0

        total_ev_stmt = select(func.count(EvidenceRecord.id)).join(
            SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id
        ).where(
            SourceRecord.project_id == project_id,
            EvidenceRecord.is_relevant == True,
        )
        total_ev_count = (await db.execute(total_ev_stmt)).scalar() or 1

        empirical_abandonment = round(abandoned_count / total_ev_count, 2)
        empirical_workaround = workaround_count > 0

        gemini_client = get_gemini_client()
        created_opportunities: List[OpportunityArea] = []

        # 4. Score each category with Gemini
        for cat in categories:
            prompt = render_prompt(
                "opportunity_score",
                category_name=cat.name,
                definition=cat.definition,
                evidence_count=cat.evidence_count,
                source_diversity=cat.source_diversity,
                failure_mechanism=cat.failure_mechanism,
            )
            score_out: OpportunityScoreOutput = await gemini_client.call_gemini(
                prompt,
                schema=OpportunityScoreOutput,
            )

            # Determine status
            if cat.evidence_count == 0:
                opp_status = "speculative"
            elif cat.confidence_level == "high":
                opp_status = "validated"
            else:
                opp_status = "draft"

            # Merge empirical and model insights
            final_abandonment = score_out.abandonment_rate if cat.evidence_count < 5 else empirical_abandonment
            final_workaround = score_out.workaround_exists or empirical_workaround

            opp = OpportunityArea(
                project_id=project_id,
                taxonomy_category_id=str(cat.id),
                name=f"Opportunity: {cat.name}",
                description=f"Address failure mechanism: {cat.definition}",
                evidence_frequency=cat.evidence_count,
                evidence_diversity=cat.source_diversity or {},
                unique_author_count=cat.unique_author_count,
                user_impact_score=score_out.user_impact_score,
                abandonment_rate=final_abandonment,
                workaround_exists=final_workaround,
                strategic_relevance=score_out.strategic_relevance,
                problem_clarity=score_out.problem_clarity,
                potential_reach=score_out.potential_reach,
                validation_effort=score_out.validation_effort,
                scoring_methodology=score_out.scoring_methodology,
                status=opp_status,
            )
            db.add(opp)
            created_opportunities.append(opp)

        await db.commit()
        for opp in created_opportunities:
            await db.refresh(opp)

        logger.info(
            "opportunities_generated",
            project_id=project_id,
            count=len(created_opportunities),
        )
        return created_opportunities

    @classmethod
    async def list_opportunities(
        cls,
        db: AsyncSession,
        project_id: str,
        status_filter: Optional[str] = None,
    ) -> List[OpportunityArea]:
        """Lists opportunity areas for a project."""
        filters = [OpportunityArea.project_id == project_id]
        if status_filter:
            filters.append(OpportunityArea.status == status_filter.lower().strip())

        stmt = (
            select(OpportunityArea)
            .where(and_(*filters))
            .order_by(OpportunityArea.evidence_frequency.desc(), OpportunityArea.user_impact_score.desc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def get_opportunity(
        cls,
        db: AsyncSession,
        project_id: str,
        opportunity_id: str,
    ) -> OpportunityArea:
        """Retrieves single opportunity area detail."""
        stmt = select(OpportunityArea).where(
            OpportunityArea.id == opportunity_id,
            OpportunityArea.project_id == project_id,
        )
        opp = (await db.execute(stmt)).scalar_one_or_none()
        if not opp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Opportunity area '{opportunity_id}' not found for project '{project_id}'.",
            )
        return opp

    @classmethod
    async def update_opportunity(
        cls,
        db: AsyncSession,
        project_id: str,
        opportunity_id: str,
        update_data: Dict[str, Any],
    ) -> OpportunityArea:
        """
        Updates opportunity area fields.
        Enforces that `analyst_notes` MUST be provided when manually modifying scores.
        """
        opp = await cls.get_opportunity(db, project_id, opportunity_id)

        SCORE_FIELDS = {
            "user_impact_score",
            "abandonment_rate",
            "workaround_exists",
            "strategic_relevance",
            "problem_clarity",
            "validation_effort",
        }

        # Check if any score fields are being updated
        updating_scores = any(
            k in update_data and update_data[k] is not None and getattr(opp, k) != update_data[k]
            for k in SCORE_FIELDS
        )

        if updating_scores:
            analyst_notes = update_data.get("analyst_notes")
            if not analyst_notes or not analyst_notes.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Field 'analyst_notes' is required when manually modifying strategic opportunity scores.",
                )

        for key, val in update_data.items():
            if val is not None and hasattr(opp, key):
                setattr(opp, key, val)

        opp.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(opp)

        logger.info(
            "opportunity_updated",
            opportunity_id=opportunity_id,
            project_id=project_id,
            manual_override=updating_scores,
        )
        return opp
