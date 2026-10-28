from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from ..schemas.schemas import UserCreate, UserResponse, Token
from ..core.security import verify_password, get_password_hash, create_access_token
from ..core.config import settings

router = APIRouter()

# Dummy DB dependency for now
def get_db():
    yield None

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # This is a stub. Real implementation will use DB session.
    # user = db.query(User).filter(User.email == user_in.email).first()
    # if user: raise HTTPException(status_code=400, detail="Email already registered")
    return {
        "id": 1,
        "email": user_in.email,
        "role": "user",
        "created_at": "2026-04-17T00:00:00Z"
    }

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Stub implementation
    # user = db.query(User).filter(User.email == form_data.username).first()
    # if not user or not verify_password(form_data.password, user.hashed_password):
    #     raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
