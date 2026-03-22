import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ELEVEN_LABS_API_KEY")
if api_key:
    print(f"Key: {api_key}")
    print(f"Hex: {' '.join(hex(ord(c)) for c in api_key)}")
    print(f"Length: {len(api_key)}")
else:
    print("Error: Key not found in .env")
