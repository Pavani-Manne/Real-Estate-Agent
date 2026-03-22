import asyncio
import os
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

load_dotenv()
api_key = os.getenv("DEEPGRAM_API_KEY")

async def test_deepgram():
    print(f"Testing Deepgram with key: {api_key[:10]}...")
    try:
        deepgram = DeepgramClient(api_key)
        dg_connection = deepgram.listen.live.v("1")
        
        def on_open(self, open, **kwargs):
            print("Deepgram Connection Open")
        
        def on_error(self, error, **kwargs):
            print(f"Deepgram Error: {error}")

        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        options = LiveOptions(model="nova-2", language="en-US", encoding="linear16", sample_rate=8000)
        dg_connection.start(options)
        await asyncio.sleep(2)
        dg_connection.finish()
        print("Deepgram Test Finished")
    except Exception as e:
        print(f"Deepgram Test FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_deepgram())
