from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"

class ActionEnum(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class PredictionResponse(BaseModel):
    id: int
    stock_id: int
    predicted_date: datetime
    predicted_price: float
    recommendation: ActionEnum
    confidence_score: float
    class Config:
        from_attributes = True

class StockData(BaseModel):
    id: int
    ticker: str
    company_name: str
    predictions: List[PredictionResponse] = []
    class Config:
        from_attributes = True
