from fastapi import FastAPI
from sqlalchemy import text

from app.db.database import AsyncSessionLocal


app = FastAPI(
    title="AI Document RAG API",
    description="Production-ready AI document question answering API",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-document-rag",
    }


@app.get("/health/db")
async def database_health_check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "status": "healthy",
        "database": "connected",
        "result": value,
    }