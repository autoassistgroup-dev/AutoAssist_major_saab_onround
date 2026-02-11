"""Check technicians in database."""
from dotenv import load_dotenv
load_dotenv()

from database import get_db

db = get_db()

print("\n=== TECHNICIANS CHECK ===\n")

all_techs = list(db.technicians.find())
print(f"Total technicians: {len(all_techs)}")

active_techs = list(db.technicians.find({"is_active": True}))
print(f"Active technicians: {len(active_techs)}")

print("\n--- Active Technicians ---")
for tech in active_techs:
    print(f"  - {tech.get('name')} ({tech.get('role', 'N/A')})")
    print(f"    ID: {tech.get('_id')}")
    print(f"    Email: {tech.get('email', 'N/A')}")
    print()
