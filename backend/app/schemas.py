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

    model_config = {"from_attributes": True}

class MatchOut(BaseModel):
    id: UUID
    lost_item_id: UUID
    found_item_id: UUID
    similarity_score: float
    status: MatchStatus

    model_config = {"from_attributes": True}
        
class UserCreate(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: UUID
    email: str

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class ClaimCreate(BaseModel):
    identifying_answer: str

class ClaimOut(BaseModel):
    id: UUID
    item_id: UUID
    claimant_id: UUID
    identifying_answer: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ClaimStatusUpdate(BaseModel):
    status: str  # "approved" or "rejected"