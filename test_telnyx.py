import os
from dotenv import load_dotenv
from telnyx import Telnyx

# 1. .env laden
load_dotenv()

# 2. Key auslesen
api_key = os.getenv("TELNYX_API_KEY")

# 3. Client INITIALISIEREN und den Key übergeben!
client = Telnyx(api_key=api_key)

response = client.calls.dial(
    connection_id="conn12345",
    from_="+15557654321",
    to="+15156925081",
    # webhook_url="https://your-webhook.url/events",
)
print(response.data)