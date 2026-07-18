import os
import requests
from dotenv import load_dotenv

# 1. .env-Datei laden
load_dotenv()

# 2. API-Key auslesen
telnyx_api_key = os.getenv("TELNYX_API_KEY")

if not telnyx_api_key:
    print("❌ Fehler: TELNYX_API_KEY wurde nicht in der .env-Datei gefunden.")
    exit(1)

def test_telnyx_connection():
    # Telnyx API v2 Endpoint für Account-Informationen
    url = "https://api.telnyx.com/v2/account"
    
    # Authentifizierungs-Header vorbereiten
    headers = {
        "Authorization": f"Bearer {telnyx_api_key}",
        "Content-Type": "application/json"
    }
    
    print("📡 Sende Test-Anfrage an Telnyx...")
    
    try:
        # API-Call absetzen
        response = requests.get(url, headers=headers)
        
        # Falls der Statuscode nicht 200er-Bereich ist, wird eine Exception geworfen
        response.raise_for_status()
        
        # Antwort auswerten
        data = response.json()
        account_name = data.get("data", {}).get("organization_name", "Unbekannt")
        email = data.get("data", {}).get("email", "Keine E-Mail hinterlegt")
        
        print("✅ Verbindung erfolgreich!")
        print(f"   Organisation: {account_name}")
        print(f"   Account E-Mail: {email}")
        
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP-Fehler aufgetreten: {http_err}")
        if response.status_code == 401:
            print("👉 Hinweis: Dein API-Key ist ungültig oder nicht korrekt kopiert worden.")
        else:
            print(f"   Antwort vom Server: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Netzwerkfehler: Keine Verbindung zu api.telnyx.com möglich.")
    except Exception as e:
        print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    test_telnyx_connection()