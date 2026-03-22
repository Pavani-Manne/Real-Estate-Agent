import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_deepgram():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    url = "https://api.deepgram.com/v1/projects"
    headers = {"Authorization": f"Token {api_key}"}
    print(f"Testing Deepgram with key: {api_key[:10]}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            print(f"Deepgram Status: {response.status_code}")
    except Exception as e:
        print(f"Deepgram Exception: {e}")

async def test_groq():
    api_key = os.getenv("GROQ")
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    print(f"Testing Groq with key: {api_key[:10]}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            print(f"Groq Status: {response.status_code}")
    except Exception as e:
        print(f"Groq Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_deepgram())
    asyncio.run(test_groq())
