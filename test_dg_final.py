import asyncio
import os
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    LiveOptions,
    LiveTranscriptionEvents,
    DeepgramClientOptions
)

load_dotenv()
api_key = os.getenv("DEEPGRAM_API_KEY")

async def test_with_live_options_object():
    print("--- TEST: Nova-2 + Detect Language (USING LiveOptions OBJECT) ---")
    try:
        client = DeepgramClient(api_key)
        connection = client.listen.asyncwebsocket.v("1")
        
        # We use the class instead of a dict
        options = LiveOptions(
            model="nova-2",
            encoding="linear16",
            sample_rate=16000,
            channels=1,
            detect_language=True
        )
        
        if await connection.start(options):
            print("SUCCESS: Connected with LiveOptions object!")
            await connection.finish()
            return True
        else:
            print("FAILED: start() returned False even with LiveOptions object.")
            return False
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_with_live_options_object())
