import os
from dotenv import load_dotenv
from telnyx import Telnyx
from telnyx import APIError

load_dotenv()

# 1. Client initialisieren
client = Telnyx(api_key=os.getenv("TELNYX_API_KEY"))

def start_test_call():
    try:
        print("📞 Initiiere Anruf...")
        
        # 2. Den Anruf über die API starten
        response = client.calls.dial(
            # Deine App-ID aus deinem Terminal-Output
            connection_id="3006449224087766220", 
            
            # Die Zielnummer (Deine private Handynummer im E.164 Format, z.B. +491701234567)
            to="+491701234567",
            
            # Deine gekaufte Telnyx-Nummer (Absender)
            from_="+1234567890" 
        )
        
        print("🚀 Anruf wurde erfolgreich gestartet!")
        print(f"Call Control ID: {response.data.call_control_id}")

    except APIError as e:
        print(f"❌ Telnyx API-Fehler (Status {e.status_code}): {e.message}")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    start_test_call()