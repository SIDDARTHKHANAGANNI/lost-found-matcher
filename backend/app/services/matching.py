from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Item, ItemType, Match

def find_matches(db: Session, item: Item, top_k: int = 5, min_similarity: float = 0.75):
    opposite_type = ItemType.found if item.type == ItemType.lost else ItemType.lost

    # pgvector cosine distance: 1 - cosine_similarity, so smaller = more similar
    candidates = (
        db.query(Item)
        .filter(Item.type == opposite_type, Item.category == item.category)
        .order_by(Item.embedding.cosine_distance(item.embedding))
        .limit(top_k)
        .all()
    )

    results = []
    for candidate in candidates:
        distance = db.query(
            Item.embedding.cosine_distance(item.embedding)
        ).filter(Item.id == candidate.id).scalar()
        similarity = 1 - distance
        if similarity >= min_similarity:
            results.append((candidate, similarity))
    return results


def save_matches(db: Session, item: Item, matches: list[tuple[Item, float]]):
    saved = []
    for candidate, score in matches:
        lost_id = item.id if item.type == ItemType.lost else candidate.id
        found_id = candidate.id if item.type == ItemType.lost else item.id

        existing = db.query(Match).filter(
            Match.lost_item_id == lost_id, Match.found_item_id == found_id
        ).first()
        if existing:
            continue

        match = Match(lost_item_id=lost_id, found_item_id=found_id, similarity_score=score)
        db.add(match)
        saved.append(match)
    db.commit()
    return saved