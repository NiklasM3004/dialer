import sys
import json
import time
import requests

# --- KONFIGURATION ---
HUBSPOT_ACCESS_TOKEN = "DEIN_HUBSPOT_TOKEN"
TELNYX_API_KEY = "DEIN_TELNYX_KEY"
TELNYX_CONNECTION_ID = "DEINE_TELNYX_CONNECTION_ID"
FROM_NUMBER = "+1234567890"

HUBSPOT_PROPERTY_NAME = "anzahl_kontaktversuche" 
JSON_FILE = "contacts.json"

def fetch_hubspot_contacts():
    """Funktion 1: Holt Kontakte aus HubSpot und speichert sie als JSON"""
    print("[HubSpot] Starte Suche nach Kontakten...")
    url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "filterGroups": [{"filters": [{"propertyName": HUBSPOT_PROPERTY_NAME, "operator": "EQ", "value": "0"}]}],
        "properties": ["firstname", "lastname", "phone", HUBSPOT_PROPERTY_NAME],
        "limit": 100
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        results = response.json().get("results", [])
        valid_contacts = [c for c in results if c.get("properties", {}).get("phone")]
        
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(valid_contacts, f, indent=4, ensure_ascii=False)
        print(f"[HubSpot] Erfolgreich {len(valid_contacts)} Kontakte in '{JSON_FILE}' gespeichert.")
    except Exception as e:
        print(f"[Fehler] HubSpot API fehlgeschlagen: {e}")

def trigger_telnyx_call(to_number):
    """Funktion 2: Startet einen einzelnen Anruf (gibt Call Control ID zurück)"""
    url = "https://api.telnyx.com/v2/calls"
    headers = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
    payload = {"connection_id": TELNYX_CONNECTION_ID, "to": to_number, "from": FROM_NUMBER}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        call_id = response.json().get("data", {}).get("call_control_id")
        print(f"[Telnyx] Anruf initiiert für {to_number}. Call-ID: {call_id}")
        return call_id
    except Exception as e:
        print(f"[Fehler] Telnyx Anruf fehlgeschlagen für {to_number}: {e}")
        return None

def check_call_status(call_control_id):
    """Funktion 3: Prüft den aktuellen Status einer Call ID einmalig"""
    url = f"https://api.telnyx.com/v2/calls/{call_control_id}"
    headers = {"Authorization": f"Bearer {TELNYX_API_KEY}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return "hung_up"
        response.raise_for_status()
        status = response.json().get("data", {}).get("call_status")
        return status
    except Exception:
        return "hung_up"

def monitor_call_live(call_id):
    """Funktion 4: Überwacht eine Call ID live im Terminal, bis der Anruf endet"""
    print(f"[Monitor] Starte Live-Überwachung für ID: {call_id}")
    while True:
        status = check_call_status(call_id)
        print(f"[Live-Status] Status: {status}        ", end="\r")
        if status in ["completed", "pushed_to_voicemail", "no_answer", "timeout", "hung_up"]:
            print(f"\n[Monitor] Anruf beendet mit Status: {status}")
            break
        time.sleep(2)

def call_first_contact():
    """Funktion 5: Ruft nur den allerersten Kontakt aus der JSON an"""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            contacts = json.load(f)
        if not contacts:
            print("[Dialer] Die JSON-Datei ist leer.")
            return
        first = contacts[0].get("properties", {})
        print(f"[Dialer] Erster Kontakt: {first.get('firstname')} {first.get('lastname')} ({first.get('phone')})")
        trigger_telnyx_call(first.get("phone"))
    except FileNotFoundError:
        print(f"[Fehler] '{JSON_FILE}' nicht gefunden. Bitte zuerst 'fetch' ausführen.")

def start_dialing_loop():
    """Funktion 6: Der vollständige Loop (Anrufen -> Überwachen -> Nächster)"""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            contacts = json.load(f)
    except FileNotFoundError:
        print(f"[Fehler] Keine '{JSON_FILE}' vorhanden.")
        return

    print(f"[Loop] Starte Auto-Dialer für {len(contacts)} Kontakte...")
    for idx, contact in enumerate(contacts):
        props = contact.get("properties", {})
        phone = props.get("phone")
        print(f"\n--- [{idx+1}/{len(contacts)}] Wähle: {phone} ---")
        
        call_id = trigger_telnyx_call(phone)
        if call_id:
            monitor_call_live(call_id) # Nutzt die Live-Überwachung
        time.sleep(2)
    print("\n[Loop] Fertig. Alle Kontakte wurden angerufen.")

# --- TERMINAL CLI INTERFACE ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verfügbare Terminal-Befehle:")
        print("  python dialer.py fetch               <- Kontakte von HubSpot in JSON laden")
        print("  python dialer.py call_first          <- Nur den ersten Kontakt aus JSON anrufen")
        print("  python dialer.py call <nummer>       <- Eine beliebige Nummer direkt anrufen")
        print("  python dialer.py status <call_id>    <- Status einer bestimmten Call-ID abfragen")
        print("  python dialer.py monitor <call_id>   <- Bestimmte Call-ID live im Terminal überwachen")
        print("  python dialer.py loop                <- Den kompletten automatischen Ablauf starten")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    
    if cmd == "fetch":
        fetch_hubspot_contacts()
    elif cmd == "call_first":
        call_first_contact()
    elif cmd == "call":
        if len(sys.argv) < 3:
            print("Fehler: Bitte eine Telefonnummer angeben (z.B. python dialer.py call +4912345)")
        else:
            trigger_telnyx_call(sys.argv[2])
    elif cmd == "status":
        if len(sys.argv) < 3:
            print("Fehler: Bitte eine Call Control ID angeben.")
        else:
            print(f"Aktueller Status: {check_call_status(sys.argv[2])}")
    elif cmd == "monitor":
        if len(sys.argv) < 3:
            print("Fehler: Bitte eine Call Control ID angeben.")
        else:
            monitor_call_live(sys.argv[2])
    elif cmd == "loop":
        start_dialing_loop()
    else:
        print(f"Unbekannter Befehl: {cmd}")
