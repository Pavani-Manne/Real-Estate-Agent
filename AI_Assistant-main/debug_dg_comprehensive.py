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

async def test_options(label, options_dict):
    print(f"--- TEST: {label} ---")
    print(f"Options: {options_dict}")
    try:
        # Test with default client options first
        client = DeepgramClient(api_key)
        connection = client.listen.asyncwebsocket.v("1")
        
        # Capture error event
        error_queue = asyncio.Queue()
        async def on_error(self, error, **kwargs):
            await error_queue.put(str(error))
            
        connection.on(LiveTranscriptionEvents.Error, on_error)
        
        try:
            if await connection.start(options_dict):
                print("SUCCESS: Connected!")
                await connection.finish()
                return True
            else:
                print("FAILED: start() returned False")
        except Exception as e:
            print(f"EXCEPTION during start(): {e}")
            
        # Check if an error event was received
        if not error_queue.empty():
            print(f"ERROR EVENT received: {await error_queue.get()}")
            
        return False
    except Exception as e:
        print(f"SETUP EXCEPTION: {e}")
        return False

async def main():
    # 1. Nova-2 with detect_language
    await test_options("Nova-2 + Detect Language", {
        "model": "nova-2-general",
        "encoding": "linear16",
        "sample_rate": 16000,
        "channels": 1,
        "detect_language": True
    })
    
    # 2. Nova-2 without detect_language (needs language)
    await test_options("Nova-2 + Language EN", {
        "model": "nova-2-general",
        "encoding": "linear16",
        "sample_rate": 16000,
        "channels": 1,
        "language": "en"
    })

    # 3. Enhanced with detect_language
    await test_options("Enhanced + Detect Language", {
        "model": "enhanced",
        "encoding": "linear16",
        "sample_rate": 16000,
        "channels": 1,
        "detect_language": True
    })

    # 4. Final attempt with all original options
    await test_options("All Original (nova-2)", {
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
