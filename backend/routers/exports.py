from typing import Optional
from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.auth import get_current_user
from backend.models.user import User
from backend.services.export_service import ExportService
from backend.schemas.export import ExportFormat

router = APIRouter(prefix="/projects/{project_id}/export", tags=["Exports"])


@router.get("/evidence")
async def export_evidence(
    project_id: str,
    format: ExportFormat = ExportFormat.CSV,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exports all active evidence records for a project in CSV or JSON format.
    - CSV format includes UTF-8 BOM, QUOTE_ALL quoting, and anonymized author pseudonyms.
    - JSON format returns structured objects with all evidence fields.
    """
    if format == ExportFormat.JSON:
        data = await ExportService.export_evidence_json(db, project_id)
        return JSONResponse(
            content=data,
            headers={"Content-Disposition": f'attachment; filename="evidence_{project_id}.json"'},
        )

    csv_content = await ExportService.export_evidence_csv(db, project_id)
    return Response(
        content=csv_content.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="evidence_{project_id}.csv"'},
    )


@router.get("/taxonomy")
async def export_taxonomy(
    project_id: str,
    format: ExportFormat = ExportFormat.CSV,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exports taxonomy categories for a project in CSV or JSON format.
    Includes category definitions, failure mechanisms, evidence counts, and representative excerpts.
    """
    if format == ExportFormat.JSON:
        data = await ExportService.export_taxonomy_json(db, project_id)
        return JSONResponse(
            content=data,
            headers={"Content-Disposition": f'attachment; filename="taxonomy_{project_id}.json"'},
        )

    csv_content = await ExportService.export_taxonomy_csv(db, project_id)
    return Response(
        content=csv_content.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="taxonomy_{project_id}.csv"'},
    )
