import httpx
import asyncio

async def test_key(api_key):
    voice_id = "EXAVITQu4vr4xnSDxMaL"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream?model_id=eleven_multilingual_v2&output_format=pcm_8000"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": "Connectivity test success.",
        "model_id": "eleven_multilingual_v2"
    }
    
    print(f"Testing key: {api_key[:10]}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"SUCCESS: Key is valid! Received {len(response.content)} bytes.")
            else:
                print(f"FAILED: Status {response.status_code}")
                print(f"Response: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    key = "sk_755c0f5c138771c19c0a8aee8d4863776b589c7e56fce2e5"
    asyncio.run(test_key(key))
