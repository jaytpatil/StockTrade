from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum
from typing import List

class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str = None
    virtual_balance: float = 100000.0
    is_guest: bool = False
    role: RoleEnum
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict = None

class TokenData(BaseModel):
    email: str = None

class TradeOrder(BaseModel):
    symbol: str
    shares: float

class DepositRequest(BaseModel):
    amount: float
