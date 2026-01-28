"""
Test script to verify the RAG chain with Google GenAI integration.
This script tests the basic functionality of the RAG chain.
"""

from RAGChain import rag_chain, vector_store, text_splitter

def test_rag_chain():
    print("=" * 60)
    print("Testing RAG Chain with Google GenAI")
    print("=" * 60)
    
    # Step 1: Add a sample document to the vector store
    print("\n1. Adding sample document to vector store...")
    sample_text = """
    Google Gemini is a family of multimodal large language models developed by Google DeepMind.
    It is designed to understand and generate text, code, images, audio, and video.
    Gemini 1.5 Flash is optimized for speed and efficiency, making it ideal for high-volume tasks.
    The model supports a context window of up to 1 million tokens.
    """
    
    try:
        texts = text_splitter.create_documents([sample_text])
        ids = vector_store.add_documents(texts)
        print(f"   ✓ Successfully added {len(ids)} document chunks")
        print(f"   Document IDs: {ids}")
    except Exception as e:
        print(f"   ✗ Error adding documents: {e}")
        return
    
    # Step 2: Test vector store similarity search
    print("\n2. Testing vector store similarity search...")
    try:
        results = vector_store.similarity_search("What is Gemini?", k=2)
        print(f"   ✓ Found {len(results)} similar chunks")
        for i, doc in enumerate(results, 1):
            print(f"   Chunk {i}: {doc.page_content[:100]}...")
    except Exception as e:
        print(f"   ✗ Error in similarity search: {e}")
        return
    
    # Step 3: Test RAG chain invoke
    print("\n3. Testing RAG chain invoke...")
    query = "What is Google Gemini?"
    try:
        response = rag_chain.invoke(query)
        print(f"   Query: {query}")
        print(f"   ✓ Response: {response}")
    except Exception as e:
        print(f"   ✗ Error invoking RAG chain: {e}")
        return
    
    # Step 4: Test RAG chain streaming
    print("\n4. Testing RAG chain streaming...")
    query = "What is Gemini 1.5 Flash optimized for?"
    try:
        print(f"   Query: {query}")
        print(f"   ✓ Streaming response: ", end="")
        for token in rag_chain.stream(query):
            print(token, end="", flush=True)
        print()  # New line after streaming
    except Exception as e:
        print(f"\n   ✗ Error streaming from RAG chain: {e}")
        return
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)

if __name__ == "__main__":
    test_rag_chain()
