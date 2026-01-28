from typing import Iterator

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank

from backend.config import Settings
from backend.services.vector_store import VectorStoreService
from backend.logger import logger


class RAGService:
    """Service for RAG operations using LCEL."""
    
    RAG_PROMPT = """Use the context provided to answer the user's question.
If you cannot answer based on the context, say you don't know.

Context:
{context}

Question: {query}

Answer:"""

    QUERY_REWRITE_PROMPT = """Rewrite this query for semantic search. 
Return only the rewritten query, no comments.

Query: {query}

Rewritten:"""

    def __init__(self, settings: Settings, vector_store_service: VectorStoreService):
        self.settings = settings
        self.vector_store = vector_store_service
        
        # Initialize LLM
        self._llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            google_api_key=settings.gemini_api_key
        )
        
        # Initialize reranker
        self._reranker = FlashrankRerank(top_n=settings.rerank_top_n)
        self._reranker.model_rebuild()
        
        # Initialize prompts
        self._rag_prompt = PromptTemplate.from_template(self.RAG_PROMPT)
        self._rewrite_prompt = PromptTemplate.from_template(self.QUERY_REWRITE_PROMPT)
    
    def _rewrite_query(self, query: str) -> str:
        """Rewrite query for better semantic search."""
        logger.info(f"Rewriting query: {query[:50]}...")
        prompt = self._rewrite_prompt.format(query=query)
        response = self._llm.invoke(prompt)
        logger.info(f"Rewritten query: {response.content[:50]}...")
        return response.content
    
    def _retrieve_and_rerank(self, query: str) -> list[Document]:
        """Retrieve documents and rerank them."""
        # Rewrite query
        rewritten = self._rewrite_query(query)
        
        # Retrieve
        logger.info("Retrieving documents from vector store...")
        docs = self.vector_store.retriever.invoke(rewritten)
        
        # Rerank if we have documents
        if docs:
            logger.info(f"Reranking {len(docs)} documents...")
            docs = list(self._reranker.compress_documents(docs, rewritten))
            logger.info(f"Reranked to {len(docs)} documents.")
        
        return docs
    
    @staticmethod
    def _format_docs(docs: list[Document]) -> str:
        """Format documents into context string."""
        return "\n\n".join(doc.page_content for doc in docs)
    
    def invoke(self, query: str) -> dict:
        """Run RAG chain and return response."""
        # Retrieve and rerank
        docs = self._retrieve_and_rerank(query)
        
        # Format context
        context = self._format_docs(docs)
        
        # Generate response
        prompt = self._rag_prompt.format(context=context, query=query)
        response = self._llm.invoke(prompt)
        
        return {
            "answer": response.content,
            "sources": [doc.page_content[:100] + "..." for doc in docs]
        }
    
    def stream(self, query: str) -> Iterator[str]:
        """Stream RAG response token by token."""
        # Retrieve and rerank
        docs = self._retrieve_and_rerank(query)
        
        # Format context
        context = self._format_docs(docs)
        logger.info(f"Context length: {len(context)} chars")
        
        # Stream response
        prompt = self._rag_prompt.format(context=context, query=query)
        logger.info("Starting LLM stream...")
        
        try:
            chunk_count = 0
            for chunk in self._llm.stream(prompt):
                content = chunk.content if hasattr(chunk, "content") else str(chunk)
                if content:
                    chunk_count += 1
                    logger.debug(f"Yielding chunk {chunk_count}: {content[:10]}...")
                    yield content
            logger.info(f"LLM stream finished. Total chunks: {chunk_count}")
        except Exception as e:
            logger.error(f"Error during LLM streaming: {str(e)}")
            raise e
