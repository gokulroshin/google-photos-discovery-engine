from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.auth import get_current_user
from backend.models.user import User
from backend.services.report_service import ReportService
from backend.schemas.report import (
    ResearchReportResponse,
    ReportSummary,
)

router = APIRouter(prefix="/projects/{project_id}/reports", tags=["Reports"])


@router.post("", response_model=ResearchReportResponse)
@router.post("/generate", response_model=ResearchReportResponse)
async def generate_project_report(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Triggers synthesis of a new grounded research discovery report using Google Gemini.
    Validates source citations and stores the resulting report.
    """
    report = await ReportService.generate_report(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )
    return {
        "id": str(report.id),
        "project_id": str(report.project_id),
        "project_name": report.json_content.get("project_name", report.title),
        "title": report.title,
        "generated_at": report.created_at.isoformat(),
        "categories_count": report.json_content.get("categories_count", 0),
        "opportunities_count": report.json_content.get("opportunities_count", 0),
        "evidence_count": report.evidence_count,
        "pending_reviews_count": report.pending_reviews_count,
        "model_version": report.model_version,
        "prompt_version": report.prompt_version,
        "categories": report.json_content.get("categories", []),
        "opportunities": report.json_content.get("opportunities", []),
        "markdown": report.markdown_content,
        "created_at": report.created_at,
    }


@router.get("", response_model=List[ReportSummary])
async def list_project_reports(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists all historical research reports generated for a project.
    """
    reports = await ReportService.list_reports(db, project_id)
    return [
        {
            "id": str(r.id),
            "project_id": str(r.project_id),
            "title": r.title,
            "status": r.status,
            "evidence_count": r.evidence_count,
            "pending_reviews_count": r.pending_reviews_count,
            "model_version": r.model_version,
            "prompt_version": r.prompt_version,
            "created_at": r.created_at,
        }
        for r in reports
    ]


@router.get("/latest")
async def get_latest_project_report(
    project_id: str,
    format: Optional[str] = None,
    accept: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetches the latest research report for a project.
    If no report exists, attempts to generate one.
    """
    report = await ReportService.get_latest_report(db, project_id)
    if not report:
        # Generate initial report if possible
        try:
            report = await ReportService.generate_report(db, project_id, current_user)
        except Exception:
            raise HTTPException(status_code=404, detail="No research reports found for this project.")

    # Content negotiation
    if format == "markdown" or (accept and "text/markdown" in accept):
        return PlainTextResponse(content=report.markdown_content, media_type="text/markdown")

    return {
        "id": str(report.id),
        "project_id": str(report.project_id),
        "project_name": report.json_content.get("project_name", report.title),
        "title": report.title,
        "generated_at": report.created_at.isoformat(),
        "categories_count": report.json_content.get("categories_count", 0),
        "opportunities_count": report.json_content.get("opportunities_count", 0),
        "evidence_count": report.evidence_count,
        "pending_reviews_count": report.pending_reviews_count,
        "model_version": report.model_version,
        "prompt_version": report.prompt_version,
        "categories": report.json_content.get("categories", []),
        "opportunities": report.json_content.get("opportunities", []),
        "markdown": report.markdown_content,
        "created_at": report.created_at,
    }


@router.get("/{report_id}")
async def get_project_report(
    project_id: str,
    report_id: str,
    format: Optional[str] = None,
    accept: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a specific historical research report by ID.
    Supports markdown or JSON via ?format=markdown|json or Accept header.
    """
    report = await ReportService.get_report(db, project_id, report_id)

    if format == "markdown" or (accept and "text/markdown" in accept):
        return PlainTextResponse(content=report.markdown_content, media_type="text/markdown")

    return {
        "id": str(report.id),
        "project_id": str(report.project_id),
        "project_name": report.json_content.get("project_name", report.title),
        "title": report.title,
        "generated_at": report.created_at.isoformat(),
        "categories_count": report.json_content.get("categories_count", 0),
        "opportunities_count": report.json_content.get("opportunities_count", 0),
        "evidence_count": report.evidence_count,
        "pending_reviews_count": report.pending_reviews_count,
        "model_version": report.model_version,
        "prompt_version": report.prompt_version,
        "categories": report.json_content.get("categories", []),
        "opportunities": report.json_content.get("opportunities", []),
        "markdown": report.markdown_content,
        "created_at": report.created_at,
    }
