from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.companies import router as companies_router
from app.api.icps import router as icps_router
from app.api.outreach import router as outreach_router
from app.api.products import router as products_router
from app.db.database import check_database
from app.db.schema import create_tables
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.
    """

    create_tables()

    yield


app = FastAPI(
    title="AI Buyer Intelligence & Outreach Engine",
    description=(
        "Intelligence, prioritisation, enrichment and "
        "outreach workflow for B2B prospecting."
    ),
    version="0.3.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "name": "AI Buyer Intelligence & Outreach Engine",
        "version": "0.3.0",
        "status": "running",
    }


@app.get("/health")
def health():
    database_ok = check_database()

    return {
        "status": (
            "healthy"
            if database_ok
            else "unhealthy"
        ),
        "database": (
            "connected"
            if database_ok
            else "disconnected"
        ),
    }


app.include_router(products_router)
app.include_router(icps_router)
app.include_router(companies_router)
app.include_router(outreach_router)
