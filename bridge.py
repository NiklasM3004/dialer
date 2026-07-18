import os
import json
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telnyx import Telnyx
from telnyx import APIError

# 1. Umgebung laden & Telnyx initialisieren
load_dotenv()
client = Telnyx(api_key=os.getenv("TELNYX_API_KEY"))

# === KONFIGURATION ===
APP_ID = os.getenv("TELNYX_APP_ID") or "3006449224087766220"
JSON_FILE = "contacts.json"

# HIER DEINE PRIVATE NUMMER EINTRAGEN (Wo dein Headset aktiv ist)
AGENT_NUMBER = "+491701234567" 

# Da du keine Telnyx-Nummer kaufen konntest, nutzen wir eine generische Absenderkennung.
# Hinweis: Manche Netze blockieren anonyme Calls, idealerweise nutzt du hier eine verifizierte ID.
FROM_NUMBER = "+18885551212" 
# =====================

app = Flask(__name__)

# Globale Variablen zur Steuerung
numbers_to_call = []
current_index = 0
agent_call_id = None
customer_call_id = None

def load_numbers():
    """Lädt die Kunden-Nummern aus der JSON."""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("contacts", [])
    except Exception as e:
        print(f"❌ Fehler beim Laden der JSON: {e}")
        return []

def call_the_agent():
    """Schritt 1: Ruft zuerst DICH (den Agenten) auf deinem Telefon an."""
    global agent_call_id
    print(f"\n📞 [Dialer startet] Rufe zuerst dein Telefon/Headset an ({AGENT_NUMBER})...")
    
    try:
        response = client.calls.dial(
            connection_id=APP_ID,
            to=AGENT_NUMBER,
            from_=FROM_NUMBER
        )
        agent_call_id = response.data.call_control_id
        print(f"⏳ Bitte geh an dein Telefon! (Call ID: {agent_call_id})")
    except APIError as e:
        print(f"❌ Fehler beim Anrufen deines Telefons: {e.message}")

def call_next_customer():
    """Schritt 2: Ruft den aktuellen Kunden aus der Liste an."""
    global current_index, customer_call_id, numbers_to_call
    
    if current_index >= len(numbers_to_call):
        print("\n🎉 Alle Kontakte aus der JSON wurden erfolgreich angerufen!")
        return

    customer_number = numbers_to_call[current_index]
    print(f"\n⏩ [{current_index + 1}/{len(numbers_to_call)}] Nächster Kunde wird angewählt: {customer_number}")
    
    try:
        response = client.calls.dial(
            connection_id=APP_ID,
            to=customer_number,
            from_=FROM_NUMBER
        )
        customer_call_id = response.data.call_control_id
        print(f"📡 Kunden-Anruf aufgebaut (ID: {customer_call_id}). Warte auf Freizeichen...")
        
        # WICHTIG: Sobald der Kundenanruf initiiert ist, schlagen wir sofort die Brücke zu DIR
        bridge_calls()
        
        current_index += 1
    except APIError as e:
        print(f"❌ Fehler beim Anrufen des Kunden {customer_number}: {e.message}")
        current_index += 1
        call_next_customer()

def bridge_calls():
    """Schritt 3: Verbindet deine Leitung mit der Leitung des Kunden."""
    global agent_call_id, customer_call_id
    print("🔗 Schweiße Audio-Kanäle zusammen (Bridge)...")
    try:
        client.calls.actions.bridge(
            call_control_id_to_bridge=agent_call_id,
            call_control_id_to_bridge_with=customer_call_id
        )
        print("✅ Bridge-Befehl an Telnyx gesendet. Du solltest den Kunden jetzt hören!")
    except APIError as e:
        print(f"❌ Bridge-Fehler: {e.message}")

@app.route('/webhook', methods=['POST'])
def telnyx_webhook():
    global agent_call_id, customer_call_id
    
    webhook_data = request.json
    event = webhook_data.get("data", {})
    event_type = event.get("event_type")
    payload = event.get("payload", {})
    call_control_id = payload.get("call_control_id")

    # FALL A: Du (der Agent) hast reagiert
    if call_control_id == agent_call_id:
        if event_type == "call.answered":
            print("🟢 Du hast an deinem Headset/Telefon abgehoben!")
            # Sobald DU am Apparat bist, starten wir den ersten Kundenanruf
            call_next_customer()
            
        elif event_type == "call.hangup":
            print("🔴 Deine eigene Leitung wurde getrennt. Dialer stoppt.")
            agent_call_id = None

    # FALL B: Der Kunde hat reagiert
    elif call_control_id == customer_call_id:
        if event_type == "call.answered":
            print("🗣️ Der Kunde hat abgehoben! Gespräch läuft.")
            
        elif event_type == "call.hangup":
            print("📴 Kunde hat aufgelegt (oder war besetzt).")
            customer_call_id = None
            # Kurz durchatmen (2 Sekunden), dann den nächsten Kunden in deine bestehende Leitung werfen
            time.sleep(2)
            call_next_customer()

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    numbers_to_call = load_numbers()
    if not numbers_to_call:
        print("❌ contacts.json ist leer oder fehlt!")
        exit(1)
        
    print(f"📋 {len(numbers_to_call)} Nummern aus JSON geladen.")
    
    # Startet deinen eigenen Anruf 3 Sekunden nach Serverstart
    from threading import Timer
    Timer(3.0, call_the_agent).start()

    # Server starten (wichtig für ngrok)
    app.run(port=5000)