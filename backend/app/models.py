import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
import enum
from app.database import Base
from sqlalchemy import Boolean

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class ItemType(str, enum.Enum):
    lost = "lost"
    found = "found"

class MatchStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"

class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    type = Column(Enum(ItemType), nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    location = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    embedding = Column(Vector(512))  # CLIP ViT-B/32 output dim
    created_at = Column(DateTime, default=datetime.utcnow)

class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lost_item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    found_item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    status = Column(Enum(MatchStatus), default=MatchStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)  # the found item being claimed
    claimant_id = Column(UUID(as_uuid=True), nullable=False)
    identifying_answer = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending/approved/rejected
    created_at = Column(DateTime, default=datetime.utcnow)