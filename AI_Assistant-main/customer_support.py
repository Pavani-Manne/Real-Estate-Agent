from flask import Flask, request, jsonify, Response
from flask_sock import Sock
from dotenv import load_dotenv
import os
import json
import logging


# Import logic from websocket_server.py
from websocket_server import handle_websocket_logic

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
sock = Sock(app)

@app.after_request
def add_ngrok_header(response):
    """Bypasses the ngrok browser warning for Piopiy HTTP requests."""
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

@app.route("/python/inbound", methods=["GET", "POST"])
def inbound_call():
    """
    📞 customer_support.py (Call Entry Point)
    
    1. Loads environment (auto-detects ngrok URL if not set)
    2. action.stream(ws_url) initializes Piopiy call control
    3. Returns PCMO to Piopiy
    """
    logging.info(f"[HTTP] Inbound call received: {request.method} {request.path}")
    
    # Automatic ngrok detection (Ensures wss:// and correct path)
    ws_url = os.getenv("ws_url") or os.getenv("WEBSOCKET_URL")
    if not ws_url:
        protocol = "wss" if request.headers.get('X-Forwarded-Proto') == 'https' else "ws"
        ws_url = f"{protocol}://{request.host}/ws"
    
    if not ws_url.endswith("/ws"):
        ws_url = ws_url.rstrip("/") + "/ws"

    try:
        pcmo = {
            "nextAction": {
                "stream": {
                    "websocketUrl": ws_url,
                    "options": {
                        "listenMode": "caller"
                    }
                }
            }
        }
        logging.info(f"[HTTP] Returning PCMO pointing to: {ws_url}")
        return Response(json.dumps(pcmo), mimetype='application/json')
    except Exception as e:
        logging.error(f"[HTTP] Error generating PCMO: {e}")
        return jsonify({"error": "Internal server error"}), 500

@sock.route('/ws')
def ws_handler(ws):
    """Integrated WebSocket endpoint on port 5000"""
    handle_websocket_logic(ws)

@app.route("/health")
def health():
    return jsonify({"status": "active"}), 200

if __name__ == "__main__":
    # Using gevent for robust WebSocket + HTTP support on port 5001
    port = 5001
    try:
        from gevent import pywsgi
        from geventwebsocket.handler import WebSocketHandler
        logging.info(f"🚀 Starting Consolidated AIVA Agent (gevent) on http://0.0.0.0:{port}")
        server = pywsgi.WSGIServer(('0.0.0.0', port), app, handler_class=WebSocketHandler)
        server.serve_forever()
    except ImportError:
        logging.warning("gevent not found. Falling back to default Flask server.")
        app.run(host="0.0.0.0", port=port)
