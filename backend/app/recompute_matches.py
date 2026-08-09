from app.database import SessionLocal
from app.models import Item
from app.services.matching import find_matches, save_matches

db = SessionLocal()
items = db.query(Item).all()

for item in items:
    matches = find_matches(db, item)
    if matches:
        saved = save_matches(db, item, matches)
        print(f"{item.category} ({item.type}) -> {len(saved)} match(es)")

db.close()