from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1 import auth, projects, reports, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic in production)
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)
    # Pre-load seed data into memory
    from app.services.data_tools import load_seed

    for source in [
        "sama_rates",
        "rfta_franchises",
        "gastat_demographics",
        "hrdf_nitaqat_ratios",
        "vision2030_kpis",
        "mci_licenses",
    ]:
        load_seed(source)
    yield


app = FastAPI(
    title="JADWA API — جدوى",
    description="Arabic-first AI Feasibility Study Platform for Saudi Arabia",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "name_ar": settings.APP_NAME_AR,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
