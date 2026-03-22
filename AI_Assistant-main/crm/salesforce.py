import os
import logging
from simple_salesforce import Salesforce
from dotenv import load_dotenv

load_dotenv()

# Singleton connection cache to avoid repeated authentication
_sf_connection = None
_sf_connection_lock = False

def get_salesforce_connection():
    """Get or create a cached Salesforce connection (singleton pattern)."""
    global _sf_connection, _sf_connection_lock
    
    if _sf_connection is not None:
        return _sf_connection
    
    try:
        _sf_connection = Salesforce(
            username=os.getenv("SF_USERNAME"),
            password=os.getenv("SF_PASSWORD"),
            security_token=os.getenv("SF_TOKEN"),
            domain="login.salesforce.com"  # Using full domain
        )
        logging.info("Salesforce connection established and cached")
        return _sf_connection
    except Exception as e:
        logging.error(f"Failed to establish Salesforce connection: {e}")
        _sf_connection = None
        raise

def create_salesforce_lead(first_name, last_name, phone, email, description):
    """Creates a new lead in Salesforce CRM with robust error handling."""
    try:
        sf = get_salesforce_connection()
        
        # Smarter name splitting
        name_parts = first_name.strip().split(" ", 1)
        f_name = name_parts[0]
        l_name = name_parts[1] if len(name_parts) > 1 else (last_name or "Lead")

        lead_data = {
            'FirstName': f_name,
            'LastName': l_name,
            'Phone': phone,
            'Email': email,
            'Description': description,
            'Company': 'Property Inquiry',
            'LeadSource': 'AI Voice Assistant'
        }
        
        result = sf.Lead.create(lead_data)
        if result.get('success'):
            logging.info(f"Lead created successfully in Salesforce: {result['id']}")
            return result['id']
        else:
            logging.error(f"Failed to create lead in Salesforce: {result.get('errors')}")
            return None
    except Exception as e:
        logging.error(f"Error creating lead in Salesforce: {e}")
        # Reset connection on error so it will be re-established on next attempt
        global _sf_connection
        _sf_connection = None
        return None
