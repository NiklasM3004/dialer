import os
from dotenv import load_dotenv
from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest
from hubspot.crm.contacts.exceptions import ApiException

# 1. .env-Datei laden
load_dotenv()

# 2. HubSpot Client mit dem Token initialisieren
api_key = os.getenv("HUBSPOT_ACCESS_TOKEN")
api_client = HubSpot(access_token=api_key)

def search_uncontacted_leads():
    # 3. Suchanfrage definieren
    search_request = PublicObjectSearchRequest(
        filter_groups=[
            {
                "filters": [
                    {
                        # 'notes_last_updated' speichert den Zeitstempel der letzten Kontaktaufnahme.
                        # Wenn dieser leer ist, gab es noch keine Interaktion.
                        "propertyName": "notes_last_updated",
                        "operator": "NOT_HAS_PROPERTY" 
                    }
                ]
            }
        ],
        # Wir lassen uns wichtige Felder und das Datum der letzten Aktivität ausgeben,
        # um im Print-Befehl zu verifizieren, dass das Feld wirklich leer ist.
        properties=["firstname", "lastname", "email", "notes_last_updated", "hs_createdate"],
        limit=50
    )

    try:
        print("Suche nach Kontakten ohne bisherige Kontaktaufnahme...")
        
        # 4. Den Search-Endpunkt aufrufen
        api_response = api_client.crm.contacts.search_api.do_search(
            public_object_search_request=search_request
        )
        
        print(f"Erfolgreich! {api_response.total} unkontaktierte Kontakte gefunden.\n")
        
        # 5. Ergebnisse ausgeben
        for contact in api_response.results:
            props = contact.properties
            firstname = props.get('firstname') or "Kein Vorname"
            lastname = props.get('lastname') or "Kein Nachname"
            email = props.get('email') or "Keine E-Mail"
            created_at = props.get('hs_createdate')
            
            print(f"- {firstname} {lastname} ({email}) | Erstellt am: {created_at}")

    except ApiException as e:
        print(f"Fehler beim Aufruf der HubSpot API: {e}")

if __name__ == "__main__":
    search_uncontacted_leads()