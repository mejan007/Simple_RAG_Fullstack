from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from backend.config import Settings
from backend.logger import logger


class VectorStoreService:
    """Service for managing the vector store."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Initialize embeddings
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.gemini_api_key
        )
        
        # Initialize vector store
        logger.info(f"Initializing ChromaDB with collection: {settings.chroma_collection_name}")
        self._vector_store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=self._embeddings,
            persist_directory=settings.chroma_persist_directory
        )
        
        # Initialize text splitter
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len
        )
    
    @property
    def retriever(self):
        """Get the retriever for RAG chain."""
        return self._vector_store.as_retriever()
    
    def add_documents(self, text: str, metadata: dict | None = None) -> list[str]:
        """Split text into chunks and add to vector store."""
        logger.info("Adding documents to vector store...")
        documents = self._text_splitter.create_documents(
            texts=[text],
            metadatas=[metadata] if metadata else None
        )
        ids = self._vector_store.add_documents(documents)
        logger.info(f"Successfully added {len(ids)} chunks.")
        return ids
    
    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        """Perform similarity search."""
        return self._vector_store.similarity_search(query, k=k)
    
    def get_status(self) -> dict:
        """Get vector store status."""
        collection = self._vector_store._collection
        doc_count = len(collection.get()["ids"])
        return {
            "collection_name": self.settings.chroma_collection_name,
            "document_count": doc_count,
            "is_persistent": self.settings.chroma_persist_directory is not None
        }
