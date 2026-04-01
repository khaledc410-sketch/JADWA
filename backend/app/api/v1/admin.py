"""
Admin API endpoints — user management, report oversight, system stats, data cache.
All endpoints require admin role.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.models.subscription import Subscription
from app.models.project import Project
from app.models.report import ReportRun, ReportOutput, AgentLog
from app.models.data_cache import DataCache

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Schemas ─────────────────────────────────────────────────────────────────


class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ── Stats ───────────────────────────────────────────────────────────────────


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """System-wide metrics."""
    total_users = db.query(func.count(User.id)).scalar()
    active_users = (
        db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar()
    )
    total_projects = db.query(func.count(Project.id)).scalar()
    total_runs = db.query(func.count(ReportRun.id)).scalar()
    completed_runs = (
        db.query(func.count(ReportRun.id))
        .filter(ReportRun.status == "completed")
        .scalar()
    )
    failed_runs = (
        db.query(func.count(ReportRun.id)).filter(ReportRun.status == "failed").scalar()
    )
    total_tokens = db.query(func.sum(AgentLog.tokens_used)).scalar() or 0
    avg_gen_time = (
        db.query(func.avg(ReportOutput.generation_time_seconds)).scalar() or 0
    )
    cache_entries = db.query(func.count(DataCache.id)).scalar()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_projects": total_projects,
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "failed_runs": failed_runs,
        "total_tokens_used": total_tokens,
        "avg_generation_time_seconds": round(float(avg_gen_time), 1),
        "data_cache_entries": cache_entries,
    }


# ── Users ───────────────────────────────────────────────────────────────────


@router.get("/users")
def admin_list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Paginated user list."""
    users = (
        db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    )
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name_ar": u.full_name_ar,
            "full_name_en": u.full_name_en,
            "role": u.role,
            "is_active": u.is_active,
            "preferred_language": u.preferred_language,
            "project_count": db.query(func.count(Project.id))
            .filter(Project.user_id == u.id)
            .scalar(),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.get("/users/{user_id}")
def admin_get_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """User detail with subscription and projects."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
        .first()
    )

    projects = (
        db.query(Project)
        .filter(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .all()
    )

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name_ar": user.full_name_ar,
        "full_name_en": user.full_name_en,
        "role": user.role,
        "is_active": user.is_active,
        "phone": user.phone,
        "company_name_ar": user.company_name_ar,
        "company_cr_number": user.company_cr_number,
        "preferred_language": user.preferred_language,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "subscription": {
            "plan": subscription.plan,
            "status": subscription.status,
            "reports_used": subscription.reports_used_this_month,
        }
        if subscription
        else None,
        "projects": [
            {
                "id": str(p.id),
                "name_ar": p.name_ar,
                "sector": p.sector,
                "status": p.status,
            }
            for p in projects
        ],
    }


@router.put("/users/{user_id}")
def admin_update_user(
    user_id: str,
    body: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update user role or active status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if body.role is not None:
        if body.role not in ("owner", "member", "admin"):
            raise HTTPException(400, "Invalid role")
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "updated", "id": str(user.id)}


# ── Reports ─────────────────────────────────────────────────────────────────


@router.get("/reports")
def admin_list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Paginated report runs, filterable by status."""
    query = db.query(ReportRun).order_by(ReportRun.created_at.desc())
    if status:
        query = query.filter(ReportRun.status == status)
    runs = query.offset(skip).limit(limit).all()
    return [
        {
            "run_id": str(r.id),
            "project_id": str(r.project_id),
            "status": r.status,
            "progress_percent": r.progress_percent,
            "current_step": r.current_step,
            "error_message": r.error_message,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


@router.get("/reports/{run_id}/logs")
def admin_get_agent_logs(
    run_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Agent execution logs for a report run."""
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
            "tokens_used": log.tokens_used,
            "error_message": log.error_message,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "duration_seconds": (
                (log.completed_at - log.started_at).total_seconds()
                if log.started_at and log.completed_at
                else None
            ),
            "output_data": log.output_data if log.output_data else {},
        }
        for log in logs
    ]


# ── Data Cache ──────────────────────────────────────────────────────────────


@router.get("/data-cache")
def admin_data_cache_status(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Data cache status grouped by source."""
    entries = db.query(DataCache).order_by(DataCache.source).all()
    by_source = {}
    for e in entries:
        if e.source not in by_source:
            by_source[e.source] = []
        by_source[e.source].append(
            {
                "cache_key": e.cache_key,
                "expires_at": e.expires_at.isoformat() if e.expires_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
        )
    return {"sources": by_source, "total_entries": len(entries)}


@router.post("/data-cache/refresh")
def admin_refresh_data_cache(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Re-seed data cache from JSON files."""
    from app.services.data_tools import seed_all_data, clear_cache

    clear_cache()
    count = seed_all_data(db)
    return {"status": "refreshed", "entries_updated": count}
