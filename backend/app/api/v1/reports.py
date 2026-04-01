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


@router.get("/{run_id}/verdict")
def get_verdict(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the structured verdict data for a report run.
    Available as soon as the Compiler finishes (~75% progress), before PDF renders.
    """
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Report run not found")

    # Verify ownership
    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(403, "Not authorized")

    if run.verdict_data:
        return {"status": "ready", "verdict": run.verdict_data}

    # Verdict not yet available — still processing
    if run.status == "running":
        return {
            "status": "processing",
            "progress": run.progress_percent,
            "current_step": run.current_step,
        }

    # Failed or other states
    return {
        "status": run.status,
        "error_message": run.error_message,
    }


@router.get("/{run_id}/sections")
def get_sections(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all compiled report sections as structured JSON.
    For free tier users, returns truncated section previews.
    """
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Report run not found")

    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(403, "Not authorized")

    if not run.sections_data:
        if run.status == "running":
            return {"status": "processing", "progress": run.progress_percent}
        raise HTTPException(404, "Sections data not available")

    # Check if free tier — truncate sections
    from app.models.subscription import Subscription

    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status == "active",
        )
        .first()
    )
    is_free = sub and sub.plan == "free" if sub else True

    sections = run.sections_data
    if isinstance(sections, dict):
        section_list = sections.get("sections", sections)
    else:
        section_list = sections

    if is_free:
        # Return truncated previews for free tier
        truncated = {}
        if isinstance(section_list, dict):
            for key, val in section_list.items():
                if key == "executive_summary":
                    truncated[key] = val  # Always show full executive summary
                else:
                    preview = (
                        str(val)[:200] + "..." if len(str(val)) > 200 else str(val)
                    )
                    truncated[key] = {"preview": preview, "locked": True}
        return {
            "status": "ready",
            "sections": truncated,
            "upgrade_required": True,
        }

    return {"status": "ready", "sections": section_list, "upgrade_required": False}


@router.get("/{run_id}/sections/{section_name}")
def get_section(
    run_id: str,
    section_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single report section by name."""
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Report run not found")

    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(403, "Not authorized")

    if not run.sections_data:
        raise HTTPException(404, "Sections data not available")

    sections = run.sections_data
    if isinstance(sections, dict):
        section_list = sections.get("sections", sections)
    else:
        section_list = sections

    if isinstance(section_list, dict) and section_name in section_list:
        return {"section_name": section_name, "data": section_list[section_name]}

    raise HTTPException(404, f"Section '{section_name}' not found")


@router.post("/{run_id}/recalculate")
def recalculate_financials(
    run_id: str,
    overrides: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recalculate financials with user-modified assumptions.

    Accepts an overrides dict in the request body. Merges with original
    assumptions from the report's financial_model section and returns
    recalculated P&L, IRR, NPV, payback, break-even, and verdict.
    """
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Report run not found")

    # Verify ownership
    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(403, "Not authorized")

    if not run.sections_data:
        raise HTTPException(400, "Report sections not yet available")

    # Extract original financial assumptions from sections_data
    sections = run.sections_data
    if isinstance(sections, dict):
        section_list = sections.get("sections", sections)
    else:
        section_list = sections

    original_assumptions = {}  # type: dict
    if isinstance(section_list, dict):
        financial_model = section_list.get("financial_model", {})
        if isinstance(financial_model, dict):
            original_assumptions = financial_model.get("assumptions", financial_model)

    from app.services.financial_calculator import recalculate_scenario

    result = recalculate_scenario(original_assumptions, overrides)
    return result


@router.put("/{run_id}/sections/{section_name}")
def update_section(
    run_id: str,
    section_name: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update/override a specific section's content. Preserves original data."""
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Report run not found")

    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(403, "Not authorized")

    if not run.sections_data:
        raise HTTPException(400, "Report sections not yet available")

    sections = run.sections_data
    if isinstance(sections, dict):
        section_list = sections.get("sections", sections)
    else:
        section_list = sections

    if not isinstance(section_list, dict):
        raise HTTPException(400, "Sections data is not in expected format")

    if section_name not in section_list:
        raise HTTPException(404, f"Section '{section_name}' not found")

    # Store the update (merge with existing)
    existing = section_list[section_name]
    if isinstance(existing, dict) and isinstance(body, dict):
        section_list[section_name] = {**existing, **body, "_user_edited": True}
    else:
        section_list[section_name] = body

    # Write back
    if isinstance(sections, dict) and "sections" in sections:
        sections["sections"] = section_list
    else:
        sections = section_list

    run.sections_data = sections
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(run, "sections_data")
    db.commit()

    return {"status": "updated", "section_name": section_name}


@router.post("/{run_id}/sections/{section_name}/refine")
def refine_section(
    run_id: str,
    section_name: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI-powered section refinement.

    Body: { "instruction": "improve" | "expand" | "simplify" | "translate_en" | "custom",
            "custom_prompt": "..." (optional) }

    Calls Claude to refine the section content based on the instruction.
    """
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Report run not found")

    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(403, "Not authorized")

    if not run.sections_data:
        raise HTTPException(400, "Report sections not available")

    sections = run.sections_data
    if isinstance(sections, dict):
        section_list = sections.get("sections", sections)
    else:
        section_list = sections

    if not isinstance(section_list, dict) or section_name not in section_list:
        raise HTTPException(404, f"Section '{section_name}' not found")

    current_content = section_list[section_name]
    instruction = body.get("instruction", "improve")
    custom_prompt = body.get("custom_prompt", "")

    # Build the refinement prompt
    instruction_map = {
        "improve": "حسّن هذا القسم ليكون أكثر احترافية وتفصيلاً. أضف أرقام وتوصيات محددة.",
        "expand": "وسّع هذا القسم بمزيد من التفاصيل والتحليل العميق. أضف نقاط لم تُذكر.",
        "simplify": "بسّط هذا القسم ليكون مختصراً وواضحاً. أزل التكرار واحتفظ بالجوهر.",
        "translate_en": "Translate this section to professional English while keeping all data and figures.",
        "make_formal": "أعد صياغة هذا القسم بأسلوب استشاري رسمي (McKinsey tone).",
    }
    ai_instruction = instruction_map.get(instruction, custom_prompt or instruction)

    import anthropic
    from app.core.config import settings

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        content_str = json.dumps(current_content, ensure_ascii=False, indent=2)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            temperature=0.4,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"أنت مستشار أعمال أول. قم بتنفيذ التعليمات التالية على هذا القسم من دراسة الجدوى.\n\n"
                        f"التعليمات: {ai_instruction}\n\n"
                        f"القسم الحالي:\n```json\n{content_str[:3000]}\n```\n\n"
                        f"أعد القسم المحسّن بنفس البنية JSON. لا تضف نصاً خارج JSON."
                    ),
                }
            ],
        )

        refined_text = response.content[0].text
        # Try to parse as JSON
        import re

        json_match = re.search(r"\{[\s\S]*\}", refined_text)
        if json_match:
            try:
                refined = json.loads(json_match.group())
                section_list[section_name] = {**refined, "_ai_refined": True}
            except json.JSONDecodeError:
                section_list[section_name] = {
                    "content": refined_text,
                    "_ai_refined": True,
                }
        else:
            section_list[section_name] = {
                "content": refined_text,
                "_ai_refined": True,
            }

        # Save
        if isinstance(sections, dict) and "sections" in sections:
            sections["sections"] = section_list
        run.sections_data = sections
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(run, "sections_data")
        db.commit()

        return {
            "status": "refined",
            "section_name": section_name,
            "refined_content": section_list[section_name],
        }

    except Exception as e:
        raise HTTPException(500, f"AI refinement failed: {str(e)}")


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
