import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_voices():
    api_key = os.getenv("ELEVEN_LABS_API_KEY")
    url = "https://api.elevenlabs.io/v1/voices"
    
    headers = {
        "xi-api-key": api_key
    }
    
    print(f"Testing ElevenLabs voices list with key: {api_key[:10]}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print("SUCCESS: Received 200 OK from ElevenLabs.")
                voices = response.json().get('voices', [])
                print(f"Found {len(voices)} voices.")
            else:
                print(f"FAILED: Status {response.status_code}")
                print(f"Response: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_voices())
