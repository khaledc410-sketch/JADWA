from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1 import auth, projects, reports, admin, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic in production)
    if settings.ENVIRONMENT == "development":
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            print(f"WARNING: Could not connect to database on startup: {e}")
            print(
                "The server will start, but DB-dependent endpoints will fail until PostgreSQL is running."
            )
    # Pre-load seed data into memory
    from app.services.data_tools import load_seed

    for source in [
        "sama_rates",
        "rfta_franchises",
        "gastat_demographics",
        "hrdf_nitaqat_ratios",
        "vision2030_kpis",
        "mci_licenses",
        "moh_healthcare",
        "moe_education",
        "citc_tech",
        "sta_tourism",
        "modon_manufacturing",
        "logistics_transport",
        "templates",
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
app.include_router(templates.router, prefix="/api/v1")


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
