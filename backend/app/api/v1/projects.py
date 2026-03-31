from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    sector: str  # franchise | real_estate | fnb | retail
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    intake_data: dict = {}


class ProjectResponse(BaseModel):
    id: str
    sector: str
    name_ar: Optional[str]
    name_en: Optional[str]
    status: str
    intake_data: dict

    class Config:
        from_attributes = True


VALID_SECTORS = {"franchise", "real_estate", "fnb", "retail"}


@router.post("/", response_model=ProjectResponse)
def create_project(
    req: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.sector not in VALID_SECTORS:
        raise HTTPException(400, f"Invalid sector. Must be one of: {VALID_SECTORS}")
    project = Project(
        user_id=current_user.id,
        sector=req.sector,
        name_ar=req.name_ar,
        name_en=req.name_en,
        intake_data=req.intake_data,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse(
        id=str(project.id),
        sector=project.sector,
        name_ar=project.name_ar,
        name_en=project.name_en,
        status=project.status,
        intake_data=project.intake_data,
    )


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return [
        ProjectResponse(
            id=str(p.id),
            sector=p.sector,
            name_ar=p.name_ar,
            name_en=p.name_en,
            status=p.status,
            intake_data=p.intake_data,
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    return ProjectResponse(
        id=str(project.id),
        sector=project.sector,
        name_ar=project.name_ar,
        name_en=project.name_en,
        status=project.status,
        intake_data=project.intake_data,
    )


@router.put("/{project_id}/intake")
def update_intake(
    project_id: str,
    intake_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    project.intake_data = intake_data
    db.commit()
    return {"message": "Intake data updated"}
