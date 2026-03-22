import asyncio
import json
import logging
import os
import re
import sys

from dotenv import load_dotenv
from loguru import logger

from piopiy.agent import Agent  # type: ignore[import-not-found]
from piopiy.voice_agent import VoiceAgent  # type: ignore[import-not-found]
from piopiy.services.deepgram.stt import DeepgramSTTService  # type: ignore[import-not-found]
from piopiy.services.elevenlabs.tts import ElevenLabsTTSService  # type: ignore[import-not-found]
from piopiy.services.groq.llm import GroqLLMService  # type: ignore[import-not-found]
from piopiy.frames.frames import TranscriptionFrame, UserAudioRawFrame, AudioRawFrame, OutputAudioRawFrame, TextFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame # type: ignore[import-not-found]
from piopiy.transports.services.telecmi import TelecmiParams # type: ignore[import-not-found]
from piopiy.processors.frame_processor import FrameProcessor, FrameDirection # type: ignore[import-not-found]
from piopiy.adapters.schemas.function_schema import FunctionSchema # type: ignore[import-not-found]
from piopiy.voice import RestClient # type: ignore[import-not-found]

# Configure logging (Unified Loguru)
logger.remove()
logger.add(sys.stderr, level="DEBUG", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

# Silence noisy libraries
logging.getLogger("livekit").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("deepgram").setLevel(logging.DEBUG)
logging.getLogger("deepgram.clients.listen.v1.websocket.async_client").setLevel(logging.DEBUG)
logging.getLogger("piopiy").setLevel(logging.DEBUG)

# --- CRITICAL INFRASTRUCTURE PATCHES ---
try:
    from piopiy.processors.frame_processor import FrameProcessor
    # Bypasses the requirement for an explicit StartFrame which some SIP bridges omit
    FrameProcessor._check_started = lambda self, frame: True
    
    # WebSocket patch for Deepgram/Piopiy compatibility on some environments
    from websockets.client import WebSocketClientProtocol
    if not hasattr(WebSocketClientProtocol, 'response'):
        def response_patch(self):
            class MockResponse:
                status = 101
                headers = {}
            return MockResponse()
        WebSocketClientProtocol.response = property(response_patch)

    # Deepgram async client patch for connection tracking
    from deepgram.clients.listen.v1.websocket.async_client import AsyncListenWebSocketClient
    if not hasattr(AsyncListenWebSocketClient, "is_connected"):
        async def is_connected_patch(self):
            return getattr(self, "_socket", None) is not None
        AsyncListenWebSocketClient.is_connected = is_connected_patch
    original_dg_init = AsyncListenWebSocketClient.__init__
    def patched_init(self, *args, **kwargs):
        original_dg_init(self, *args, **kwargs)
        self._socket = None
    AsyncListenWebSocketClient.__init__ = patched_init

    from piopiy.transports.services.telecmi import TelecmiTransportClient
    original_publish_audio = TelecmiTransportClient.publish_audio
    async def logged_publish_audio(self, audio_frame):
        if not hasattr(self, "_publish_count"): self._publish_count = 0
        self._publish_count += 1
        # Log every 20 frames (~400ms of audio) to confirm the transport is ACTIVE
        if self._publish_count % 20 == 1:
            logger.info(f"📤 [TRANSPORT] Publishing audio frame {self._publish_count} (Transport is SENDING)")
        await original_publish_audio(self, audio_frame)
    TelecmiTransportClient.publish_audio = logged_publish_audio
    logger.info("✅ Full infrastructure patches applied (StartFrame + WebSockets + Deepgram + Trace).")
except Exception as e:
    logger.error(f"Infrastructure patch failed: {e}")

# --- HANDLERS (Moved inside create_session for context) ---

HANG_UP_SCHEMA = FunctionSchema(
    name="hang_up_call",
    description="Ends the call when the conversation is finished.",
    properties={},
    required=[]
)

LEAD_SCHEMA = FunctionSchema(
    name="create_salesforce_lead",
    description="Creates a new lead with property inquiry details once all information is collected.",
    properties={
        "name": {"type": "string"},
        "phone": {"type": "string"},
        "intent": {"type": "string", "enum": ["Buy", "Rent", "Invest"]},
        "property_type": {"type": "string", "enum": ["Apartment", "Villa", "Townhouse", "Commercial"]},
        "location": {"type": "string"},
        "budget": {"type": "string"},
        "bedrooms": {"type": "string"},
        "timeline": {"type": "string"},
    },
    required=["name", "phone", "intent", "property_type", "location", "budget"]
)

# --- CONFIGURATION ---
load_dotenv()
AGENT_ID = os.getenv("PI_AGENT_ID")
AGENT_TOKEN = os.getenv("PI_AGENT_TOKEN")
GROQ = os.getenv("GROQ")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

GREETING = "Hello! Thank you for calling. How can I assist you with your property search today?"
SYSTEM_PROMPT = """
ROLE
You are a professional, friendly, voice-based AI Real Estate Sales Assistant.
Your job is to handle calls, understand customer needs, qualify leads, and collect required information smoothly.

LANGUAGE HANDLING (STRICT)
• Detect the language from the user's FIRST message.
• If Arabic → respond ONLY in Arabic.
• If English → respond ONLY in English.
• NEVER mix languages.
• Maintain the same language throughout the conversation.

PERSONALITY & VOICE STYLE
• Speak like a real human agent on a phone call.
• Keep responses VERY SHORT (max 1–2 sentences).
• Ask ONLY ONE question at a time.
• Avoid long explanations.
• Be natural, polite, and efficient.

PRIMARY OBJECTIVE
Collect the following details step-by-step:
1. Intent (Buy / Rent / Invest)
2. Property Type
3. Location
4. Budget
5. Bedrooms / Size
6. Timeline
7. Name
8. Phone Number (confirm clearly)

CONVERSATION FLOW (STRICT ORDER)
Follow this flow naturally (do NOT skip steps unless already answered):

1. Greet the user.
2. Ask intent (buy/rent/invest).
3. Ask property type.
4. Ask location.
5. Ask budget.
6. Ask bedrooms/size.
7. Ask timeline.
8. Ask name.
9. Ask and CONFIRM phone number.

IMPORTANT:
• If user already gave info → do NOT ask again.
• Always move forward step-by-step.

SMART HANDLING
• If vague → ask for clarification.
• If hesitant → reassure politely.
• If user interrupts → continue from last missing step.
• If user gives multiple details → extract and skip ahead.

SUMMARY (MANDATORY)
After collecting ALL required details:

• MUST generate a clear summary (DO NOT SKIP)

Example:
“You are looking for a 3-bedroom villa in Dubai with a budget of 2 million and planning to move within 2 months.”

• Summary MUST include:
  - Property type
  - Location
  - Budget
  - Bedrooms
  - Timeline

QUERY STEP (MANDATORY)
After summary, ALWAYS ask:
“Is there anything else I can help you with?”

• If user asks a question:
  - Answer briefly (1 sentence)
  - Ask again: “Is there anything else I can help you with?”

• If user says:
  - “No”
  - “That’s all”
  - “Nothing”
  - “Thank you”

→ Proceed to closing.

CLOSING (MANDATORY)
Say:
“Thank you for sharing the details. Our team will contact you shortly with suitable options.”

CRITICAL OUTPUT FORMAT (INTERNAL)
After closing, output:

[LEAD_DATA]: {
  "name": "...",
  "phone": "...",
  "intent": "...",
  "property_type": "...",
  "location": "...",
  "budget": "...",
  "bedrooms": "...",
  "timeline": "..."
}

TOOL EXECUTION (STRICT ORDER)
1. CALL create_salesforce_lead
2. CALL hang_up_call

CRITICAL RULES
• NEVER skip summary
• NEVER skip query step
• NEVER skip lead data
• NEVER skip phone confirmation
• NEVER ask multiple questions
• NEVER generate long responses
• ALWAYS keep conversation flowing
• ALWAYS respond immediately (no silence)

FAILSAFE (VERY IMPORTANT)
If unsure what to say:
→ Ask the next required question from the flow

If conversation stalls:
→ Continue from the last missing detail
"""

async def create_session(agent_id, call_id, from_number, to_number, **kwargs):
    logger.info(f"📞 [{call_id}] New Session started from {from_number}")
    
    # Initialize REST client for out-of-band actions like hangup
    rest_client = RestClient(token=AGENT_TOKEN)

    # Define handlers inside to capture call_id and rest_client
    async def hang_up_handler(params):
        logger.info("👋 [AGENT] Requesting hangup. Waiting for final summary to play...")
        # 7-second buffer to allow TTS to finish the closing reassurance
        await asyncio.sleep(7.0) 
        logger.info(f"📞 [{call_id}] Executing REST hangup...")
        try:
            rest_client.voice.hangup(call_id=call_id)
        except Exception as e:
            logger.error(f"REST Hangup failed: {e}")
        return "Call disconnected."

    async def create_lead_handler(params):
        args = params.arguments
        name = args.get("name", "Voice-Lead")
        data = {
            "name": name,
            "phone": args.get("phone"),
            "intent": args.get("intent"),
            "property_type": args.get("property_type"),
            "location": args.get("location"),
            "budget": args.get("budget"),
            "bedrooms": args.get("bedrooms"),
            "timeline": args.get("timeline")
        }
        logger.info(f"💾 [CRM] Captured lead via Tool: {json.dumps(data, indent=2)}")
        return f"Lead for {name} saved successfully."

    # 2-second safety delay for bridge stabilization
    await asyncio.sleep(2.0)

    try:
        class DebugLoggerProcessor(FrameProcessor):
            async def process_frame(self, frame, direction):
                await super().process_frame(frame, direction)
                if isinstance(frame, TranscriptionFrame):
                    logger.info(f"📝 [STT] {frame.user_id} said: '{frame.text}' (Final: {frame.result.is_final if hasattr(frame, 'result') else '?'})")
                elif isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
                    logger.info(f"🤖 [LLM] Response: {frame.text}")
                elif isinstance(frame, UserStartedSpeakingFrame):
                    logger.debug("👤 [VAD] User started speaking")
                elif isinstance(frame, UserStoppedSpeakingFrame):
                    logger.info("👤 [VAD] User stopped speaking")
                elif isinstance(frame, UserAudioRawFrame):
                    if not hasattr(self, "_f_in"): self._f_in = 0
                    self._f_in += 1
                    if self._f_in % 500 == 0:
                        logger.info(f"🔍 [AUDIO-IN] Connection is active...")

        stt = DeepgramSTTService(api_key=DEEPGRAM_API_KEY, model="nova-2-general")
        tts = ElevenLabsTTSService(
            api_key=ELEVEN_LABS_API_KEY, 
            voice_id=ELEVEN_VOICE_ID,
            sample_rate=8000
        )
        llm = GroqLLMService(api_key=GROQ, model="llama-3.3-70b-versatile")

        voice_agent = VoiceAgent(
            instructions=SYSTEM_PROMPT,
            greeting=GREETING
        )
        
        voice_agent.add_tool(LEAD_SCHEMA, create_lead_handler)
        voice_agent.add_tool(HANG_UP_SCHEMA, hang_up_handler)

        telecmi_params = TelecmiParams(
            audio_out_enabled=True,
            audio_in_enabled=True,
            audio_out_sample_rate=8000, 
            audio_in_sample_rate=16000, # Increased for Deepgram accuracy
            audio_out_10ms_chunks=2
        )

        await voice_agent.Action(
            stt=stt, tts=tts, llm=llm,
            allow_interruptions=True, # Critical for interaction
            vad=True, 
            telecmi_params=telecmi_params
        )

        # Inject Trace at the very front
        voice_agent._processors.insert(0, DebugLoggerProcessor())

        logger.info(f"🚀 [{call_id}] VoiceAgent starting...")
        await voice_agent.start()
        
    except Exception as e:
        logger.error(f"❌ [{call_id}] Session Failed: {e}")

async def main():
    if not all([AGENT_ID, AGENT_TOKEN, GROQ, DEEPGRAM_API_KEY, ELEVEN_LABS_API_KEY]):
        logger.error("Missing required environment variables.")
        return

    if os.name == 'nt':
        # Windows does not support add_signal_handler, but the SDK calls it.
        # We patch it with a no-op to prevent NotImplementedError.
        loop = asyncio.get_event_loop()
        setattr(loop, 'add_signal_handler', lambda *args: None)

    agent = Agent(
        agent_id=AGENT_ID,
        agent_token=AGENT_TOKEN,
        create_session=create_session,
        debug=True
    )

    logger.info(f"📡 Connecting to Piopiy (Agent: {AGENT_ID})...")
    await agent.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass