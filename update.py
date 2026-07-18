import os
import sys
from dotenv import load_dotenv
from telnyx import Telnyx
# Wir importieren hier die allgemeine Telnyx API-Fehlerklasse
from telnyx import APIError 

# 1. .env-Datei laden
load_dotenv()

# 2. Umgebungsvariablen auslesen
api_key = os.getenv("TELNYX_API_KEY")
app_id = os.getenv("TELNYX_APP_ID")

if not api_key or not app_id:
    print("❌ Fehler: TELNYX_API_KEY oder TELNYX_APP_ID fehlt in der .env-Datei.")
    sys.exit(1)

# 3. Telnyx-Client initialisieren
client = Telnyx(api_key=api_key)

def update_telnyx_webhook(new_url: str):
    print(f"🔄 Versuche, die Webhook-URL für App '{app_id}' zu aktualisieren...")
    print(f"🔗 Neue URL: {new_url}")
    
    try:
        # 4. API-Aufruf zur Aktualisierung der Call Control Application
        response = client.call_control_applications.modify(
            id=app_id,
            webhook_event_url=new_url
        )
        
        # 5. Erfolgskontrolle
        updated_url = response.data.webhook_event_url
        app_name = response.data.application_name
        
        print("\n✅ Webhook erfolgreich aktualisiert!")
        print(f"   App-Name:   {app_name}")
        print(f"   Gespeicherte URL: {updated_url}")

    except APIError as e:
        # Fängt alle Telnyx-spezifischen API-Fehler (z.B. 401, 404) sauber ab
        print(f"❌ Telnyx API-Fehler aufgetreten (Status {e.status_code}):")
        print(f"   Details: {e.message}")
    except Exception as e:
        print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    # Ersetze das hier mit deiner echten ngrok-URL aus deinem Terminal
    NEUE_WEBHOOK_URL = "https://7c05-2003-e7-b74b-3d00-8c37-997f-7db2-babc.ngrok-free.app/webhook"
    
    update_telnyx_webhook(NEUE_WEBHOOK_URL)