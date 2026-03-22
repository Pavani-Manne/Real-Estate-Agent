import asyncio
import os
import logging
from dotenv import load_dotenv
from livekit import rtc

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("Diagnostic")

load_dotenv()

URL = "http://65.20.89.42:7880" # From your logs
TOKEN = os.getenv("PI_AGENT_TOKEN") # We assume this is the token you get from TeleCMI
ROOM = "piopiyai_diagnostic_test" # We will use a dummy room or ask you to call

async def main():
    print("--- TeleCMI/LiveKit Audio Diagnostic ---")
    room_name = input("Enter the Room Name from your latest logs: ")
    token = input("Enter the Token from your latest logs (long string): ")
    
    room = rtc.Room()
    
    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        print(f"User joined: {participant.identity}")

    @room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication, participant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            print(f"!!! Audio track subscribed from {participant.identity} !!!")
            asyncio.create_task(process_audio(track))

    async def process_audio(track):
        audio_stream = rtc.AudioStream(track)
        print("Waiting for audio frames...")
        count = 0
        async for event in audio_stream:
            if isinstance(event, rtc.AudioFrameEvent):
                count += 1
                if count % 50 == 0:
                    print(f"Received {count} audio frames!")
    
    print(f"Connecting to {room_name}...")
    try:
        await room.connect(URL, token)
        print("Connected! Waiting for you to speak on the phone...")
        await asyncio.sleep(60) # Wait for 1 minute
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await room.disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
