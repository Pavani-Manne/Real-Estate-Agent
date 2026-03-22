import asyncio
import os
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveTranscriptionEvents

load_dotenv()
api_key = os.getenv("DEEPGRAM_API_KEY")

async def test_combination():
    print("Testing Detect Language TRUE + Smart Format FALSE...")
    try:
        client = DeepgramClient(api_key)
        connection = client.listen.asyncwebsocket.v("1")
        
        options = {
            "detect_language": True,
            "smart_format": False,
            "encoding": "linear16",
            "sample_rate": 16000,
            "channels": 1,
            "model": "nova-2-general"
        }
        
        if await connection.start(options):
            print("SUCCESS!")
            await connection.finish()
        else:
            print("FAILED.")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_combination())
