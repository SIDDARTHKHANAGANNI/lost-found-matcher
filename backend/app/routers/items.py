import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Item, ItemType, Match, Claim, User
from app.schemas import (
    ItemOut, ItemCreate, MatchOut, MatchUpdate, ClaimCreate, ClaimOut,
    ClaimStatusUpdate, ContactInfo
)
from app.services.embedding import embedding_service
from app.services.matching import find_matches, save_matches
from app.config import settings
from app.auth import get_current_user
from app.services.rate_limit import limiter
from pydantic import ValidationError
from PIL import Image
from PIL import UnidentifiedImageError
import io
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024  # 8MB
router = APIRouter()


@router.get("/browse", response_model=list[ItemOut])
@limiter.limit(settings.rate_limit_public)
def browse_items(
    request: Request,
    type: ItemType = ItemType.found,
    category: str | None = None,
    location: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Item).filter(Item.type == type)
    if category:
        query = query.filter(Item.category == category)
    if location:
        query = query.filter(Item.location == location)
    if search:
        query = query.filter(Item.description.ilike(f"%{search}%"))
    return query.order_by(Item.created_at.desc()).all()


@router.get("/my-matches", response_model=list[MatchOut])
@limiter.limit(settings.rate_limit_authenticated)
def my_matches(
    request: Request,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    my_item_ids = [i.id for i in db.query(Item).filter(Item.user_id == user_id).all()]
    matches = db.query(Match).filter(
        (Match.lost_item_id.in_(my_item_ids)) | (Match.found_item_id.in_(my_item_ids))
    ).order_by(Match.created_at.desc()).all()
    return matches


@router.get("/mine/all", response_model=list[ItemOut])
@limiter.limit(settings.rate_limit_authenticated)
def my_items(
    request: Request,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    return db.query(Item).filter(Item.user_id == user_id).order_by(Item.created_at.desc()).all()


@router.get("/my-claims/submitted", response_model=list[ClaimOut])
@limiter.limit(settings.rate_limit_authenticated)
def my_submitted_claims(
    request: Request,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    claims = db.query(Claim).filter(Claim.claimant_id == user_id).order_by(Claim.created_at.desc()).all()
    return claims


@router.post("/", response_model=ItemOut)
@limiter.limit(settings.rate_limit_authenticated)
async def create_item(
    request: Request,
    type: ItemType = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    try:
        validated = ItemCreate(type=type, category=category, description=description, location=location)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    
    # size check first, cheapest rejection
    contents = await image.read()
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Image exceeds 8MB size limit")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # verify the file is genuinely a valid image by attempting to decode it —
    # extension and Content-Type headers are client-supplied and can be spoofed,
    # so we never trust them alone
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()  # checks structural validity without fully decoding
        # re-open after verify() (verify() invalidates the file pointer)
        img = Image.open(io.BytesIO(contents))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="File is not a valid image")

    if img.format not in {"JPEG", "PNG", "WEBP"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format: {img.format}. Allowed: JPEG, PNG, WEBP",
        )

    # re-encode to strip any embedded payloads/metadata (polyglot file defense) —
    # we never write the client's raw bytes to disk, only a clean re-render
    img = img.convert("RGB")
    output_buffer = io.BytesIO()
    save_format = "JPEG" if img.format != "PNG" else "PNG"
    img.save(output_buffer, format=save_format, quality=90)
    clean_contents = output_buffer.getvalue()

    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = "jpg" if save_format == "JPEG" else "png"
    filename = f"{uuid.uuid4()}.{ext}"  # server-generated name — never trust client filename
    filepath = os.path.join(settings.upload_dir, filename)

    with open(filepath, "wb") as f:
        f.write(clean_contents)
        
    embedding = embedding_service.embed_combined(filepath, validated.description)

    item = Item(
        user_id=user_id,
        type=validated.type,
        category=validated.category,
        description=validated.description,
        location=validated.location,
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


@router.get("/", response_model=list[ItemOut])
@limiter.limit(settings.rate_limit_public)
def list_items(request: Request, type: ItemType | None = None, db: Session = Depends(get_db)):
    query = db.query(Item)
    if type:
        query = query.filter(Item.type == type)
    return query.order_by(Item.created_at.desc()).all()


@router.get("/{item_id}", response_model=ItemOut)
@limiter.limit(settings.rate_limit_public)
def get_item(request: Request, item_id: uuid.UUID, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/{item_id}/claim", response_model=ClaimOut)
@limiter.limit(settings.rate_limit_authenticated)
def submit_claim(
    request: Request,
    item_id: uuid.UUID,
    claim_in: ClaimCreate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    claim = Claim(
        item_id=item_id,
        claimant_id=user_id,
        identifying_answer=claim_in.identifying_answer,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


@router.get("/{item_id}/claims", response_model=list[ClaimOut])
@limiter.limit(settings.rate_limit_authenticated)
def list_claims(request: Request, item_id: uuid.UUID, db: Session = Depends(get_db)):
    claims = db.query(Claim).filter(Claim.item_id == item_id).order_by(Claim.created_at.desc()).all()
    return claims


@router.get("/{item_id}/matches", response_model=list[MatchOut])
@limiter.limit(settings.rate_limit_authenticated)
def get_matches(request: Request, item_id: uuid.UUID, db: Session = Depends(get_db)):
    matches = db.query(Match).filter(
        (Match.lost_item_id == item_id) | (Match.found_item_id == item_id)
    ).order_by(Match.similarity_score.desc()).all()
    if not matches:
        raise HTTPException(status_code=404, detail="No matches found")
    return matches


@router.patch("/matches/{match_id}", response_model=MatchOut)
@limiter.limit(settings.rate_limit_authenticated)
def update_match_status(
    request: Request, match_id: uuid.UUID, update: MatchUpdate, db: Session = Depends(get_db)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.status = update.status
    db.commit()
    db.refresh(match)
    return match


@router.patch("/claims/{claim_id}", response_model=ClaimOut)
@limiter.limit(settings.rate_limit_authenticated)
def update_claim_status(
    request: Request,
    claim_id: uuid.UUID,
    update: ClaimStatusUpdate,
    db: Session = Depends(get_db),
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    claim.status = update.status
    db.commit()
    db.refresh(claim)
    return claim


@router.get("/claims/{claim_id}/contact", response_model=ContactInfo)
@limiter.limit(settings.rate_limit_authenticated)
def get_contact_after_approval(
    request: Request,
    claim_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != "approved":
        raise HTTPException(status_code=403, detail="Claim not yet approved")
    if claim.claimant_id != user_id:
        raise HTTPException(status_code=403, detail="Not your claim")

    item = db.query(Item).filter(Item.id == claim.item_id).first()
    finder = db.query(User).filter(User.id == item.user_id).first()
    return ContactInfo(email=finder.email)