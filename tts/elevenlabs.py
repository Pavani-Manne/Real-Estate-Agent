import httpx
import base64
import os
import asyncio
import json
import logging

from dotenv import load_dotenv

load_dotenv()

ELEVEN_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL") # Default voice

# pcm_8000 matches Piopiy's streaming requirements for efficiency
ELEVEN_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream?model_id=eleven_multilingual_v2&output_format=pcm_8000"

sales_agent_ws = None
stop_audio_event = asyncio.Event()

def stop_audio():
    logging.info("[TTS] Stopping audio stream")
    stop_audio_event.set()

async def get_speech(text):
    """
    Fetches speech from ElevenLabs and streams it to the WebSocket.
    Uses the Multilingual v2 model for English and Arabic support.
    """
    if not text or not text.strip():
        logging.warning("[TTS] Empty text, skipping TTS")
        return
    
    logging.info(f"[TTS] Generating speech for: {text[:100]}")
    stop_audio_event.clear()

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                    "POST",
                    ELEVEN_URL,
                    headers=headers,
                    json=payload,
                    timeout=30.0
            ) as response:

                if response.status_code != 200:
                    err = await response.aread()
                    logging.error(f"[TTS] API error {response.status_code}: {err.decode()}")
                    return

                logging.debug(f"[TTS] ElevenLabs API status: {response.status_code}")
                
                # Buffer for smoother playback
                buffer = b""
                threshold = 4 * 1024 # 4KB chunks
                chunk_count = 0

                async for chunk in response.aiter_bytes():
                    if stop_audio_event.is_set():
                        logging.info("[TTS] Audio interrupted.")
                        break

                    buffer += chunk
                    chunk_count += 1

                    if len(buffer) >= threshold:
                        logging.debug(f"[TTS] Sending audio chunk {chunk_count} ({len(buffer)} bytes)")
                        await send_audio_stream(buffer)
                        buffer = b""

                if buffer and not stop_audio_event.is_set():
                    logging.debug(f"[TTS] Sending final audio chunk ({len(buffer)} bytes)")
                    await send_audio_stream(buffer)
                
                logging.info(f"[TTS] Speech generation complete ({chunk_count} chunks)")

    except Exception as e:
        logging.error(f"[TTS] Exception: {e}", exc_info=True)

async def send_audio_stream(audio_stream):
    """
    Sends the raw PCM audio stream to the Piopiy WebSocket.
    """
    global sales_agent_ws
    if not sales_agent_ws:
        logging.warning("[TTS] WebSocket not available, cannot send audio")
        return

    try:
        b64_audio = base64.b64encode(audio_stream).decode()
        # Align with Piopiy PCM streaming format
        payload = {
            "type": "streamAudio",
            "data": {
                "audioDataType": "raw",
                "sampleRate": 8000,
                "audioData": b64_audio
            }
        }
        logging.debug(f"[TTS] Sending {len(audio_stream)} bytes via WebSocket")
        await sales_agent_ws.send(json.dumps(payload))
    except Exception as e:
        logging.error(f"[TTS] WebSocket send error: {e}", exc_info=True)

def set_wss(ws):
    global sales_agent_ws
    sales_agent_ws = ws