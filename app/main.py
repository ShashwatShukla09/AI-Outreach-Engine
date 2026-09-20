from fastapi import FastAPI

from app.db.database import check_database


app = FastAPI(
    title="AI Buyer Intelligence & Outreach Engine",
    description="Intelligence, prioritisation, enrichment and outreach workflow for B2B prospecting.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "AI Buyer Intelligence & Outreach Engine",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
def health():
    database_ok = check_database()

    return {
        "status": "healthy" if database_ok else "unhealthy",
        "database": "connected" if database_ok else "disconnected",
    }
