import os
from dotenv import load_dotenv
from telnyx import Telnyx

# 1. .env laden
load_dotenv()

# 2. Key auslesen
api_key = os.getenv("TELNYX_API_KEY")

# 3. Client INITIALISIEREN und den Key übergeben!
client = Telnyx(api_key=api_key)
client = Telnyx(
    api_key=os.environ.get("TELNYX_API_KEY"),  # This is the default and can be omitted
)
call_control_application = client.call_control_applications.delete(
    "3006446897096295558",
)
print(call_control_application.data)