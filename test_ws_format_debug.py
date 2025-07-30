"""
Test WebSocket con logging dettagliato per debug formato messaggi
"""
import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def test_websocket_messages():
    uri = "ws://127.0.0.1:8058/ws"
    session_id = str(uuid.uuid4())
    
    print(f"\n{'='*60}")
    print(f"WebSocket Test - {datetime.now().isoformat()}")
    print(f"{'='*60}")
    print(f"URI: {uri}")
    print(f"Session ID: {session_id}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"\n[OK] Connected successfully")
            
            # Ricevi messaggio di conferma
            confirmation = await websocket.recv()
            conf_data = json.loads(confirmation)
            print(f"\n[RECEIVED] Confirmation:")
            print(f"   Type: {conf_data.get('type')}")
            print(f"   Data: {json.dumps(conf_data.get('data', {}), indent=6)}")
            
            # Invia messaggio semplice
            chat_message = {
                "type": "chat",
                "session_id": session_id,
                "user_id": "test_user",
                "data": {
                    "message": "Dimmi solo: test",
                    "search_type": "hybrid"
                }
            }
            
            print(f"\n[SENDING] Chat message: '{chat_message['data']['message']}'")
            await websocket.send(json.dumps(chat_message))
            
            # Ricevi risposte
            print(f"\n[RECEIVING] Responses:")
            print(f"{'='*60}")
            
            response_count = 0
            text_chunks = []
            timeout = 15  # 15 secondi timeout
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        print(f"\n[TIMEOUT] After {timeout}s")
                        break
                    
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    response_count += 1
                    
                    try:
                        data = json.loads(response)
                        
                        print(f"\n[RESPONSE #{response_count}]:")
                        print(f"   Type: '{data.get('type')}'")
                        print(f"   Session ID: {data.get('session_id')}")
                        print(f"   Request ID: {data.get('request_id')}")
                        
                        if data.get('data'):
                            print(f"   Data structure: {type(data.get('data'))}")
                            print(f"   Data keys: {list(data.get('data', {}).keys()) if isinstance(data.get('data'), dict) else 'N/A'}")
                            print(f"   Data content: {json.dumps(data.get('data'), indent=6)}")
                        
                        # Collect text chunks
                        if data.get('type') == 'text' and isinstance(data.get('data'), dict):
                            content = data.get('data', {}).get('content', '')
                            if content:
                                text_chunks.append(content)
                                print(f"   [COLLECTED] Text chunk: '{content}'")
                            
                        if data.get("type") == "completed":
                            print(f"\n[COMPLETED] Stream finished!")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"\n[ERROR] JSON decode: {e}")
                        print(f"   Raw response: {response}")
                        
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
                    continue
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"\n[ERROR] Connection closed: {e}")
                    break
                    
            # Show assembled message
            print(f"\n{'='*60}")
            if text_chunks:
                assembled = "".join(text_chunks)
                print(f"[ASSEMBLED] Message ({len(text_chunks)} chunks):")
                print(f"   '{assembled}'")
            else:
                print(f"[WARNING] No text chunks received!")
                
            print(f"\n[SUMMARY]:")
            print(f"   Total responses: {response_count}")
            print(f"   Text chunks: {len(text_chunks)}")
            print(f"   Connection duration: {elapsed:.2f}s")
                    
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting WebSocket Format Test...")
    asyncio.run(test_websocket_messages())
    print("\n[DONE] Test completed")
