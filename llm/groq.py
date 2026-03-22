import os
import json
import re
import logging
import asyncio
from groq import AsyncGroq
from tts.elevenlabs import get_speech
from crm.salesforce import create_salesforce_lead
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ")
client = AsyncGroq(api_key=api_key)

# Thread pool for blocking I/O operations (Salesforce API calls)
executor = ThreadPoolExecutor(max_workers=4)

SYSTEM_PROMPT = """
ROLE
You are a professional bilingual AI Real Estate Sales Assistant.
Your responsibility is to handle incoming property inquiries, qualify potential customers (buyers, renters, or investors), and collect key lead information for the sales team.
 
LANGUAGE HANDLING
• Automatically detect the customer's language (English or Arabic).
• Continue the conversation in the same language.
• Do not switch languages unless the customer does.
• Ensure proper Arabic honorifics and polite forms when speaking Arabic.
 
PERSONALITY & TONE
• Be polite, friendly, and professional.
• Speak naturally like a human real estate sales representative.
• Keep responses concise and conversational (max 2 sentences per turn).
• Avoid long explanations.
• Ask only one question at a time.
 
PRIMARY OBJECTIVE
Your main goal is to qualify the lead and collect the following information:
1. Customer Name
2. Phone Number
3. Intent (Buy / Rent / Invest)
4. Property Type (Apartment / Villa / Townhouse / Commercial)
5. Preferred Location
6. Budget Range
7. Bedrooms or Property Size (if relevant)
8. Purchase Timeline (Immediately / 1–3 months / 6+ months)
 
CONVERSATION FLOW
Step 1 — Greeting: Start with a warm greeting (e.g., "Hello! Thank you for calling. How can I assist you with your property search today?" or in Arabic: "أهلاً بك! شكراً لاتصالك. كيف يمكنني مساعدتك في بحثك عن عقار اليوم؟").
Step 2 — Identify Intent: Ask if they are looking to Buy, Rent, or Invest.
Step 3 — Property Type: Ask which type of property they are interested in.
Step 4 — Location: Ask for their preferred area or city. (Tease: "Great area! I have several premium units there.")
Step 5 — Budget: Ask for their approximate budget range.
Step 6 — Property Details: Ask for the number of bedrooms or size.
Step 7 — Timeline: Ask when they plan to move or purchase.
Step 8 — Contact Details: Collect Name and Phone Number.
 
HANDLING QUESTIONS
If the customer asks about specific properties, provide brief info then guide back to requirements: "I'd be happy to check that for you. May I first ask which location and budget you are considering?"
 
LEAD COMPLETION CRITERIA
Once the following are collected: Name, Phone Number, Property Type, Location, and Budget.
 
CRITICAL OUTPUT FORMAT (INTERNAL)
Upon completion, append this tag at the very end:
[LEAD_DATA]: {
  "name": "Customer Name",
  "phone": "Phone Number",
  "intent": "Buy/Rent/Invest",
  "property_type": "Apartment/Villa/Townhouse/Commercial",
  "location": "Preferred Location",
  "budget": "Budget Range",
  "bedrooms": "Bedrooms/Size",
  "timeline": "Timeline"
}
IMPORTANT: Only output this block after lead criteria are met. Ask ONE question at a time. Do not mention this block to the user.
"""

# Dictionary to store chat history per session/connection
session_histories = {}

async def chat_with_assistant(text, session_id="default"):
    """
    Asynchronous interaction with Groq LLM.
    Handles streaming response and triggers TTS.
    """
    if not text or not text.strip():
        logging.warning(f"[LLM] Empty transcript received")
        return
    
    logging.info(f"[LLM] Processing user input: {text[:100]}")
    
    if session_id not in session_histories:
        session_histories[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    history = session_histories[session_id]
    history.append({"role": "user", "content": text})

    try:
        # Add timeout to prevent hanging on Groq API
        logging.debug(f"[LLM] Sending to Groq API...")
        response = await asyncio.wait_for(
            client.chat.completions.create(
                messages=history,
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=500
            ),
            timeout=15.0  # 15 second timeout
        )

        assistant_response = response.choices[0].message.content
        if not assistant_response:
            logging.warning(f"[LLM] Empty response from Groq")
            return
        
        logging.info(f"[LLM] Groq response received: {assistant_response[:100]}")

        # Clean response for speech (remove the LEAD_DATA tag if present)
        speech_text = re.sub(r'\[LEAD_DATA\].*', '', assistant_response).strip()
        
        if speech_text:
            logging.info(f"[LLM] Sending to TTS: {speech_text[:100]}")
            await get_speech(speech_text)
        else:
            logging.warning("[LLM] No speech text after removing LEAD_DATA tag")

        history.append({"role": "assistant", "content": assistant_response})

        # Process lead data if present
        if "[LEAD_DATA]:" in assistant_response:
            logging.info(f"[LLM] Lead data detected, processing...")
            await handle_lead_data(assistant_response)

    except asyncio.TimeoutError:
        logging.error(f"[LLM] Timeout waiting for Groq response")
    except Exception as e:
        logging.error(f"[LLM] Error in chat_with_assistant: {e}", exc_info=True)

async def handle_lead_data(response_text):
    """Parses lead data and sends it to Salesforce asynchronously."""
    try:
        match = re.search(r'\[LEAD_DATA\]:\s*(\{.*\})', response_text)
        if match:
            data_json = match.group(1)
            lead_data = json.loads(data_json)
            
            logging.info(f"Lead identified: {lead_data}. Syncing to Salesforce...")
            
            description = (
                f"Automated AI Property Inquiry\n"
                f"Intent: {lead_data.get('intent')}\n"
                f"Property: {lead_data.get('property_type')}\n"
                f"Location: {lead_data.get('location')}\n"
                f"Budget: {lead_data.get('budget')}"
            )
            
            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                executor,
                create_salesforce_lead,
                lead_data.get("name", "Unknown"),
                "Lead",
                lead_data.get("phone", "Unknown"),
                "captured@aiva.ai",
                description
            )
    except asyncio.TimeoutError:
        logging.error("Timeout processing lead data")
    except Exception as e:
        logging.error(f"Error processing lead data: {e}")

def clear_session(session_id):
    """Cleanup session to prevent memory leaks."""
    session_histories.pop(session_id, None)
    logging.debug(f"Session {session_id} cleared from memory")
