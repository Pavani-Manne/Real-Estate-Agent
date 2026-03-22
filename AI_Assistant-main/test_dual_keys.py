import httpx
import asyncio

async def test_key(api_key, label):
    voice_id = "EXAVITQu4vr4xnSDxMaL"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream?model_id=eleven_multilingual_v2&output_format=pcm_8000"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": "Connectivity test.",
        "model_id": "eleven_multilingual_v2"
    }
    
    print(f"Testing key {label}: {api_key[:10]}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"SUCCESS: Key {label} is valid! Received {len(response.content)} bytes.")
            else:
                print(f"FAILED: Key {label} returned {response.status_code}: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

async def main():
    keys = {
        "64-char": "a2ee5399137ac64103cecd3e2308b171d63c951a1ea19840446ffed1bd6ee178",
        "sk-key": "sk_6debe71399f67074b57b565fa0c0a6287c50ecd9abf07a20"
    }
    for label, key in keys.items():
        await test_key(key, label)

if __name__ == "__main__":
    asyncio.run(main())
