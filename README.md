# 🏡 Real Estate AI Voice Agent

An AI-powered voice assistant designed to handle real estate customer inquiries, qualify leads, and provide human-like conversations in **English and Arabic**.

---

## 📌 Key Features

* 🎙 **Real-Time Voice Interaction** – Handle inbound/outbound calls using Piopiy (TeleCMI)
* 🗣 **Multilingual Support** – English & Arabic conversations
* 🤖 **AI-Powered Conversations** – Lead qualification using LLM (Groq / Llama models)
* 🔊 **Natural Voice Responses** – High-quality TTS using ElevenLabs
* 📊 **CRM Integration** – Capture and manage leads (Salesforce-ready)
* 🌙 **24/7 Availability** – Works even after business hours

---

## 🛠️ Tech Stack

| Component      | Tool / Framework         |
| -------------- | ------------------------ |
| Telephony      | Piopiy (TeleCMI)         |
| Backend        | Python (Flask / FastAPI) |
| Streaming      | WebSockets               |
| Speech-to-Text | Deepgram API             |
| AI / LLM       | Groq API (Llama Models)  |
| Text-to-Speech | ElevenLabs API           |
| CRM            | Salesforce API           |
| Tunneling      | ngrok                    |

---

## 📦 Setup Instructions

### 1. Prerequisites

* Python 3.9+
* API Keys:

  * Deepgram
  * Groq
  * ElevenLabs
* Piopiy Account
* ngrok installed

---

### 2. Installation

```bash
git clone https://github.com/Pavani-Manne/Real-Estate-Agent.git
cd AI_Assistant-main
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

### 3. Configuration

Create a `.env` file and add:

```env
GROQ_API_KEY=your_key_here
DEEPGRAM_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
WEBSOCKET_URL=your_ngrok_url
```

---

### 4. Run the Project

```bash
python AI_ASSISTANT/customer_support.py
```

---

## 🧩 Project Structure

```
AI_ASSISTANT/
├── asr/        # Speech-to-text
├── call/       # Call handling
├── llm/        # AI logic
├── tts/        # Voice output
├── crm/        # CRM integration
├── customer_support.py
```

---

## 💡 Use Cases

* AI Voice Assistant for Real Estate
* Lead Qualification Automation
* 24/7 Customer Support
* Voice-based Conversational AI

---

## 👩‍💻 Contributors

* Pavani Manne
* Anjali Bypureddy

---

## 📬 Contact

📧 Email: [pavani.manne@motivitylabs.com](mailto:pavani.manne@motivitylabs.com)
