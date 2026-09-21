import csv
import io
import json
from typing import List, Dict, Any
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.taxonomy_category import TaxonomyCategory


class ExportService:
    """
    Service for generating Excel-compatible CSV and structured JSON exports
    of evidence records and taxonomy categories.
    """

    @classmethod
    async def export_evidence_csv(cls, db: AsyncSession, project_id: str) -> str:
        """
        Exports all active evidence records for a project as CSV with UTF-8 BOM and QUOTE_ALL.
        """
        await cls._verify_project(db, project_id)

        stmt = (
            select(EvidenceRecord, SourceRecord)
            .join(SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id)
            .where(
                and_(
                    SourceRecord.project_id == project_id,
                    SourceRecord.deleted_at.is_(None),
                )
            )
            .order_by(EvidenceRecord.created_at.desc())
        )
        rows = (await db.execute(stmt)).all()

        output = io.StringIO()
        # Write UTF-8 BOM for Microsoft Excel compatibility
        output.write("\ufeff")

        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow([
            "id",
            "source_record_id",
            "source_platform",
            "source_url",
            "source_date",
            "author_handle",
            "is_relevant",
            "retrieval_scenario",
            "memory_cues",
            "missing_information",
            "search_behavior",
            "retrieval_outcome",
            "failure_points",
            "user_segment",
            "evidence_excerpt",
            "confidence_score",
            "rationale",
            "needs_human_review",
            "created_at",
        ])

        for ev, src in rows:
            writer.writerow([
                ev.id,
                ev.source_record_id,
                src.source_platform if src else "unknown",
                src.source_url if src else "",
                src.source_date.isoformat() if src and src.source_date else "",
                src.author_handle if src else "user_anonymous",
                ev.is_relevant,
                ev.retrieval_scenario or "",
                json.dumps(ev.memory_cues) if ev.memory_cues else "",
                ev.missing_information or "",
                ev.search_behavior or "",
                ev.retrieval_outcome or "",
                "; ".join(ev.failure_points) if ev.failure_points else "",
                ev.user_segment or "",
                ev.evidence_excerpt or "",
                ev.confidence_score if ev.confidence_score is not None else "",
                ev.rationale or "",
                ev.needs_human_review,
                ev.created_at.isoformat() if ev.created_at else "",
            ])

        return output.getvalue()

    @classmethod
    async def export_evidence_json(cls, db: AsyncSession, project_id: str) -> List[Dict[str, Any]]:
        """
        Exports all active evidence records for a project as structured JSON.
        """
        await cls._verify_project(db, project_id)

        stmt = (
            select(EvidenceRecord, SourceRecord)
            .join(SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id)
            .where(
                and_(
                    SourceRecord.project_id == project_id,
                    SourceRecord.deleted_at.is_(None),
                )
            )
            .order_by(EvidenceRecord.created_at.desc())
        )
        rows = (await db.execute(stmt)).all()

        records = []
        for ev, src in rows:
            records.append({
                "id": ev.id,
                "source_record_id": ev.source_record_id,
                "source_platform": src.source_platform if src else "unknown",
                "source_url": src.source_url if src else None,
                "source_date": src.source_date.isoformat() if src and src.source_date else None,
                "author_handle": src.author_handle if src else "user_anonymous",
                "is_relevant": ev.is_relevant,
                "retrieval_scenario": ev.retrieval_scenario,
                "memory_cues": ev.memory_cues,
                "missing_information": ev.missing_information,
                "search_behavior": ev.search_behavior,
                "retrieval_outcome": ev.retrieval_outcome,
                "failure_points": ev.failure_points,
                "user_segment": ev.user_segment,
                "evidence_excerpt": ev.evidence_excerpt,
                "confidence_score": ev.confidence_score,
                "rationale": ev.rationale,
                "needs_human_review": ev.needs_human_review,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
            })
        return records

    @classmethod
    async def export_taxonomy_csv(cls, db: AsyncSession, project_id: str) -> str:
        """
        Exports taxonomy categories as CSV with UTF-8 BOM and QUOTE_ALL.
        """
        await cls._verify_project(db, project_id)

        stmt = (
            select(TaxonomyCategory)
            .where(TaxonomyCategory.project_id == project_id)
            .order_by(TaxonomyCategory.evidence_count.desc())
        )
        categories = (await db.execute(stmt)).scalars().all()

        output = io.StringIO()
        output.write("\ufeff")

        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow([
            "id",
            "version",
            "name",
            "definition",
            "user_segment",
            "failure_mechanism",
            "evidence_count",
            "unique_author_count",
            "confidence_level",
            "product_implications",
            "representative_excerpts",
            "open_questions",
            "created_at",
        ])

        for cat in categories:
            writer.writerow([
                str(cat.id),
                cat.version,
                cat.name,
                cat.definition,
                cat.user_segment or "",
                cat.failure_mechanism or "",
                cat.evidence_count,
                cat.unique_author_count,
                cat.confidence_level,
                cat.product_implications or "",
                " | ".join(cat.representative_excerpts) if cat.representative_excerpts else "",
                " | ".join(cat.open_questions) if cat.open_questions else "",
                cat.created_at.isoformat() if cat.created_at else "",
            ])

        return output.getvalue()

    @classmethod
    async def export_taxonomy_json(cls, db: AsyncSession, project_id: str) -> List[Dict[str, Any]]:
        """
        Exports taxonomy categories as structured JSON.
        """
        await cls._verify_project(db, project_id)

        stmt = (
            select(TaxonomyCategory)
            .where(TaxonomyCategory.project_id == project_id)
            .order_by(TaxonomyCategory.evidence_count.desc())
        )
        categories = (await db.execute(stmt)).scalars().all()

        return [
            {
                "id": str(c.id),
                "version": c.version,
                "name": c.name,
                "definition": c.definition,
                "user_segment": c.user_segment,
                "failure_mechanism": c.failure_mechanism,
                "evidence_count": c.evidence_count,
                "unique_author_count": c.unique_author_count,
                "confidence_level": c.confidence_level,
                "product_implications": c.product_implications,
                "representative_excerpts": c.representative_excerpts,
                "open_questions": c.open_questions,
                "source_diversity": c.source_diversity,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in categories
        ]

    @staticmethod
    async def _verify_project(db: AsyncSession, project_id: str) -> ResearchProject:
        stmt = select(ResearchProject).where(
            and_(ResearchProject.id == project_id, ResearchProject.deleted_at.is_(None))
        )
        project = (await db.execute(stmt)).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
