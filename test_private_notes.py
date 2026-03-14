import requests
import json

base_url = 'https://auto-assist-portal.vercel.app'
ticket_id = 'TE2029' # Use an open ticket from the DB

session = requests.Session()

# 0. Get CSRF token if needed (many APIs don't check it but let's see)
# 1. Login as Admin
print("Logging in as admin...")
res = session.post(f"{base_url}/api/auth/login", json={'user_id': 'admin001', 'password': 'admin@123'})
print("Admin login status:", res.status_code)

# 2. Forward to Tech
print(f"\nForwarding {ticket_id} to tech director...")
res = session.post(f"{base_url}/api/tickets/{ticket_id}/tech-director", json={'referral_note': 'API Test Forward Note'})
print("Forward status:", res.status_code)
print("Forward response:", res.json() if res.status_code == 200 else res.text)

# 3. Logout
session.get(f"{base_url}/api/auth/logout")

# 4. Login as Tech Director
print("\nLogging in as Tech Director...")
res = session.post(f"{base_url}/api/auth/login", json={'user_id': 'marc001', 'password': 'tech@123'})
print("Tech login status:", res.status_code)

# 5. Return to Admin
print(f"\nReturning {ticket_id} to admin...")
res = session.post(f"{base_url}/api/tickets/{ticket_id}/refer-back-to-admin", json={'referral_note': 'API Test Return Note'})
print("Return status:", res.status_code)
print("Return response:", res.json() if res.status_code == 200 else res.text)

# 6. Check Private Notes
print(f"\nFetching private notes for {ticket_id}...")
res = session.get(f"{base_url}/api/tickets/{ticket_id}/private-notes")
print("Notes status:", res.status_code)
if res.status_code == 200:
    notes = res.json().get('notes', [])
    print(f"Found {len(notes)} private notes:")
    for i, n in enumerate(notes):
        print(f"  Note {i+1}: [{n.get('author')}] {n.get('title')} - {n.get('content')}")
else:
    print("Failed to fetch private notes.")
