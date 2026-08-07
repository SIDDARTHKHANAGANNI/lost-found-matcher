import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Item, ItemType
from app.schemas import ItemOut, MatchOut
from app.services.embedding import embedding_service
from app.services.matching import find_matches, save_matches
from app.config import settings
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=ItemOut)
async def create_item(
    type: ItemType = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(settings.upload_dir, filename)

    with open(filepath, "wb") as f:
        f.write(await image.read())

    embedding = embedding_service.embed_combined(filepath, description)

    item = Item(
        user_id=user_id,
        type=type,
        category=category,
        description=description,
        location=location,
        image_url=filepath,
        embedding=embedding,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    matches = find_matches(db, item)
    if matches:
        save_matches(db, item, matches)

    return item


@router.get("/{item_id}/matches", response_model=list[MatchOut])
def get_matches(item_id: uuid.UUID, db: Session = Depends(get_db)):
    from app.models import Match
    matches = db.query(Match).filter(
        (Match.lost_item_id == item_id) | (Match.found_item_id == item_id)
    ).order_by(Match.similarity_score.desc()).all()
    if not matches:
        raise HTTPException(status_code=404, detail="No matches found")
    return matches


@router.get("/", response_model=list[ItemOut])
def list_items(type: ItemType | None = None, db: Session = Depends(get_db)):
    query = db.query(Item)
    if type:
        query = query.filter(Item.type == type)
    return query.order_by(Item.created_at.desc()).all()