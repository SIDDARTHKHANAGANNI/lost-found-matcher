from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Item, ItemType, Match
from app.services.location import location_score

def time_score(t1: datetime, t2: datetime, max_days: float = 14.0) -> float:
    diff_days = abs((t1 - t2).total_seconds()) / 86400
    if diff_days >= max_days:
        return 0.0
    return 1.0 - (diff_days / max_days)

def find_matches(db: Session, item: Item, top_k: int = 5, min_similarity: float = 0.75):
    opposite_type = ItemType.found if item.type == ItemType.lost else ItemType.lost

    candidates = (
        db.query(Item)
        .filter(Item.type == opposite_type, Item.category == item.category)
        .order_by(Item.embedding.cosine_distance(item.embedding))
        .limit(top_k * 2)  # pull more, rerank below
        .all()
    )

    results = []
    for candidate in candidates:
        distance = db.query(
            Item.embedding.cosine_distance(item.embedding)
        ).filter(Item.id == candidate.id).scalar()
        clip_similarity = 1 - distance

        if clip_similarity < min_similarity:
            continue

        loc_score = location_score(item.location, candidate.location)
        t_score = time_score(item.created_at, candidate.created_at)

        # weighted final score: CLIP similarity dominant, location/time as tiebreakers/boosters
        final_score = (0.7 * clip_similarity) + (0.2 * loc_score) + (0.1 * t_score)
        results.append((candidate, final_score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


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