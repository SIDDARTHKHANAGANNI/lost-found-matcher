from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate,UserLogin, UserOut, Token
from app.auth import hash_password, verify_password, create_access_token
from app.services.rate_limit import (
    limiter, check_account_backoff, record_failed_attempt, clear_failed_attempts
)
from app.config import settings

router = APIRouter()

@router.post("/signup", response_model=UserOut)
@limiter.limit(settings.rate_limit_auth_per_ip)
def signup(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=user_in.email, hashed_password=hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
@limiter.limit(settings.rate_limit_auth_per_ip)
def login(request: Request, user_in: UserLogin, db: Session = Depends(get_db)):
    check_account_backoff(user_in.email)

    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        record_failed_attempt(user_in.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    clear_failed_attempts(user_in.email)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}