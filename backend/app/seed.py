import shutil
import uuid
from app.database import SessionLocal
from app.models import Item, ItemType
from app.services.embedding import embedding_service
from app.services.matching import find_matches, save_matches
SAMPLE_ITEMS = [
    {"type": "lost", "category": "backpack", "description": "black jansport backpack, left in library", "location": "Library", "source": "tests/sample_images/backpack_1.jpg"},
    {"type": "found", "category": "backpack", "description": "black backpack found near canteen", "location": "Canteen", "source": "tests/sample_images/backpack_2.jpg"},
    {"type": "lost", "category": "bottle", "description": "blue steel water bottle", "location": "Sports Complex", "source": "tests/sample_images/bottle_1.jpg"},
    {"type": "found", "category": "bottle", "description": "blue water bottle found at gym", "location": "Gym", "source": "tests/sample_images/bottle_2.jpg"},
    {"type": "lost", "category": "phone", "description": "black iphone with cracked screen", "location": "Auditorium", "source": "tests/sample_images/phone_1.jpg"},
]

def seed():
    db = SessionLocal()
    for i, entry in enumerate(SAMPLE_ITEMS):
        dest_path = f"uploads/seed_{i}.jpg"
        shutil.copy(entry["source"], dest_path)

        embedding = embedding_service.embed_combined(dest_path, entry["description"])

        item = Item(
            user_id=uuid.uuid4(),
            type=ItemType(entry["type"]),
            category=entry["category"],
            description=entry["description"],
            location=entry["location"],
            image_url=dest_path,
            embedding=embedding,
        )
        db.add(item)
        print(f"seeded: {entry['type']} - {entry['category']} from {entry['source']}")
    db.commit()

    # second pass — compute matches now that all items exist
    all_items = db.query(Item).all()
    for item in all_items:
        matches = find_matches(db, item)
        if matches:
            saved = save_matches(db, item, matches)
            print(f"matched {item.category} ({item.type}) -> {len(saved)} match(es)")

    db.close()

if __name__ == "__main__":
    seed()