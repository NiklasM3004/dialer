import os
import json
from dotenv import load_dotenv
from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest
from hubspot.crm.contacts.exceptions import ApiException

# 1. .env-Datei laden
load_dotenv()

# 2. HubSpot Client mit dem Token initialisieren
api_key = os.getenv("HUBSPOT_ACCESS_TOKEN")
api_client = HubSpot(access_token=api_key)

def search_and_save_uncontacted_leads():
    # 3. Suchanfrage definieren (Filter: Kontakte ohne jegliche Kontaktaufnahme)
    search_request = PublicObjectSearchRequest(
        filter_groups=[
            {
                "filters": [
                    {
                        "propertyName": "notes_last_updated",
                        "operator": "NOT_HAS_PROPERTY" 
                    }
                ]
            }
        ],
        # Diese Felder werden von HubSpot angefordert
        properties=["firstname", "lastname", "email", "notes_last_updated", "hs_createdate"],
        limit=100
    )

    try:
        print("🔍 Suche nach unkontaktierten Kontakten in HubSpot...")
        
        # 4. Den Search-Endpunkt aufrufen
        api_response = api_client.crm.contacts.search_api.do_search(
            public_object_search_request=search_request
        )
        
        print(f"✅ {api_response.total} unkontaktierte Kontakte gefunden.")
        
        # 5. Daten für den JSON-Export aufbereiten
        contacts_list = []
        for contact in api_response.results:
            # Wir ziehen uns die relevanten Daten aus dem .properties-Dict
            props = contact.properties
            
            contact_data = {
                "id": contact.id,
                "firstname": props.get('firstname'),
                "lastname": props.get('lastname'),
                "email": props.get('email'),
                "created_at": props.get('hs_createdate'),
                "notes_last_updated": props.get('notes_last_updated')
            }
            contacts_list.append(contact_data)
        
        # Gesamtes Datenpaket schnüren (inklusive Metadaten)
        output_data = {
            "total_count": api_response.total,
            "contacts": contacts_list
        }
        
        # 6. In JSON-Datei schreiben
        output_filename = "hubspot_uncontacted_contacts.json"
        with open(output_filename, "w", encoding="utf-8") as json_file:
            # indent=4 formatiert das JSON mit Absätzen und Einrückungen
            json.dump(output_data, json_file, indent=4, ensure_ascii=False)
            
        print(f"💾 Daten erfolgreich in '{output_filename}' gespeichert!")

    except ApiException as e:
        print(f"❌ Fehler beim Aufruf der HubSpot API: {e}")

if __name__ == "__main__":
    search_and_save_uncontacted_leads()