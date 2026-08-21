from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DOCUMENT_STORAGE_DIR: Path = Path("storage")
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_STORE_DIR: Path = Path("vector_store")
    VECTOR_COLLECTION_NAME: str = "document_chunks"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4"
    OLLAMA_TIMEOUT_SECONDS: float = 120.0

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()