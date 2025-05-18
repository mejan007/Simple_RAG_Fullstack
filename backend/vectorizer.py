from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# Get Embeddings Model
embeddings = OllamaEmbeddings(model = "mxbai-embed-large")

vector_store = Chroma(
    collection_name="test_collection",
    embedding_function=embeddings
)


