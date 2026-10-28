from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import models, schemas, auth
from database import get_db

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_pass = auth.get_password_hash(user_in.password)
    new_user = models.User(
        email=user_in.email, 
        hashed_password=hashed_pass,
        full_name=user_in.full_name or user_in.email.split('@')[0],
        virtual_balance=100000.0,
        is_guest=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    access_token = auth.create_access_token(
        data={"sub": user.email}, 
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    user_payload = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name or "Trader",
        "virtual_balance": user.virtual_balance,
        "is_guest": getattr(user, 'is_guest', False),
        "role": user.role.value if hasattr(user.role, 'value') else user.role
    }
    return {"access_token": access_token, "token_type": "bearer", "user": user_payload}

@router.post("/guest", response_model=schemas.Token)
def login_as_guest(db: Session = Depends(get_db)):
    """One-click instant guest login with preloaded $100,000 demo trading currency."""
    guest_email = "guest_trader@platform.demo"
    user = db.query(models.User).filter(models.User.email == guest_email).first()
    if not user:
        hashed_pass = auth.get_password_hash("guest_pass_demo_2026")
        user = models.User(
            email=guest_email,
            hashed_password=hashed_pass,
            full_name="Guest Trader",
            virtual_balance=100000.0,
            is_guest=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    user_payload = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "virtual_balance": user.virtual_balance,
        "is_guest": True,
        "role": user.role.value if hasattr(user.role, 'value') else user.role
    }
    return {"access_token": access_token, "token_type": "bearer", "user": user_payload}

@router.get("/me")
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name or "Trader",
        "virtual_balance": current_user.virtual_balance if hasattr(current_user, 'virtual_balance') else 100000.0,
        "is_guest": getattr(current_user, 'is_guest', False),
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "created_at": current_user.created_at.strftime("%Y-%m-%d") if hasattr(current_user, 'created_at') and current_user.created_at else "N/A"
    }
