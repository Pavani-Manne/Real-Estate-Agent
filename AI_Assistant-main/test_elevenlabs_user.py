import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_user():
    api_key = os.getenv("ELEVEN_LABS_API_KEY")
    url = "https://api.elevenlabs.io/v1/user"
    
    headers = {
        "xi-api-key": api_key
    }
    
    print(f"Testing ElevenLabs /v1/user with key: {api_key[:10]}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print("SUCCESS: Received 200 OK from ElevenLabs.")
                print(f"User Info: {response.json()}")
            else:
                print(f"FAILED: Status {response.status_code}")
                print(f"Response: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_user())
