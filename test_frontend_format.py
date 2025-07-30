"""
Frontend WebSocket Debug Test
Questo script testa la comunicazione WebSocket con logging dettagliato
"""
import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def test_frontend_format():
    uri = "ws://127.0.0.1:8058/ws"
    session_id = str(uuid.uuid4())
    
    print(f"[{datetime.now().isoformat()}] Connecting to {uri}")
    print(f"Session ID: {session_id}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[{datetime.now().isoformat()}] Connected successfully")
            
            # Ricevi messaggio di conferma
            confirmation = await websocket.recv()
            print(f"[{datetime.now().isoformat()}] Received confirmation:")
            print(json.dumps(json.loads(confirmation), indent=2))
            
            # Invia messaggio di chat
            chat_message = {
                "type": "chat",
                "session_id": session_id,
                "user_id": "test_user",
                "data": {
                    "message": "Dimmi solo: ciao",
                    "search_type": "hybrid"
                }
            }
            
            print(f"\n[{datetime.now().isoformat()}] Sending chat message...")
            await websocket.send(json.dumps(chat_message))
            print(f"[{datetime.now().isoformat()}] Message sent")
            
            # Ricevi risposte con formato dettagliato
            response_count = 0
            text_chunks = []
            timeout = 30
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        print(f"\n[{datetime.now().isoformat()}] Timeout after {timeout}s")
                        break
                    
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_count += 1
                    
                    # Parse and display response
                    try:
                        data = json.loads(response)
                        print(f"\n[{datetime.now().isoformat()}] Response {response_count}:")
                        print(f"  Type: {data.get('type')}")
                        print(f"  Data: {json.dumps(data.get('data', {}), indent=4)}")
                        
                        # Collect text chunks
                        if data.get('type') == 'text' and data.get('data', {}).get('content'):
                            text_chunks.append(data['data']['content'])
                            
                        if data.get("type") == "completed":
                            print(f"\n[{datetime.now().isoformat()}] Stream completed")
                            break
                            
                    except json.JSONDecodeError:
                        print(f"[{datetime.now().isoformat()}] Failed to parse response: {response}")
                        
                except asyncio.TimeoutError:
                    print(f"\n[{datetime.now().isoformat()}] No response received in 5s")
                    continue
                    
            # Show assembled message
            if text_chunks:
                print(f"\n[{datetime.now().isoformat()}] Assembled message:")
                print("".join(text_chunks))
                    
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"Starting Frontend Format Test at {datetime.now().isoformat()}")
    asyncio.run(test_frontend_format())
    print(f"\nTest completed at {datetime.now().isoformat()}")
