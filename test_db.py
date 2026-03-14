import pymongo
from bson import json_util
import json

uri = "mongodb+srv://autoassist:auto123@cluster0.bbmwvcn.mongodb.net/support_tickets?retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(uri)
db = client.support_tickets

replies = list(db.replies.find({"ticket_id": "M7F499"}).sort("created_at", -1).limit(3))
for r in replies:
    print(f"Reply ID: {r['_id']}")
    print(f"Sender: {r.get('sender_name')}")
    print(f"Message: {r.get('message')}")
    print(f"Attachments type: {type(r.get('attachments'))}")
    if r.get('attachments'):
        for a in r.get('attachments'):
            # Print keys and basic info to avoid dumping massive base64
            print(f" - Attachment keys: {list(a.keys())}")
            print(f" - Filename: {a.get('filename')}")
            print(f" - has_data: {a.get('has_data')}")
            print(f" - file_path: {a.get('file_path')}")
            if a.get('data'):
                print(f" - Data length: {len(str(a.get('data')))}")
    else:
        print(" - No attachments array or empty list")
    print("-" * 50)
