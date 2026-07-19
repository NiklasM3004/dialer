import os
import requests
from dotenv import load_dotenv
from telnyx import Telnyx
from telnyx import APIError

load_dotenv()

# 1. Client initialisieren
client = Telnyx(api_key=os.getenv("TELNYX_API_KEY"))


response = requests.get(
    "https://api.telnyx.com/v2/requirements",
    headers={
        "Authorization": f"Bearer {os.environ['TELNYX_API_KEY']}",
        "Accept": "application/json",
    },
    params={
        "filter[country_code]": "US",
        "filter[phone_number_type]": "local",
        "filter[action]": "ordering",
    },
)

data = response.json()
print(data)