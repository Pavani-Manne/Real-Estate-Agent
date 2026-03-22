import os
import logging
from simple_salesforce import Salesforce
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()

def test_salesforce():
    username = os.getenv("SF_USERNAME")
    password = os.getenv("SF_PASSWORD")
    token = os.getenv("SF_TOKEN")
    
    print(f"Attempting to connect to Salesforce as {username}...")
    try:
        # Trying standard login
        sf = Salesforce(
            username=username,
            password=password,
            security_token=token
        )
        print("Successfully connected to Salesforce!")
        return sf
    except Exception as e:
        print(f"Standard Login Failed: {e}")
        
    print("\nAttempting with domain='login'...")
    try:
        sf = Salesforce(
            username=username,
            password=password,
            security_token=token,
            domain='login'
        )
        print("Connected via domain='login'!")
        return sf
    except Exception as e:
        print(f"Domain Login Failed: {e}")

if __name__ == "__main__":
    test_salesforce()
