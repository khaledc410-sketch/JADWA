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


@router.post("/{run_id}/retry")
def retry_report(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retry a failed report run, resuming from last checkpoint."""
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Report run not found")

    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")

    if run.status not in ("failed",):
        raise HTTPException(400, "Can only retry failed runs")

    run.status = "queued"
    run.error_message = None
    run.progress_percent = 0
    run.current_step = "إعادة المحاولة..."
    db.commit()

    from app.tasks.pipeline import run_report_pipeline

    task = run_report_pipeline.delay(str(run.id), "ar")
    run.celery_task_id = task.id
    run.status = "running"
    db.commit()

    return {"run_id": str(run.id), "status": "retrying"}


@router.get("/{run_id}/agent-logs")
def get_agent_logs(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get agent logs for a report run (user must own the project)."""
    from app.models.report import AgentLog

    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")

    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(403, "Not authorized")

    logs = (
        db.query(AgentLog)
        .filter(AgentLog.run_id == run_id)
        .order_by(AgentLog.started_at)
        .all()
    )

    return [
        {
            "agent_name": log.agent_name,
            "status": log.status,
            "tokens_used": log.tokens_used or 0,
            "output_data": log.output_data if log.output_data else {},
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        }
        for log in logs
    ]


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

    # Generate presigned URL from S3 key
    from app.services.storage import get_storage

    try:
        storage = get_storage()
        presigned_url = storage.generate_presigned_url(output.pdf_url, expires_in=3600)
        return {
            "pdf_url": presigned_url,
            "page_count": output.page_count,
            "expires_in_seconds": 3600,
        }
    except Exception:
        # Fallback to stored URL (local path or direct URL)
        return {"pdf_url": output.pdf_url, "page_count": output.page_count}
