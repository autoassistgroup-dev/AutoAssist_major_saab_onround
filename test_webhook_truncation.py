import requests
import json

url = "http://localhost:5000/api/webhook/reply"
ticket_id = "WT0939"  # Use a valid ticket ID from previous context or generic

long_message = "START " + "A" * 5000 + " END"

payload = {
    "ticket_id": ticket_id,
    "sender_name": "Test Tester",
    "message": long_message,
    "from": "test@example.com"
}

try:
    print(f"Sending message of length {len(long_message)}...")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Now verify by fetching the ticket replies (if I can)
    # But I can't fetch replies easily without auth.
    # I trust the response for now.
except Exception as e:
    print(f"Error: {e}")
