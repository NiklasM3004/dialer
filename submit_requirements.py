"""
Telnyx Regulatory Requirements Submitter
-----------------------------------------
Reicht automatisiert alle Dokumente/Angaben ein, die laut GET /requirements
für eine Nummernbestellung (country_code + phone_number_type + action)
notwendig sind.

Ablauf:
  1. Requirements abrufen (GET /requirements)
  2. Für jeden "document"-Requirement-Type: Datei hochladen (POST /documents)
  3. Für jeden "address"-Requirement-Type: Adresse anlegen (POST /addresses)
  4. Requirement Group erstellen (POST /requirement_groups)
  5. Werte in die Requirement Group eintragen (PATCH /requirement_groups/{id})
  6. (Optional) Requirement Group mit einer bestehenden Nummernbestellung
     verknüpfen (POST /number_order_phone_numbers/{id}/requirement_group)

Voraussetzungen:
  pip install requests

Nutzung:
  1. config.json ausfüllen (siehe config.example.json weiter unten im Kommentar)
  2. TELNYX_API_KEY als Umgebungsvariable setzen
  3. python submit_requirements.py config.json
"""

import base64
import json
import os
import sys

import requests

BASE_URL = "https://api.telnyx.com/v2"
API_KEY = os.environ.get("TELNYX_API_KEY")

if not API_KEY:
    sys.exit("Bitte TELNYX_API_KEY als Umgebungsvariable setzen.")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}


def get_requirements(country_code, phone_number_type, action):
    """Schritt 1: Requirements für die gewünschte Kombination abrufen."""
    response = requests.get(
        f"{BASE_URL}/requirements",
        headers=HEADERS,
        params={
            "filter[country_code]": country_code,
            "filter[phone_number_type]": phone_number_type,
            "filter[action]": action,
        },
    )
    response.raise_for_status()
    data = response.json()["data"]

    if not data:
        print("Keine Requirements gefunden - für diese Kombination ist vermutlich nichts einzureichen.")
        return []

    return data[0]["requirement_types"]


def upload_document(filepath):
    """Schritt 2: Ein Dokument hochladen (multipart), liefert die document_id zurück."""
    with open(filepath, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/documents",
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file": (os.path.basename(filepath), f)},
        )
    response.raise_for_status()
    document_id = response.json()["data"]["id"]
    print(f"Dokument hochgeladen: {filepath} -> {document_id}")
    return document_id


def create_address(address_dict):
    """Schritt 3: Adresse anlegen, liefert die address_id zurück."""
    response = requests.post(
        f"{BASE_URL}/addresses",
        headers={**HEADERS, "Content-Type": "application/json"},
        json=address_dict,
    )
    response.raise_for_status()
    address_id = response.json()["data"]["id"]
    print(f"Adresse angelegt -> {address_id}")
    return address_id


def create_requirement_group(country_code, phone_number_type, action):
    """Schritt 4: Requirement Group anlegen, liefert (group_id, requirement_ids)."""
    response = requests.post(
        f"{BASE_URL}/requirement_groups",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={
            "country_code": country_code,
            "phone_number_type": phone_number_type,
            "action": action,
        },
    )
    response.raise_for_status()
    data = response.json()["data"]
    group_id = data["id"]
    print(f"Requirement Group erstellt: {group_id}")
    return group_id, data["regulatory_requirements"]


def fill_requirement_group(group_id, filled_requirements):
    """
    Schritt 5: Werte in die Requirement Group eintragen.
    filled_requirements: Liste von {"requirement_id": ..., "field_value": ...}
    """
    response = requests.patch(
        f"{BASE_URL}/requirement_groups/{group_id}",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"regulatory_requirements": filled_requirements},
    )
    response.raise_for_status()
    print(f"Requirement Group {group_id} mit Werten befüllt.")
    return response.json()["data"]


def attach_to_number_order(number_order_phone_number_id, group_id):
    """Schritt 6 (optional): Requirement Group mit einer bestehenden Bestellung verknüpfen."""
    response = requests.post(
        f"{BASE_URL}/number_order_phone_numbers/{number_order_phone_number_id}/requirement_group",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"requirement_group_id": group_id},
    )
    response.raise_for_status()
    print(f"Requirement Group {group_id} mit Bestellung {number_order_phone_number_id} verknüpft.")
    return response.json()["data"]


def main(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    country_code = config["country_code"]
    phone_number_type = config["phone_number_type"]
    action = config["action"]

    # 1. Requirements abrufen, um die requirement_type_ids und deren Typen zu kennen
    requirement_types = get_requirements(country_code, phone_number_type, action)
    type_by_id = {rt["id"]: rt["type"] for rt in requirement_types}
    name_by_id = {rt["id"]: rt["name"] for rt in requirement_types}

    # 2. Requirement Group anlegen (liefert leere Platzhalter je requirement_id)
    group_id, empty_requirements = create_requirement_group(country_code, phone_number_type, action)

    # 3. Für jede Anforderung den passenden Wert aus der config besorgen/erzeugen
    filled_requirements = []
    for req in empty_requirements:
        requirement_id = req["requirement_id"]
        req_type = type_by_id.get(requirement_id, req.get("field_type"))
        req_name = name_by_id.get(requirement_id, requirement_id)

        entry = config["values"].get(requirement_id)
        if entry is None:
            print(f"WARNUNG: Kein Wert in config.json für '{req_name}' ({requirement_id}) hinterlegt - übersprungen.")
            continue

        if req_type == "document":
            field_value = upload_document(entry["file_path"])
        elif req_type == "address":
            field_value = create_address(entry["address"])
        else:  # textual
            field_value = entry["text"]

        filled_requirements.append({
            "requirement_id": requirement_id,
            "field_value": field_value,
        })

    # 4. Werte eintragen
    result = fill_requirement_group(group_id, filled_requirements)

    # 5. Optional: direkt mit einer bestehenden Nummernbestellung verknüpfen
    if config.get("number_order_phone_number_id"):
        attach_to_number_order(config["number_order_phone_number_id"], group_id)

    print("\nFertig. Requirement Group ID (für zukünftige Bestellungen wiederverwendbar):")
    print(group_id)
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Nutzung: python submit_requirements.py config.json")
    main(sys.argv[1])


# ---------------------------------------------------------------------------
# Beispiel config.json für eine deutsche Lokalnummer (Requirement-IDs aus
# eurer vorherigen GET /requirements-Antwort für DE/local/ordering):
#
# {
#   "country_code": "DE",
#   "phone_number_type": "local",
#   "action": "ordering",
#   "number_order_phone_number_id": null,
#   "values": {
#     "2708e569-696a-4fc7-9305-5fdb3eb9c7dd": {
#       "text": "Contact: Max Mustermann | Business: Beispiel GmbH | Phone: +4930xxxxxxx"
#     },
#     "6d3e2643-efaa-4bd3-8c31-77b6cda1d6a2": {
#       "file_path": "./docs/proof_of_address.pdf"
#     },
#     "6f9a47f5-da93-4e7b-91ab-02e38b596d70": {
#       "file_path": "./docs/handelsregisterauszug.pdf"
#     },
#     "95cac7a7-cf24-4d34-81e4-e2d01a35adda": {
#       "file_path": "./docs/bnetza_formular.pdf"
#     },
#     "a7d9a3a3-70ed-4cb4-821b-b94e8ea6dc9b": {
#       "address": {
#         "first_name": "Max",
#         "last_name": "Mustermann",
#         "business_name": "Beispiel GmbH",
#         "street_address": "Musterstraße 1",
#         "locality": "Berlin",
#         "postal_code": "10115",
#         "country_code": "DE"
#       }
#     }
#   }
# }
# ---------------------------------------------------------------------------