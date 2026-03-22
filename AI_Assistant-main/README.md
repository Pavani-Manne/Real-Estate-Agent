## 📞 AIVA – AI Voice Assistant for Real-Estate
AIVA is a **real-time AI-driven voice solution** designed for property inquiries and lead qualification. It handles calls during after-hours, supporting both English and Arabic with a human-like voice interaction.

---

## 📌 Key Features
- 🎙 **Real-Time Voice Interaction** – Handle calls via Piopiy (TeleCMI) with premium WebSocket streaming.
- 🗣 **Multilingual ASR** – Seamlessly switch between English and Arabic using **Deepgram Nova-2**.
- 🤖 **Contex-Aware AI** – Qualify leads using **Groq (Llama 3.3 70B)** with a specialized property inquiry prompt.
- 🔊 **Premium TTS** – High-quality, natural voice responses via **ElevenLabs Multilingual V2**.
- 📊 **CRM Integration** – Real-time lead capture and qualification in **Salesforce**.
- 🌙 **After-Hours Support** – Operates 24/7 to ensure no customer call is missed.

---

## 🛠️ Tech Stack
| Component             | Tool / Framework         |
|-----------------------|--------------------------|
| **Telephony**         | Piopiy (TeleCMI)         |
| **Streaming**         | WebSocket, Flask-Sock    |
| **Speech-to-Text**    | Deepgram API             |
| **AI Engine**         | Groq LLM API             |
| **Text-to-Speech**    | ElevenLabs API           |
| **CRM**               | Salesforce API           |
| **Tunneling**         | ngrok                    |

---

## 📦 Setup Instructions

### **1. Prerequisites**
- Python 3.9+
- Piopiy Account & Registered Number
- Deepgram API Key
- Groq API Key
- ElevenLabs API Key
- Salesforce Developer Account/Credentials
- ngrok installed on your machine

### **2. Installation**
```bash
git clone https://github.com/YeshwanthMotivity/AI_Assistant.git
cd AI_Assistant-main
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

### **3. Configuration**
Update the [.env](file:///.env) file with your API keys and the ngrok URL.

### **4. Running the Assistant**
1. **Start ngrok**:
   ```bash
   ngrok http 5000
   ```
2. **Update `.env`**: Copy the `Forwarding` URL (e.g., `https://xxxx.ngrok-free.app`) and set `WEBSOCKET_URL=wss://xxxx.ngrok-free.app/ws`.
3. **Configure Piopiy**: Set your Piopiy inbound webhook to `https://xxxx.ngrok-free.app/python/inbound`.
4. **Run the Server**:
   ```bash
   python AI_ASSISTANT/customer_support.py
   ```

---

## 🧩 Project Structure
```bash
.
├── AI_ASSISTANT/
│   ├── asr/                 # Deepgram ASR Integration
│   ├── call/                # Piopiy Telephony Logic
│   ├── llm/                 # Groq LLM & Prompt Engineering
│   ├── tts/                 # ElevenLabs TTS Integration
│   ├── crm/                 # Salesforce Lead Integration
│   ├── customer_support.py  # Main Flask Server & WebSocket Hub
│   ├── requirements.txt     # Dependency list
│   └── .env                 # API keys and Configuration
```

---


## 💡 Use Cases  ##

1. **AI-driven IVR Replacement:** Eliminates the need for "Press 1, Press 2" phone menus.
2. **24/7 Automated Customer Support:** Provides continuous support without human intervention.
3. **Scalable Call Center Solution:** Suitable for handling a high volume of calls and can be extended to multi-channel support.
4. **Voice-based Chatbot:** Serves as a foundation for conversational AI experiences in an enterprise setting.
    
---

## 📬  About the Team
• Mentor / Manager: Mr. Venkata Ramana Sudhakar Polavarapu

• Team Members: Yeshwanth Goud Mudimala, Uma Venkata Karthik Vallabhaneni, Anjali Bypureddy

---
## 📬 Contact
For questions or collaboration, you can reach out at:

**Email 📧** : yeshwanth.mudimala@motivitylabs.com
