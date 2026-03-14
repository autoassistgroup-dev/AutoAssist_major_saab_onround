from app import create_app
from database import get_db
from bson.objectid import ObjectId

app = create_app()
with app.app_context():
    db = get_db()
    member = db.members.find_one({"_id": ObjectId("6971c6ee969247226ebdb221")})
    if member:
        print("Forwarded by member:", member.get("name"), member.get("role"))
    else:
        print("Member not found in DB")
        from pprint import pprint
        print("All members:")
        for m in db.members.find({}, {"_id": 1, "name": 1, "role": 1}):
            pprint(m)
