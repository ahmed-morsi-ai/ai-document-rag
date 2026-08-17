from fastapi import FastAPI

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