from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models import ItemType, MatchStatus

class ItemCreate(BaseModel):
    type: ItemType
    category: str
    description: str
    location: str

class ItemOut(BaseModel):
    id: UUID
    type: ItemType
    category: str
    description: str
    location: str
    image_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class MatchOut(BaseModel):
    id: UUID
    lost_item_id: UUID
    found_item_id: UUID
    similarity_score: float
    status: MatchStatus

    class Config:
        from_attributes = True