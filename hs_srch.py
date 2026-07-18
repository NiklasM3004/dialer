import os
from dotenv import load_dotenv
from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest
from hubspot.crm.contacts.exceptions import ApiException

# 1. .env-Datei laden
load_dotenv()

# 2. HubSpot Client mit dem Token initialisieren
# (os.getenv liest den Wert aus der geladenen .env)
api_key = os.getenv("HUBSPOT_ACCESS_TOKEN")
api_client = HubSpot(access_token=api_key)

def search_hubspot_contacts():
    # 3. Suchanfrage (Search Request Object) definieren
    search_request = PublicObjectSearchRequest(
        filter_groups=[
            {
                "filters": [
                    {
                        "propertyName": "firstname",
                        "operator": "EQ",  # EQ = Equal (Gleich)
                        "value": "Max"
                    }
                ]
            }
        ],
        # Welche Felder sollen im Ergebnis enthalten sein?
        properties=["firstname", "lastname", "email"],
        limit=10
    )

    try:
        print("Starte Suche in HubSpot...")
        
        # 4. Den Search-Endpunkt aufrufen
        api_response = api_client.crm.contacts.search_api.do_search(
            public_object_search_request=search_request
        )
        
        # 5. Ergebnisse ausgeben
        print(f"Erfolgreich! {api_response.total} Ergebnisse gefunden.\n")
        
        for contact in api_response.results:
            # Die eigentlichen Daten liegen im '.properties'-Dictionary des Kontakts
            props = contact.properties
            print(f"Name: {props.get('firstname')} {props.get('lastname')} | E-Mail: {props.get('email')}")

    except ApiException as e:
        print(f"Fehler beim Aufruf der HubSpot API: {e}")

if __name__ == "__main__":
    search_hubspot_contacts()