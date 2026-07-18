import requests

url = "https://7c05-2003-e7-b74b-3d00-8c37-997f-7db2-babc.ngrok-free.app"
headers = {
    "Authorization": "Bearer DEIN_API_KEY",
    "Content-Type": "application/json",
}
payload = {
    "webhook_event_url": "https://deine-neue-ngrok-url.ngrok-free.app/webhook"
}
requests.patch(url, json=payload, headers=headers)