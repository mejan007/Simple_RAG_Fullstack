import base64
import asyncio
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect

from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
# from typing import List, Optional


from vectorizer import vector_store
from RAGChain import text_splitter, rag_chain

app = FastAPI()

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Redirect to SwaggerUI
@app.get("/", tags = ["General"])
def root():
    return RedirectResponse(url="/docs")


# Document Upload Endpoint

# We’ll require a Base64-encoded string representing the file’s content.
# This model is used to validate incoming data in Base64 format. 
class FileRequest(BaseModel):
    file_data: str # Base64 encoded file content string

# With the request model defined, we can now implement the POST function.

'''
Note that we are not using a persistent ChromaDB instance. 
As a result, each time we shut down or restart the FastAPI application, 
we will need to repopulate the vector database.
'''


# @app.post('/upload', tags = ["VectorDB"])
# def upload(request: FileRequest):
#     '''
#     This function begins by decoding the base64-encoded file string provided in the request.

#     If decoding fails, an exception is raised.

#     Once the file is successfully decoded, the content is split into chunks using 
#     the text_splitter imported from RAGChain.py file.

#     These chunks are then stored in the vector database. 
#     Finally, the function returns a success status along with the list of document IDs 
#     created and uploaded to the vector store to confirm the operation was successful.
#     '''
#     file_str = ""

#     try:
#         decoded_bytes = base64.b64decode(request.file_data)
#         # if request.file_data is "SGVsbG8gV29ybGQ=" (Base64 for "Hello World"), 
#         # it decodes to the bytes b'Hello World'.

#         file_str = decoded_bytes.decode("utf-8")
#         # The result is stored in file_str (e.g., file_str = "Hello World")
    
#     except Exception as e:
#         raise HTTPException(
#             status_code = status.HTTP_400_BAD_REQUEST,
#             detail = f"Invalid file data:{str(e)}"
#         )

#     if not file_str:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
#                             detail=f"Invalid file data: File is empty or null...")
    
#     # Create Documents (Chunks) from file
#     texts = text_splitter.create_documents([file_str])
#     '''
#         Takes a list containing the decoded file_str (the full text content).

#         Splits the text into chunks based on the text_splitter configuration.

#         Returns a list of LangChain Document objects, where each Document contains 
#         a chunk of text in its page_content field 

#         Document object which contains:
#         page_content: The text of the chunk (up to ~1000 characters).

#         metadata: Optional metadata (e.g., source or filename, though not used in our current code).
#     '''

#     # Save Document Chunks to Vector Store
#     ids = vector_store.add_documents(texts)
#     '''
#         Takes the list of Document objects (texts) from the previous step.

#         Generates embeddings for each document's page_content (using OllamaEmbeddings, as configured in RAGChain.py).

#         Stores the embeddings and document metadata in the Chroma vector store.

#         Returns a list of unique IDs (ids) assigned to the stored documents.
#     '''

#     # Return Success & List of Ids for created documents
#     return {
#         'status': status.HTTP_201_CREATED,
#         'uploaded_ids': ids
#     }

@app.post('/upload', tags=["VectorDB"])
def upload(request: FileRequest):
    '''
    This function begins by decoding the base64-encoded file string provided in the request.

    If decoding fails, an exception is raised.

    Once the file is successfully decoded, the content is split into chunks using 
    the text_splitter imported from RAGChain.py file.

    These chunks are then stored in the vector database. 
    Finally, the function returns a success status along with the list of document IDs 
    created and uploaded to the vector store to confirm the operation was successful.
    '''
    file_str = ""

    try:
        # Check if the base64 string is empty
        if not request.file_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file data provided"
            )
            
        decoded_bytes = base64.b64decode(request.file_data)
        file_str = decoded_bytes.decode("utf-8")
    
    except base64.binascii.Error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 encoding. Please check the file format."
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode file as UTF-8. Make sure you're uploading a text file."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file data: {str(e)}"
        )

    if not file_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file data: File is empty or null..."
        )
    
    # Create Documents (Chunks) from file
    try:
        texts = text_splitter.create_documents([file_str])
        
        # Save Document Chunks to Vector Store
        ids = vector_store.add_documents(texts)
        
        # Return Success & List of Ids for created documents
        return {
            'status': status.HTTP_201_CREATED,
            'uploaded_ids': ids,
            'chunks_count': len(ids)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


# Endpoint to get the status of vector DB
@app.get('/vector_status', tags=["VectorDB"])
def get_vector_status():
    '''
    Returns information about the current state of the vector store
    '''
    try:
        # This is a basic implementation - you may need to adjust based on your vector_store implementation
        collection = vector_store._collection
        doc_count = len(collection.get()['ids'])
        
        return {
            'status': status.HTTP_200_OK,
            'document_count': doc_count,
            'has_documents': doc_count > 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting vector store status: {str(e)}"
        )


# Semantic Similarity Search Endpoint

'''
We'll create a semantic similarity search endpoint to test whether the vector store was properly 
populated with document chunks. 
Like the previous endpoint, this will also be a POST request, so we start by defining a request class. 
'''

class SearchRequest(BaseModel):

    search_str: str # VectorDB search string (string to perform semantic search)
    n: int = 2 # Number of semantically similar chunks to return from VectorDB with default = 2


# POST: Returns Semantic Similarity Chunks based on a user's query
@app.post('/vector_search', tags = ["VectorDB"])
def similarity_search(request: SearchRequest):
    '''
        This endpoint takes the request as a parameter and uses the vector_store from RAGChain.py 
        to perform a semantic similarity search.

        The search retrieves the most relevant document chunks based on the provided query and returns them in the response. 
    '''
    try:

        results = vector_store.similarity_search(
            request.search_str,
            k = request.n
        )
    
        return {
            'status': status.HTTP_200_OK,
            'results': results
        }
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"Error in request: {str(e)}"
        )
    

# RAG Chain Endpoint
'''
We can now create the main POST endpoint to invoke the RAG chain. 
This endpoint will handle a user's query and interact with the rag_chain we 
previously defined in the RAGChain.py file.
'''

class RAGRequest(BaseModel):
    query: str # User Query


@app.post('/rag', tags = ["RAG"])
def rag_chain_invoke(request: RAGRequest):

    # The endpoint validates the input query to ensure it’s not empty or None. 
    # If the validation fails, it raises an HTTP exception.

    query = request.query

    if not query:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Error in request: Empty or None string value in query......"
        )
    
    # Query the RAG chain
    try:
        response = rag_chain.invoke(query)
        
        return {
            'status': status.HTTP_200_OK,
            'response': response
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RAG query: {str(e)}"
        )


'''
Unlike the standard HTTP request-response model, a WebSocket connection maintains an open 
communication channel between the endpoints, allowing bidirectional traffic to flow 
seamlessly. 

This setup lets us handle the initial request to establish the connection, stream 
responses from the LLM, and manage any errors or messages from either the frontend 
or backend, ensuring smooth communication and coordination between the two.
'''


# We define a Websocket endpoint using FastAPI's @app.websocket decorator.
@app.websocket("/ws/stream")
async def chat_stream(websocket: WebSocket):

    '''
        This endpoint will manage real-time communication between the backend and frontend.
        This function accepts a WebSocket object and waits for the connection to be established using websocket.accept().


        Once the connection is accepted, we use a try block to house the core logic for streaming data. 
        Inside the except block, we handle specific scenarios like WebSocketDisconnect, 
        which is triggered when the frontend disconnects.

        A general Exception block is also included to catch and log any other errors 
        that might arise during the WebSocket session.
    '''

    await websocket.accept()
    try:
        resp = ''
        while True:
            # Receive data from the Frontend
            data = await websocket.receive_json()

            # Check if the request data contains proper keys
            if 'query' not in data:
                await websocket.send_text('<<E:NO_QUERY>>')
                break
            
            # Get Query From Request Data
            query = data['query']

            # Check if vector store has documents
            collection = vector_store._collection
            if len(collection.get()['ids']) == 0:
                await websocket.send_text('No documents have been uploaded yet. Please upload a document first.')
                await websocket.send_text('<<END>>')
                continue

            # Stream the response
            for token in rag_chain.stream(query):
                await websocket.send_text(token)
                await asyncio.sleep(0)
                resp += token
            
            # Send Successful Completion response to the Frontend
            await websocket.send_text('<<END>>')

    # Websocket disconnected
    except WebSocketDisconnect:
        print("WebSocket Disconnected")

    # Any other exception
    except Exception as e:
        print(f"Error in Websocket connection: {e}")
        try:
            await websocket.send_text(f"Error: {str(e)}")
            await websocket.send_text('<<END>>')
        except:
            pass # If we can't send the error, the connection is likely already closed


