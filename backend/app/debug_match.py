from app.database import SessionLocal
from app.models import Item, ItemType

db = SessionLocal()
items = db.query(Item).all()

for item in items:
    print(f"{item.id} | {item.type} | {item.category} | {item.description}")

# pick two items you expect to match, replace IDs below
lost = db.query(Item).filter(Item.type == ItemType.lost).first()
found = db.query(Item).filter(Item.type == ItemType.found).first()

if lost and found:
    distance = db.query(
        Item.embedding.cosine_distance(lost.embedding)
    ).filter(Item.id == found.id).scalar()
    print(f"\nSimilarity between '{lost.category}' and '{found.category}': {1 - distance}")

db.close()