from dotenv import load_dotenv
load_dotenv()
from database import get_db
from flask import Flask
app = Flask(__name__)

with app.app_context():
    db = get_db()
    tickets = list(db.tickets.find().sort("created_at", -1).limit(5))

    print(f"Found {len(tickets)} recent tickets:")
    for t in tickets:
        ticket_id = t.get('ticket_id')
        n8n_draft = t.get('n8n_draft')
        draft_body = t.get('draft_body')
        draft = t.get('draft')
        print(f"\n--- {ticket_id} ---")
        print(f"Subject: {t.get('subject')}")
        print(f"Created at: {t.get('created_at')}")
        print(f"n8n_draft length: {len(n8n_draft) if n8n_draft else 0}")
        print(f"draft_body length: {len(draft_body) if draft_body else 0}")
        print(f"draft length: {len(draft) if draft else 0}")
        
        if draft_body:
            print(f"draft_body snippet: {draft_body[:100]}...")
