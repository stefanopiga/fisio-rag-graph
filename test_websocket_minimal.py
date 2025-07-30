"""
Test script minimo per debug WebSocket
"""
import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def test_websocket():
    uri = "ws://127.0.0.1:8058/ws"
    session_id = str(uuid.uuid4())
    
    print(f"[{datetime.now().isoformat()}] Connecting to {uri}")
    print(f"Session ID: {session_id}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[{datetime.now().isoformat()}] Connected successfully")
            
            # Ricevi messaggio di conferma
            confirmation = await websocket.recv()
            print(f"[{datetime.now().isoformat()}] Received confirmation: {confirmation}")
            
            # Invia messaggio di chat
            chat_message = {
                "type": "chat",
                "session_id": session_id,
                "user_id": "test_user",
                "data": {
                    "message": "Ciao, come funziona la riabilitazione della spalla?",
                    "search_type": "hybrid"
                }
            }
            
            print(f"[{datetime.now().isoformat()}] Sending chat message...")
            await websocket.send(json.dumps(chat_message))
            print(f"[{datetime.now().isoformat()}] Message sent")
            
            # Ricevi risposte
            response_count = 0
            timeout = 30  # 30 secondi timeout
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    # Timeout check
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        print(f"[{datetime.now().isoformat()}] Timeout after {timeout}s")
                        break
                    
                    # Receive with timeout
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_count += 1
                    print(f"[{datetime.now().isoformat()}] Response {response_count}: {response[:200]}...")
                    
                    # Parse response
                    try:
                        data = json.loads(response)
                        if data.get("type") == "stream_end":
                            print(f"[{datetime.now().isoformat()}] Stream completed")
                            break
                    except json.JSONDecodeError:
                        print(f"[{datetime.now().isoformat()}] Failed to parse response as JSON")
                        
                except asyncio.TimeoutError:
                    print(f"[{datetime.now().isoformat()}] No response received in 5s")
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print(f"[{datetime.now().isoformat()}] Connection closed by server")
                    break
                    
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"Starting WebSocket test at {datetime.now().isoformat()}")
    asyncio.run(test_websocket())
    print(f"Test completed at {datetime.now().isoformat()}")