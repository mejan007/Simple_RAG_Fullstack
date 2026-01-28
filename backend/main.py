from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.routers import documents, chat


from backend.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Simple RAG API...")
    # Pre-warm services (Singleton initialization)
    from backend.dependencies import get_rag_service
    
    logger.info("Pre-warming RAG Service (this might download models on first run)...")
    get_rag_service()
    
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down Simple RAG API...")
    # Shutdown logic can go here


app = FastAPI(
    title="Simple RAG API",
    description="Modern RAG Fullstack Backend with LCEL",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/", tags=["General"])
async def root():
    """Redirect to Swagger UI."""
    return RedirectResponse(url="/docs")
