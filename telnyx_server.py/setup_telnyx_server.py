import os
from telnyx import Telnyx
from dotenv import load_dotenv
from telnyx import Telnyx
# Wir importieren hier die allgemeine Telnyx API-Fehlerklasse
from telnyx import APIError 

# 1. .env-Datei laden
load_dotenv()



client = Telnyx(
    api_key=os.environ.get("TELNYX_API_KEY"),  # This is the default and can be omitted
)
call_control_application = client.call_control_applications.create(
    application_name="call-router",
    webhook_event_url="https://webhook.site/981ba2ac-ba24-4918-8ea5-c758016887a7",
)
print(call_control_application.data)