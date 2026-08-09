from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models import ItemType, MatchStatus
from app.models import MatchStatus

class MatchUpdate(BaseModel):
    status: MatchStatus
    
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
        
class UserCreate(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: UUID
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"