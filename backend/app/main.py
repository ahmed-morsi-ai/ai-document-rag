from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router

app = FastAPI(
    title="AI Document RAG API",
    version="1.0.0",
    description="Production-ready AI document question answering API",
)


app.include_router(auth_router)
app.include_router(documents_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}