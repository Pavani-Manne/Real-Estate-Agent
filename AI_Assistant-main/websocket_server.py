import asyncio
import uuid
import logging
import threading
from asr.deepgram import DeepgramClient
from tts.elevenlabs import set_wss, get_speech
from llm.groq import clear_session

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_websocket_logic(ws):
    """
    🌐 websocket_server.py Logic (Real-Time Audio Processing Engine)
    
    1. Client connects (session_id created)
    2. DeepgramClient started for transcription
    3. set_wss(websocket) links WS to TTS
    4. Send Greeting text -> speech
    5. Process incoming audio bytes -> Deepgram
    """
    session_id = str(uuid.uuid4())
    logging.info(f"[WS] Client connected: {session_id}")
    
    # 2. Setup loop and Deepgram
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    asr_client = DeepgramClient(loop)
    asr_client.start()

    # ✅ FIX: Wait until Deepgram is actually connected before streaming audio or sending greeting
    timeout = 5  # seconds
    elapsed = 0
    while not asr_client.is_running and elapsed < timeout:
        import time; time.sleep(0.1); elapsed += 0.1
    
    # 3. Link WebSocket to TTS
    set_wss(ws)
    
    # 4. Greeting is now handled dynamically by the LLM after the user speaks.
    # threading.Thread(target=lambda: loop.run_until_complete(send_greeting()), daemon=True).start()

    # 5. Process incoming audio (Listen loop)
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
            
            if isinstance(message, bytes):
                # Sends to Deepgram
                asr_client.stream_audio(message)
            else:
                logging.debug(f"[WS] Received non-binary message: {message[:50]}...")
              
    except Exception as e:
        logging.error(f"[WS] Error in session {session_id}: {e}")
    finally:
        # 6. Handle disconnect
        logging.info(f"[WS] Client disconnected. Stopping Deepgram client. Session: {session_id}")
        asr_client.stop()
        clear_session(session_id)
        set_wss(None)
        loop.close()
