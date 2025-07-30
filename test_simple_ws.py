import asyncio
import json
import websockets

async def simple_test():
    print("Connecting to ws://127.0.0.1:8058/ws")
    try:
        async with websockets.connect("ws://127.0.0.1:8058/ws") as ws:
            print("Connected!")
            
            # Ricevi conferma
            msg = await ws.recv()
            print(f"Received: {msg}")
            
            # Invia messaggio
            chat_msg = {
                "type": "chat",
                "session_id": "test-session",
                "user_id": "test-user",
                "data": {
                    "message": "Test message",
                    "search_type": "hybrid"
                }
            }
            
            print(f"Sending: {json.dumps(chat_msg)}")
            await ws.send(json.dumps(chat_msg))
            
            # Aspetta risposta
            print("Waiting for response...")
            for i in range(10):
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    print(f"Response {i+1}: {response}")
                except asyncio.TimeoutError:
                    print(f"Timeout {i+1}")
                    
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(simple_test())