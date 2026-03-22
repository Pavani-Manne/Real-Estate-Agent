from websocket import WebSocketApp
import websocket
import json
import threading
import os
import time
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv

# Use relative imports for consistency with the package structure
from llm.groq import chat_with_assistant
from tts.elevenlabs import stop_audio

load_dotenv()

auth_token = os.getenv("DEEPGRAM_API_KEY")
headers = {
    "Authorization": f"Token {auth_token}"
}

# Optimized for English and Arabic with Nova-2 model
# language=multi allows for automatic language detection
ws_url = "wss://api.deepgram.com/v1/listen?sample_rate=8000&encoding=linear16&model=nova-2&language=multi&smart_format=true&vad_turnoff=500"

class DeepgramClient:
    def __init__(self, loop):
        self.ws: "Optional[WebSocketApp]" = None
        self.keep_alive_thread: "Optional[threading.Thread]" = None
        self.loop = loop
        self.is_running = False

    def on_open(self, ws):
        logging.info("Deepgram WebSocket connection established.")
        self.is_running = True
        thread = threading.Thread(target=self.keep_alive)
        thread.daemon = True
        thread.start()
        self.keep_alive_thread = thread

    def on_message(self, ws, message):
        try:
            response = json.loads(message)
            logging.debug(f"[ASR] Deepgram response type: {response.get('type')}")
            
            if response.get("type") == "Results":
                channel = response.get("channel", {})
                alternatives = channel.get("alternatives", [{}])
                transcript = alternatives[0].get("transcript", "")
                is_final = response.get("is_final", False)
                
                if transcript:
                    logging.info(f"[ASR] Transcript (final={is_final}): {transcript}")
                    
                    # Only process final transcripts
                    if is_final:
                        # Handle interruption: Stop existing TTS audio
                        stop_audio()
                        # Pass to LLM via thread-safe coroutine
                        try:
                            logging.debug(f"[ASR] Scheduling chat_with_assistant for: {transcript}")
                            future = asyncio.run_coroutine_threadsafe(
                                chat_with_assistant(transcript), 
                                self.loop
                            )
                            # Set timeout for the async operation
                            result = future.result(timeout=30)
                            logging.debug(f"[ASR] Chat completed successfully")
                        except asyncio.InvalidStateError:
                            logging.warning("[ASR] Event loop is not running, cannot schedule coroutine")
                        except TimeoutError:
                            logging.error("[ASR] Timeout waiting for chat response")
                        except Exception as e:
                            logging.error(f"[ASR] Error scheduling chat: {e}", exc_info=True)
        except Exception as e:
            logging.error(f"[ASR] Error in Deepgram on_message: {e}", exc_info=True)

    def on_close(self, ws, close_status_code, close_msg):
        logging.warning(f"Deepgram connection closed: {close_status_code} - {close_msg}")
        self.is_running = False
        self.ws = None

    def on_error(self, ws, error):
        logging.error(f"Deepgram WebSocket error: {error}")

    def keep_alive(self):
        """Send keep-alive pings to prevent connection timeout."""
        while self.is_running:
            ws = self.ws
            # Check if connection is still alive
            if not (ws and ws.sock and ws.sock.connected):
                logging.debug("WebSocket connection lost, exiting keep_alive")
                break
            try:
                ws.send(json.dumps({"type": "KeepAlive"}))
                time.sleep(5)
            except Exception as e:
                logging.warning(f"Error sending keep-alive: {e}")
                # Break on error to prevent spinning
                break

    def start(self):
        if self.ws:
            logging.warning("Deepgram client is already starting/running.")
            return

        new_ws: WebSocketApp = WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error,
            header=headers
        )
        self.ws = new_ws
        ws_thread = threading.Thread(target=new_ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

    def stop(self):
        """Gracefully stop the Deepgram client and all threads."""
        self.is_running = False
        ws = self.ws
        if ws is not None:
            try:
                ws.close()
                logging.info("Deepgram WebSocket closed successfully")
            except Exception as e:
                logging.warning(f"Error closing Deepgram WebSocket: {e}")
        
        # Wait for keep_alive thread to finish (with timeout)
        if self.keep_alive_thread and self.keep_alive_thread.is_alive():
            self.keep_alive_thread.join(timeout=2.0)
            if self.keep_alive_thread.is_alive():
                logging.warning("Keep-alive thread did not terminate within timeout")
        
        self.ws = None

    def stream_audio(self, audio_chunk):
        ws = self.ws
        if ws and ws.sock and ws.sock.connected:
            try:
                ws.send(audio_chunk, opcode=websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                logging.error(f"Error streaming audio to Deepgram: {e}")
        else:
            logging.debug("Deepgram WebSocket is not connected.")
