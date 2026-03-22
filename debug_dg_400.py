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

async def test_options(options_dict):
    print(f"Testing with options: {options_dict}")
    try:
        client = DeepgramClient(api_key)
        connection = client.listen.asyncwebsocket.v("1")
        
        async def on_error(self, error, **kwargs):
            print(f"Error received: {error}")
            
        connection.on(LiveTranscriptionEvents.Error, on_error)
        
        if await connection.start(options_dict):
            print("Successfully connected!")
            await connection.finish()
            return True
        else:
            print("Failed to connect.")
            return False
    except Exception as e:
        print(f"Caught exception: {e}")
        return False

async def main():
    # Test 1: Minimal with nova-2
    await test_options({
        "model": "nova-2-general",
        "encoding": "linear16",
        "sample_rate": 16000,
        "channels": 1
    })
    
    # Test 2: With detect_language
    await test_options({
        "model": "nova-2-general",
        "encoding": "linear16",
        "sample_rate": 16000,
        "channels": 1,
        "detect_language": True
    })

    # Test 3: The exact options from the logs
    await test_options({
        "channels": 1,
        "encoding": "linear16",
        "interim_results": True,
        "model": "nova-2-general",
        "punctuate": True,
        "profanity_filter": True,
        "smart_format": True,
        "vad_events": False,
        "detect_language": True,
        "sample_rate": 16000
    })

if __name__ == "__main__":
    asyncio.run(main())
