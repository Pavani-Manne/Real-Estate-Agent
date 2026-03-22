import piopiy
import piopiy.voice_agent
import inspect
import os

print(f"piopiy path: {os.path.abspath(piopiy.__file__)}")
print(f"voice_agent path: {os.path.abspath(piopiy.voice_agent.__file__)}")

try:
    sig = inspect.signature(piopiy.voice_agent.VoiceAgent.Action)
    print(f"VoiceAgent.Action signature: {sig}")
except Exception as e:
    print(f"Error getting signature: {e}")

try:
    sig = inspect.signature(piopiy.voice_agent.VoiceAgent.__init__)
    print(f"VoiceAgent.__init__ signature: {sig}")
except Exception as e:
    print(f"Error getting __init__ signature: {e}")
