import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from datetime import datetime
from app.models import ItemType, MatchStatus
from app.config import settings


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def email_domain_restricted(cls, v: str) -> str:
        domain = v.split("@")[-1].lower()
        if domain not in settings.allowed_domains_list:
            raise ValueError(
                f"Signup restricted to university email addresses ({', '.join(settings.allowed_domains_list)})"
            )
        return v

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        return v
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)
class UserOut(BaseModel):
    id: UUID
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Items ----------

ALLOWED_CATEGORIES = {
    "backpack", "bottle", "phone", "wallet", "umbrella", "keys",
    "laptop", "charger", "book", "id_card", "headphones", "bag", "other"
}

class ItemCreate(BaseModel):
    type: ItemType
    category: str = Field(..., min_length=2, max_length=40)
    description: str = Field(..., min_length=5, max_length=500)
    location: str = Field(..., min_length=2, max_length=100)

    @field_validator("category")
    @classmethod
    def category_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[a-z0-9 _-]+", v):
            raise ValueError("Category may only contain letters, numbers, spaces, - and _")
        return v

    @field_validator("description")
    @classmethod
    def description_no_control_chars(cls, v: str) -> str:
        v = v.strip()
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", v):
            raise ValueError("Description contains invalid control characters")
        return v

    @field_validator("location")
    @classmethod
    def location_format(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r"[A-Za-z0-9 .,'-]+", v):
            raise ValueError("Location contains invalid characters")
        return v


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


# ---------- Matches ----------

class MatchOut(BaseModel):
    id: UUID
    lost_item_id: UUID
    found_item_id: UUID
    similarity_score: float
    status: MatchStatus

    class Config:
        from_attributes = True


class MatchUpdate(BaseModel):
    status: MatchStatus


# ---------- Claims ----------

class ClaimCreate(BaseModel):
    identifying_answer: str = Field(..., min_length=10, max_length=500)

    @field_validator("identifying_answer")
    @classmethod
    def answer_no_control_chars(cls, v: str) -> str:
        v = v.strip()
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", v):
            raise ValueError("Answer contains invalid control characters")
        return v


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
    status: str = Field(..., pattern="^(approved|rejected)$")


class ContactInfo(BaseModel):
    email: str  