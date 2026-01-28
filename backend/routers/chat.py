from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from backend.models.schemas import RAGRequest, RAGResponse
from backend.services.rag_chain import RAGService
from backend.dependencies import get_rag_service
from backend.logger import logger

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/rag", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Invoke the RAG chain for a user query."""
    logger.info(f"Received RAG query: {request.query[:50]}...")
    try:
        result = rag_service.invoke(request.query)
        logger.info("Successfully processed RAG query")
        return RAGResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(e)}"
        )

@router.websocket("/ws/stream")
async def chat_stream(
    websocket: WebSocket,
    rag_service: RAGService = Depends(get_rag_service)
):
    """WebSocket endpoint for streaming RAG responses."""
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    try:
        while True:
            data = await websocket.receive_json()
            if "query" not in data:
                logger.warning("Received WebSocket message without query")
                await websocket.send_text("<<E:NO_QUERY>>")
                continue
            
            query = data["query"]
            logger.info(f"Received streaming query: {query[:50]}...")
            
            # Use the streaming method from RAGService
            count = 0
            for token in rag_service.stream(query):
                await websocket.send_text(token)
                count += 1
            logger.info(f"Sent {count} tokens to websocket")
            
            await websocket.send_text("<<END>>")
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
        await websocket.send_text("<<END>>")
