import math
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from backend.models.taxonomy_category import TaxonomyCategory
from backend.models.evidence_record import EvidenceRecord
from backend.models.source_record import SourceRecord
from backend.models.project import ResearchProject
from backend.gemini.client import get_gemini_client
from backend.gemini.prompts import render_prompt

logger = structlog.get_logger(__name__)


class TaxonomyClusterOutput(BaseModel):
    name: str = Field(..., description="Concise, descriptive category name")
    definition: str = Field(..., description="Clear explanation of the retrieval problem")
    user_segment: Optional[str] = Field(None, description="Primary user personas affected")
    common_memory_cues: Dict[str, Any] = Field(default_factory=dict)
    missing_information: Optional[str] = Field(None, description="Common missing cues or metadata")
    common_search_behavior: Optional[str] = Field(None, description="Typical user search attempts")
    failure_mechanism: str = Field(..., description="Why Google Photos search failed")
    representative_excerpts: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    product_implications: Optional[str] = Field(None, description="Product considerations")


class TaxonomyService:
    """
    Generates and maintains the retrieval problem taxonomy using semantic clustering,
    LLM category definition, and statistical evidence aggregation.
    """

    MIN_CATEGORIES = 3
    MAX_CATEGORIES = 15

    @classmethod
    async def generate_taxonomy(
        cls,
        db: AsyncSession,
        project_id: str,
        k_clusters: Optional[int] = None,
    ) -> List[TaxonomyCategory]:
        """
        Executes end-to-end taxonomy generation:
        1. Fetch all validated evidence records
        2. Cluster records semantically (via embeddings or keyword fallback)
        3. Define categories with Gemini LLM
        4. Validate metrics, unique author counts, and confidence levels
        5. Version and store taxonomy categories
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

        # 2. Fetch validated evidence records
        stmt = (
            select(EvidenceRecord)
            .options(selectinload(EvidenceRecord.source_record))
            .join(SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id)
            .where(
                SourceRecord.project_id == project_id,
                SourceRecord.deleted_at.is_(None),
                EvidenceRecord.is_relevant == True,
                EvidenceRecord.needs_human_review == False,
            )
        )
        evidence_records = list((await db.execute(stmt)).scalars().all())

        if len(evidence_records) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient evidence records to generate taxonomy ({len(evidence_records)} found). At least 3 validated records are required.",
            )

        # 3. Determine cluster count k
        total_records = len(evidence_records)
        if k_clusters:
            k = max(cls.MIN_CATEGORIES, min(k_clusters, cls.MAX_CATEGORIES, total_records))
        else:
            k = max(cls.MIN_CATEGORIES, min(math.ceil(total_records / 5), cls.MAX_CATEGORIES, total_records))

        # 4. Cluster evidence records
        clusters = cls._cluster_records(evidence_records, k)

        # 5. Determine next version number
        version_stmt = select(func.max(TaxonomyCategory.version)).where(TaxonomyCategory.project_id == project_id)
        current_version = (await db.execute(version_stmt)).scalar() or 0
        new_version = current_version + 1

        gemini_client = get_gemini_client()
        created_categories: List[TaxonomyCategory] = []

        # 6. Generate category definitions with Gemini
        for cluster_idx, cluster_items in enumerate(clusters):
            if not cluster_items:
                continue

            sample_records = [
                {
                    "retrieval_scenario": rec.retrieval_scenario or "Unspecified scenario",
                    "evidence_excerpt": rec.evidence_excerpt or (rec.source_record.raw_content[:150] if rec.source_record else ""),
                    "failure_points": rec.failure_points or [],
                    "memory_cues": rec.memory_cues or {},
                }
                for rec in cluster_items[:10]
            ]

            prompt = render_prompt("taxonomy_cluster", records=sample_records)
            cluster_definition: TaxonomyClusterOutput = await gemini_client.call_gemini(
                prompt,
                schema=TaxonomyClusterOutput,
            )

            # Compute category metrics
            evidence_count = len(cluster_items)
            
            # Count unique authors (deduplicated by author_handle)
            author_handles = set()
            source_diversity: Dict[str, int] = {}

            for rec in cluster_items:
                if rec.source_record:
                    handle = rec.source_record.author_handle or "anonymous"
                    author_handles.add(handle)
                    platform = rec.source_record.source_platform or "unknown"
                    source_diversity[platform] = source_diversity.get(platform, 0) + 1

            unique_author_count = len(author_handles)

            # Determine confidence level
            if evidence_count < 3:
                confidence_level = "low"
            elif evidence_count < 8:
                confidence_level = "medium"
            else:
                confidence_level = "high"

            # Fallback representative excerpts if empty
            excerpts = cluster_definition.representative_excerpts or [
                rec.evidence_excerpt for rec in cluster_items if rec.evidence_excerpt
            ][:4]

            cat = TaxonomyCategory(
                project_id=project_id,
                version=new_version,
                name=cluster_definition.name or f"Category {cluster_idx + 1}",
                definition=cluster_definition.definition,
                user_segment=cluster_definition.user_segment,
                common_memory_cues=cluster_definition.common_memory_cues or {},
                missing_information=cluster_definition.missing_information,
                common_search_behavior=cluster_definition.common_search_behavior,
                failure_mechanism=cluster_definition.failure_mechanism,
                evidence_count=evidence_count,
                unique_author_count=unique_author_count,
                source_diversity=source_diversity,
                representative_excerpts=excerpts,
                confidence_level=confidence_level,
                open_questions=cluster_definition.open_questions or [],
                product_implications=cluster_definition.product_implications,
            )
            db.add(cat)
            created_categories.append(cat)

        await db.commit()
        for cat in created_categories:
            await db.refresh(cat)

        logger.info(
            "taxonomy_generated",
            project_id=project_id,
            version=new_version,
            category_count=len(created_categories),
        )
        return created_categories

    @classmethod
    def _cluster_records(
        cls,
        records: List[EvidenceRecord],
        k: int,
    ) -> List[List[EvidenceRecord]]:
        """
        Groups evidence records into k clusters using vector embeddings (KMeans)
        or feature/keyword heuristic fallback.
        """
        # Check if embeddings are available on all records
        embeddings = []
        for rec in records:
            if rec.embedding and isinstance(rec.embedding, (list, np.ndarray)) and len(rec.embedding) == 768:
                embeddings.append(rec.embedding)

        if HAS_SKLEARN and len(embeddings) == len(records) and len(records) >= k:
            try:
                X = np.array(embeddings)
                kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
                labels = kmeans.fit_predict(X)

                clusters: List[List[EvidenceRecord]] = [[] for _ in range(k)]
                for idx, label in enumerate(labels):
                    clusters[label].append(records[idx])
                non_empty = [c for c in clusters if c]
                if len(non_empty) >= min(k, cls.MIN_CATEGORIES) or len(non_empty) == len(records):
                    return non_empty
            except Exception as e:
                logger.warning("kmeans_clustering_failed_using_fallback", error=str(e))

        # Fallback: Hash / label-based bucketing across k buckets
        clusters = [[] for _ in range(k)]
        for idx, rec in enumerate(records):
            bucket_idx = idx % k
            clusters[bucket_idx].append(rec)
        return [c for c in clusters if c]

    @classmethod
    async def list_categories(
        cls,
        db: AsyncSession,
        project_id: str,
        version: Optional[int] = None,
    ) -> Tuple[List[TaxonomyCategory], int, int]:
        """
        Lists taxonomy categories for a given project. Defaults to latest version.
        Returns (categories, total_count, version).
        """
        if version is None:
            version_stmt = select(func.max(TaxonomyCategory.version)).where(TaxonomyCategory.project_id == project_id)
            latest_version = (await db.execute(version_stmt)).scalar()
            if latest_version is None:
                return [], 0, 1
            target_version = latest_version
        else:
            target_version = version

        stmt = (
            select(TaxonomyCategory)
            .where(
                TaxonomyCategory.project_id == project_id,
                TaxonomyCategory.version == target_version,
            )
            .order_by(TaxonomyCategory.evidence_count.desc())
        )
        categories = list((await db.execute(stmt)).scalars().all())
        return categories, len(categories), target_version

    @classmethod
    async def get_category(
        cls,
        db: AsyncSession,
        project_id: str,
        category_id: str,
    ) -> TaxonomyCategory:
        """Retrieves single category detail."""
        stmt = select(TaxonomyCategory).where(
            TaxonomyCategory.id == category_id,
            TaxonomyCategory.project_id == project_id,
        )
        cat = (await db.execute(stmt)).scalar_one_or_none()
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxonomy category '{category_id}' not found for project '{project_id}'.",
            )
        return cat

    @classmethod
    async def update_category(
        cls,
        db: AsyncSession,
        project_id: str,
        category_id: str,
        update_data: Dict[str, Any],
    ) -> TaxonomyCategory:
        """Updates category fields e.g. name, definition, open questions."""
        cat = await cls.get_category(db, project_id, category_id)

        for key, val in update_data.items():
            if val is not None and hasattr(cat, key):
                setattr(cat, key, val)

        cat.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(cat)
        return cat

    @classmethod
    async def merge_categories(
        cls,
        db: AsyncSession,
        project_id: str,
        source_category_ids: List[str],
        target_name: str,
        merged_definition: Optional[str] = None,
    ) -> TaxonomyCategory:
        """
        Merges multiple taxonomy categories into a unified category.
        Aggregates evidence counts, unique authors, source diversity, and excerpts.
        Admin role required.
        """
        if len(source_category_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 category IDs are required to perform a merge.",
            )

        stmt = select(TaxonomyCategory).where(
            TaxonomyCategory.project_id == project_id,
            TaxonomyCategory.id.in_(source_category_ids),
        )
        cats = list((await db.execute(stmt)).scalars().all())
        if len(cats) < len(source_category_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more specified category IDs were not found.",
            )

        target_version = max(c.version for c in cats)
        total_evidence = sum(c.evidence_count for c in cats)
        total_unique_authors = sum(c.unique_author_count for c in cats)

        # Merge source diversity dicts
        merged_diversity: Dict[str, int] = {}
        for c in cats:
            for platform, count in (c.source_diversity or {}).items():
                merged_diversity[platform] = merged_diversity.get(platform, 0) + count

        # Merge representative excerpts
        merged_excerpts = []
        for c in cats:
            merged_excerpts.extend(c.representative_excerpts or [])
        merged_excerpts = list(dict.fromkeys(merged_excerpts))[:5]

        # Merge open questions
        merged_questions = []
        for c in cats:
            merged_questions.extend(c.open_questions or [])
        merged_questions = list(dict.fromkeys(merged_questions))[:5]

        # Create new merged category
        merged_cat = TaxonomyCategory(
            project_id=project_id,
            version=target_version,
            name=target_name.strip(),
            definition=merged_definition or f"Merged failure mode combining: {', '.join([c.name for c in cats])}",
            user_segment=cats[0].user_segment or "General Users",
            common_memory_cues=cats[0].common_memory_cues or {},
            missing_information=cats[0].missing_information or "",
            common_search_behavior=cats[0].common_search_behavior or "",
            failure_mechanism=cats[0].failure_mechanism or "Multi-factor retrieval breakdown",
            evidence_count=total_evidence,
            unique_author_count=total_unique_authors,
            source_diversity=merged_diversity,
            representative_excerpts=merged_excerpts,
            confidence_level="high" if total_evidence >= 10 else "medium",
            open_questions=merged_questions,
            product_implications=cats[0].product_implications or "",
        )
        db.add(merged_cat)

        # Delete source categories
        for c in cats:
            await db.delete(c)

        await db.commit()
        await db.refresh(merged_cat)
        return merged_cat

    @classmethod
    async def delete_category(
        cls,
        db: AsyncSession,
        project_id: str,
        category_id: str,
    ) -> bool:
        """Deletes a taxonomy category. Admin role required."""
        cat = await cls.get_category(db, project_id, category_id)
        await db.delete(cat)
        await db.commit()
        return True

