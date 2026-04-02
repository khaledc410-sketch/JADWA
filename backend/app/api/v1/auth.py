from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name_ar: Optional[str] = None
    full_name_en: Optional[str] = None
    preferred_language: str = "ar"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    preferred_language: str


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        full_name_ar=req.full_name_ar,
        full_name_en=req.full_name_en,
        preferred_language=req.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        preferred_language=user.preferred_language,
    )


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        preferred_language=user.preferred_language,
    )


@router.get("/me")
def get_me(db: Session = Depends(get_db)):
    """Placeholder — use get_current_user dependency in protected routes."""
    return {"message": "Use Authorization header with Bearer token"}


@router.post("/bootstrap-admin")
def bootstrap_admin(db: Session = Depends(get_db)):
    """One-time setup: promote the first registered user to admin. Only works if no admins exist."""
    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")
    first_user = db.query(User).order_by(User.created_at).first()
    if not first_user:
        raise HTTPException(status_code=404, detail="No users found")
    first_user.role = "admin"
    db.commit()
    return {"message": f"User {first_user.email} promoted to admin"}
