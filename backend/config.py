from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    gemini_api_key: str
    
    # Model Configuration
    llm_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/text-embedding-004"
    llm_temperature: float = 0.1
    
    # Vector Store Configuration
    chroma_collection_name: str = "rag_collection"
    chroma_persist_directory: str = "./chroma_data"  # Default to local persistence
    
    # Text Splitter Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Reranker Configuration
    rerank_top_n: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
