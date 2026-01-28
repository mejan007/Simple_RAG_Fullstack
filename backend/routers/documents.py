import base64
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from backend.models.schemas import (
    FileUploadResponse, 
    SearchRequest, 
    SearchResponse,
    SearchResult,
    VectorStatusResponse
)
from backend.services.vector_store import VectorStoreService
from backend.dependencies import get_vector_store_service
from backend.logger import logger

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """Receive file via multipart form-data, extract text, and add to vector store."""
    logger.info(f"Received file upload request: {file.filename}")
    try:
        content = await file.read()
        
        # Check for PDF magic number (%PDF-)
        if file.filename.lower().endswith(".pdf") or content.startswith(b"%PDF-"):
            logger.info(f"Processing PDF: {file.filename}")
            import io
            from pypdf import PdfReader
            
            pdf_stream = io.BytesIO(content)
            reader = PdfReader(pdf_stream)
            file_str = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    file_str += text + "\n"
        else:
            logger.info(f"Processing text file: {file.filename}")
            file_str = content.decode("utf-8")
            
    except Exception as e:
        logger.error(f"Error processing uploaded file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file data or format: {str(e)}"
        )

    if not file_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    try:
        ids = vector_store.add_documents(file_str)
        return FileUploadResponse(
            message="Document uploaded successfully",
            document_ids=ids,
            chunks_count=len(ids)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.post("/search", response_model=SearchResponse)
async def similarity_search(
    request: SearchRequest,
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """Perform semantic similarity search on uploaded documents."""
    try:
        docs = vector_store.similarity_search(request.query, k=request.top_k)
        results = [
            SearchResult(
                content=doc.page_content,
                metadata=doc.metadata
            ) for doc in docs
        ]
        return SearchResponse(results=results, count=len(results))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/status", response_model=VectorStatusResponse)
async def get_status(
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """Get current status of the vector store."""
    try:
        status_info = vector_store.get_status()
        return VectorStatusResponse(**status_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )
