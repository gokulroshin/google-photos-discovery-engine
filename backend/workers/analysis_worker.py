import asyncio
from datetime import datetime, timezone
from typing import Optional, Callable, List
from sqlalchemy import select
import structlog
from backend.database import AsyncSessionLocal
from backend.models.model_run import ModelRun
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.gemini.client import get_gemini_client, GeminiUnavailableError
from backend.gemini.schemas import (
    RelevanceFilterOutput,
    EvidenceExtraction,
    validate_excerpt_in_content,
)
from backend.gemini.prompts import render_prompt

logger = structlog.get_logger(__name__)


class AnalysisWorker:
    """
    Background worker that executes the two-stage Gemini classification pipeline:
    Stage 1: Relevance Filtering
    Stage 2: Structured Evidence Extraction + Embedding Generation + Human Review Routing.
    """

    BATCH_CHECKPOINT_SIZE = 50
    session_factory: Callable = AsyncSessionLocal

    @classmethod
    async def run_analysis_job(cls, run_id: str, session_factory: Optional[Callable] = None):
        logger.info("analysis_worker_started", run_id=run_id)
        maker = session_factory or cls.session_factory
        gemini_client = get_gemini_client()

        async with maker() as db:
            # 1. Fetch ModelRun
            stmt = select(ModelRun).where(ModelRun.id == run_id)
            model_run = (await db.execute(stmt)).scalar_one_or_none()
            if not model_run:
                logger.error("model_run_not_found", run_id=run_id)
                return

            if model_run.status in ["completed", "cancelled"]:
                return

            model_run.status = "running"
            await db.commit()

            # 2. Fetch unprocessed source records
            analyzed_subquery = select(EvidenceRecord.source_record_id).where(
                EvidenceRecord.source_record_id.is_not(None)
            )
            records_stmt = (
                select(SourceRecord)
                .where(
                    SourceRecord.project_id == model_run.project_id,
                    SourceRecord.deleted_at.is_(None),
                    SourceRecord.id.not_in(analyzed_subquery),
                )
                .order_by(SourceRecord.created_at.asc())
            )
            unprocessed_records = list((await db.execute(records_stmt)).scalars().all())
            model_run.records_total = len(unprocessed_records)
            await db.commit()

            success_count = 0
            failed_count = 0

            try:
                for idx, record in enumerate(unprocessed_records):
                    # Check for cancellation or status change
                    await db.refresh(model_run)
                    if model_run.status == "cancelled":
                        logger.info("analysis_job_cancelled_by_user", run_id=run_id)
                        model_run.completed_at = datetime.now(timezone.utc)
                        await db.commit()
                        return

                    try:
                        # --- STAGE 1: Relevance Filter ---
                        rel_prompt = render_prompt("relevance_filter", raw_content=record.raw_content)
                        rel_result: RelevanceFilterOutput = await gemini_client.call_gemini(
                            rel_prompt,
                            schema=RelevanceFilterOutput,
                        )

                        if rel_result.is_relevant and rel_result.confidence >= 0.7:
                            # --- STAGE 2: Structured Evidence Extraction ---
                            ext_prompt = render_prompt("extraction", raw_content=record.raw_content)
                            ext_result: EvidenceExtraction = await gemini_client.call_gemini(
                                ext_prompt,
                                schema=EvidenceExtraction,
                            )

                            # Validate excerpt is verbatim substring
                            valid_excerpt = validate_excerpt_in_content(
                                ext_result.evidence_excerpt, record.raw_content
                            )
                            needs_review = (ext_result.confidence_score < 0.7) or (valid_excerpt is None and ext_result.evidence_excerpt is not None)

                            # Generate vector embedding for semantic search (decoupled from classification)
                            embed_text = valid_excerpt or record.raw_content[:500]
                            embedding = None
                            embedding_stale = False
                            try:
                                embedding = await gemini_client.generate_embedding(embed_text)
                            except Exception as embed_err:
                                logger.warning("embedding_generation_failed_non_blocking", error=str(embed_err), record_id=str(record.id))
                                embedding_stale = True

                            evidence = EvidenceRecord(
                                source_record_id=str(record.id),
                                model_run_id=str(model_run.id),
                                is_relevant=True,
                                relevance_labels=ext_result.relevance_labels or [],
                                retrieval_scenario=ext_result.retrieval_scenario,
                                memory_cues=ext_result.memory_cues.model_dump() if ext_result.memory_cues else {},
                                missing_information=ext_result.missing_information,
                                search_behavior=ext_result.search_behavior,
                                retrieval_outcome=ext_result.retrieval_outcome.value if hasattr(ext_result.retrieval_outcome, "value") else str(ext_result.retrieval_outcome),
                                failure_points=ext_result.failure_points or [],
                                user_segment=ext_result.user_segment,
                                evidence_excerpt=valid_excerpt or ext_result.evidence_excerpt,
                                confidence_score=ext_result.confidence_score,
                                rationale=ext_result.rationale,
                                needs_human_review=needs_review,
                                is_genuine_experience=ext_result.is_genuine_experience,
                                embedding=embedding,
                                embedding_stale=embedding_stale,
                                embedding_model_version=gemini_client.embedding_model_name,
                            )
                            db.add(evidence)

                        elif rel_result.is_relevant and rel_result.confidence < 0.7:
                            # Low confidence relevance -> Route to Human Review Queue
                            embed_text = record.raw_content[:500]
                            embedding = None
                            embedding_stale = False
                            try:
                                embedding = await gemini_client.generate_embedding(embed_text)
                            except Exception as embed_err:
                                logger.warning("embedding_generation_failed_non_blocking", error=str(embed_err), record_id=str(record.id))
                                embedding_stale = True

                            evidence = EvidenceRecord(
                                source_record_id=str(record.id),
                                model_run_id=str(model_run.id),
                                is_relevant=True,
                                relevance_labels=["uncertain_relevance"],
                                retrieval_scenario="Uncertain retrieval failure intent",
                                memory_cues={},
                                confidence_score=rel_result.confidence,
                                rationale=rel_result.rationale,
                                needs_human_review=True,
                                is_genuine_experience=rel_result.is_genuine_experience,
                                embedding=embedding,
                                embedding_stale=embedding_stale,
                                embedding_model_version=gemini_client.embedding_model_name,
                            )
                            db.add(evidence)

                        else:
                            # Non-relevant record
                            evidence = EvidenceRecord(
                                source_record_id=str(record.id),
                                model_run_id=str(model_run.id),
                                is_relevant=False,
                                relevance_labels=[],
                                confidence_score=rel_result.confidence,
                                rationale=rel_result.rationale,
                                needs_human_review=False,
                                is_genuine_experience=rel_result.is_genuine_experience,
                            )
                            db.add(evidence)

                        success_count += 1

                    except GeminiUnavailableError:
                        raise  # Caught below to pause job
                    except Exception as item_err:
                        logger.warning("record_classification_error", record_id=str(record.id), error=str(item_err))
                        failed_count += 1

                    # Checkpoint commit every batch
                    if (idx + 1) % cls.BATCH_CHECKPOINT_SIZE == 0:
                        model_run.records_success = success_count
                        model_run.records_failed = failed_count
                        await db.commit()
                        await asyncio.sleep(0.01)

                # Completed successfully
                model_run.records_success = success_count
                model_run.records_failed = failed_count
                model_run.status = "completed"
                model_run.completed_at = datetime.now(timezone.utc)
                await db.commit()
                logger.info(
                    "analysis_run_completed",
                    run_id=run_id,
                    success=success_count,
                    failed=failed_count,
                )

            except GeminiUnavailableError as gue:
                logger.error("gemini_unavailable_pausing_run", run_id=run_id, error=str(gue))
                model_run.status = "paused"
                model_run.records_success = success_count
                model_run.records_failed = failed_count
                model_run.error_log = {
                    "error": str(gue),
                    "paused_at": datetime.now(timezone.utc).isoformat(),
                    "message": "Gemini API unavailable or rate limited. Run can be resumed manually.",
                }
                await db.commit()

            except Exception as unhandled_err:
                logger.error("analysis_run_fatal_error", run_id=run_id, error=str(unhandled_err))
                model_run.status = "failed"
                model_run.records_success = success_count
                model_run.records_failed = failed_count
                model_run.error_log = {"error": str(unhandled_err)}
                model_run.completed_at = datetime.now(timezone.utc)
                await db.commit()
