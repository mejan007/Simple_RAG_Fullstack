# Imports

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
# from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import FlashrankRerank

from dotenv import load_dotenv
from vectorizer import vector_store
# Load Environment Vars
load_dotenv()

# Initialize the LLM
llm = OllamaLLM(model = "llama3.2", temperature = 0.1)

# with open("data/2024_state_of_the_union.txt") as f:
#     state_of_the_union = f.read()


# Initialize Text Splitter
# initialize LangChain’s text splitter to handle chunking the uploaded documents 
# before embedding and storing them in the vector store.
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap = 200,
    length_function = len
)

# # Create Documents (Chunks) From File
# texts = text_splitter.create_documents([state_of_the_union])

# # Save Document Chunks to Vector Store
# ids = vector_store.add_documents(texts)

# Set Chroma as the Retriever
retriever = vector_store.as_retriever()

# results = vector_store.similarity_search(
#     'Who invaded Ukraine?',
#     k=2
# )

# for res in results:
#     print(f"* {res.page_content} [{res.metadata}]\n\n")

# Custom Prompt is designed to ensure the chain answers only based on the retrieved context, 
# avoiding responses derived from the LLM’s training data. 
# For testing, the prompt explicitly instructs the chain to apologize if it 
# cannot answer using the provided context, ensuring that the system behaves as expected.

# Create the Prompt Template


prompt_template = """Use the context provided to answer the user's question 
below. If you do not know the answer based on the context provided, tell the
user that you do not know the answer to their question based on the context
provided and that you are sorry.
context: {context}

question: {query}

answer: """

# # Create Prompt Instance from template
custom_rag_prompt = PromptTemplate.from_template(prompt_template)


# Pre-retrieval Query Writing
'''
We create a dedicated function that transforms the user's original query 
into a concise statement or paragraph. This rewritten query enhances semantic 
similarity searches within the vector store, ensuring that the most relevant 
chunks are retrieved.
'''

# Pre-retrieval Query Rewriting Function
def query_rewrite(query: str, llm: OllamaLLM):

    # Rewritten Query Prompt
    query_rewrite_prompt = f"""You are a helpful assistant that takes a
    user's query and turns it into a short statement or paragraph so that
    it can be used in a semantic similarity search on a vector database to
    return the most similar chunks of content based on the rewritten query.
    Please make no comments, just return the rewritten query.
    \n\nquery: {query}\n\nai: """

    # Invoke LLM
    retrieval_query = llm.invoke(query_rewrite_prompt)

    # Return Generated Retrieval Query
    return retrieval_query


def format_docs(docs):
    '''
    Utility function that formats the semantically similar context document chunks returned by the 
    vector store. These chunks are essential for providing the model with the 
    context needed to answer the user's query. 

    This function takes a list of LangChain-formatted document objects and extracts the 
    page_content field from each document. 
    It then concatenates these contents into a single formatted string, 
    separated by double newlines. 
    This formatted string is what we will pass into the prompt as the model's context.
    '''
    return "\n\n".join(doc.page_content for doc in docs)
# Post-retrieval Document Reranking

compressor = FlashrankRerank()

compressor.model_rebuild()
'''
It uses Flashrank, a lightweight and fast neural re-ranker that scores 
documents based on how relevant they are to the query. 
'''

compression_retriever = ContextualCompressionRetriever(
    base_compressor = compressor,
    base_retriever= retriever
)
'''
Calls base_retriever to get initial documents.

Then passes those to base_compressor (Flashrank here) to re-rank or filter. 
'''

class RAGChain:

    def __init__(self, llm: OllamaLLM, retriever: ContextualCompressionRetriever,
                 prompt: PromptTemplate):
        self.llm = llm
        self.retriever = retriever
        self.prompt = prompt

    #  Run Chain Function - same naming convention as LangChain
    def invoke(self, query: str):
        # Pre-retrieval Query Rewrite
        retrieval_query = query_rewrite(query, self.llm)
        
        # Retrieval w/ Post-retrieval Reranking
        docs = self.retriever.invoke(retrieval_query)

        # Format Docs for Context String
        context = format_docs(docs)

        # Prompt Template
        final_prompt = self.prompt.format(context=context, query=query)

        # LLM Invoke
        return llm.invoke(final_prompt)


    # Adding stream functionality so, that response isn't a single chunk but can be stramed
    # Stream invoke of rag chain
    def stream(self, query: str):

        '''
        This function closely mirrors the existing invoke function but introduces streaming 
        capabilities by sending tokens as they are generated. The process involves 
        rewriting the query using the LLM, retrieving and reranking relevant documents, 
        formatting the documents into a context string, and finally streaming the response token 
        by token from the LLM.
        '''

        # Advanced RAG: Pre-retrieval Query Rewrite
        retrieval_query = query_rewrite(query, self.llm)

        # Retrieval with Post-retrieval Reranking
        docs = self.retriever.invoke(retrieval_query)

        # Format Docs for context string
        context = format_docs(docs)

        # Prompt Template
        final_prompt = self.prompt.format(context = context, query = query)

        # Stream the response from LLM
        for token in self.llm.stream(final_prompt):
            yield token
    
# Initialize Custom RAG Chain
rag_chain = RAGChain(llm, compression_retriever, custom_rag_prompt)

# Define the query
# query = 'Is Russia the aggressor?'

# # Invoke the chain
# response = rag_chain.invoke(query)

# # Print Output
# print(response)
# print("\n\n--------------------------------------------")
# # print(type(response))


