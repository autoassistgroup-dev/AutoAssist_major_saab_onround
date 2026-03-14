from app import create_app
from database import get_db

app = create_app()
with app.app_context():
    db = get_db()
    for t in db.tickets.find({"is_forwarded": True}):
        f_by = db.members.find_one({"_id": t.get("forwarded_by")})
        f_to = db.members.find_one({"_id": t.get("forwarded_to")})
        by_name = f_by.get("name") if f_by else str(t.get("forwarded_by"))
        to_name = f_to.get("name") if f_to else str(t.get("forwarded_to"))
        print(f"Ticket {t.get('ticket_id')} forwarded by {by_name} TO {to_name}")
