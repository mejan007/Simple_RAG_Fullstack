from pydantic import BaseModel, Field


# ============================================================
# Document Upload
# ============================================================

class FileUploadRequest(BaseModel):
    """Request model for file upload."""
    file_data: str = Field(..., description="Base64 encoded file content")


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    message: str
    document_ids: list[str]
    chunks_count: int


# ============================================================
# Vector Search
# ============================================================

class SearchRequest(BaseModel):
    """Request model for similarity search."""
    query: str = Field(..., description="Search query string")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")


class SearchResult(BaseModel):
    """Single search result."""
    content: str
    metadata: dict = Field(default_factory=dict)
    score: float | None = None


class SearchResponse(BaseModel):
    """Response model for similarity search."""
    results: list[SearchResult]
    count: int


# ============================================================
# Vector Store Status
# ============================================================

class VectorStatusResponse(BaseModel):
    """Response model for vector store status."""
    collection_name: str
    document_count: int
    is_persistent: bool


# ============================================================
# RAG Chat
# ============================================================

class RAGRequest(BaseModel):
    """Request model for RAG query."""
    query: str = Field(..., min_length=1, description="User query")


class RAGResponse(BaseModel):
    """Response model for RAG query."""
    answer: str
    sources: list[str] = Field(default_factory=list)
