from functools import lru_cache
from fastapi import Depends
from backend.config import Settings, get_settings
from backend.services.vector_store import VectorStoreService
from backend.services.rag_chain import RAGService

@lru_cache()
def get_vector_store_service() -> VectorStoreService:
    """Dependency provider for VectorStoreService (Singleton)."""
    settings = get_settings()
    return VectorStoreService(settings)

@lru_cache()
def get_rag_service() -> RAGService:
    """Dependency provider for RAGService (Singleton)."""
    settings = get_settings()
    vector_store = get_vector_store_service()
    return RAGService(settings, vector_store)
