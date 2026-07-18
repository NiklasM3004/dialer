import os
from dotenv import load_dotenv
from telnyx import Telnyx
from telnyx import APIError

load_dotenv()

# 1. Client initialisieren
client = Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
client = Telnyx(
    api_key=os.environ.get("TELNYX_API_KEY"),  # This is the default and can be omitted
)
page = client.call_control_applications.list()
page = page.data[0]
print(page.id)