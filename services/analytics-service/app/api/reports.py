from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.analytics import ReportCreate, ReportResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.post("/reports", response_model=ReportResponse, status_code=201)
async def create_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new analytics report"""
    service = ReportService(db)

    # Create report record
    report = await service.create_report(
        user_id=current_user["user_id"],
        report_data=report_data
    )

    # Generate report in background
    background_tasks.add_task(service.generate_report, report.id)

    return report


@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all reports for the current user"""
    service = ReportService(db)
    return await service.list_reports(
        user_id=current_user["user_id"],
        skip=skip,
        limit=limit
    )


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific report"""
    service = ReportService(db)
    report = await service.get_report(
        report_id=report_id,
        user_id=current_user["user_id"]
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Download a report file"""
    service = ReportService(db)
    report = await service.get_report(
        report_id=report_id,
        user_id=current_user["user_id"]
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report is not ready. Status: {report.status}"
        )

    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file not found")

    # Set correct media type based on format
    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "md": "text/markdown"
    }
    media_type = media_types.get(report.format, "application/octet-stream")

    # Clean filename (remove special characters)
    safe_filename = "".join(c for c in report.name if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"{safe_filename}.{report.format}"

    return FileResponse(
        report.file_path,
        filename=filename,
        media_type=media_type
    )
