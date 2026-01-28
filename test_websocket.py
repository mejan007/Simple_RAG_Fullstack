import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8090/chat/ws/stream"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Send query
            query = {"query": "What is the capital of Mars according to the text?"}
            print(f"Sending: {query}")
            await websocket.send(json.dumps(query))
            
            # Receive loop
            while True:
                response = await websocket.recv()
                print(f"Received: {response}")
                if response == "<<END>>" or response == "<<E:NO_QUERY>>":
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
