import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_elevenlabs():
    api_key = os.getenv("ELEVEN_LABS_API_KEY")
    voice_id = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream?model_id=eleven_multilingual_v2&output_format=pcm_8000"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": "Hello, this is a connectivity test.",
        "model_id": "eleven_multilingual_v2"
    }
    
    print(f"Testing ElevenLabs for voice: {voice_id}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                print("SUCCESS: Received 200 OK from ElevenLabs. Bytes received:", len(response.content))
            else:
                print(f"FAILED: Status {response.status_code}")
                print(f"Response: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_elevenlabs())
