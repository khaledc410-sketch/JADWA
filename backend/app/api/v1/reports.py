import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.report import ReportRun, ReportOutput

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{project_id}/generate")
def generate_report(
    project_id: str,
    language: str = "ar",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger the AI pipeline for a project. Returns run_id for polling."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    if not project.intake_data:
        raise HTTPException(
            400, "Intake data is empty. Complete the intake form first."
        )

    # Create report run record
    run = ReportRun(project_id=project.id, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)

    # Dispatch to Celery
    from app.tasks.pipeline import run_report_pipeline

    task = run_report_pipeline.delay(str(run.id), language)

    # Store celery task id
    run.celery_task_id = task.id
    run.status = "running"
    db.commit()

    return {"run_id": str(run.id), "status": "queued"}


@router.get("/{run_id}/status")
def get_run_status(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Report run not found")
    return {
        "run_id": str(run.id),
        "status": run.status,
        "progress_percent": run.progress_percent,
        "current_step": run.current_step,
        "pipeline_state": run.pipeline_state,
        "error_message": run.error_message,
    }


@router.get("/{run_id}/stream")
async def stream_progress(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Server-Sent Events endpoint for real-time pipeline progress."""

    async def event_generator():
        while True:
            run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
            if not run:
                yield f"data: {json.dumps({'error': 'Run not found'})}\n\n"
                break
            data = {
                "status": run.status,
                "progress": run.progress_percent,
                "step": run.current_step,
            }
            yield f"data: {json.dumps(data)}\n\n"
            if run.status in ("completed", "failed"):
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{run_id}/download")
def download_report(
    run_id: str,
    language: str = "ar",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    output = (
        db.query(ReportOutput)
        .filter(
            ReportOutput.run_id == run_id,
            ReportOutput.language == language,
        )
        .first()
    )
    if not output or not output.pdf_url:
        raise HTTPException(404, "Report not ready or not found")
    return {"pdf_url": output.pdf_url, "page_count": output.page_count}
