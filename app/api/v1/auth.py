from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional

from app.core.security import create_access_token
from app.core.config import settings
from app.api.deps import get_db
from app.services.auth_service import authenticate_user, create_user, get_user_by_email
from app.schemas.user import User

router = APIRouter()

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    userType: str = "member"
    is_active: bool = True
    is_superuser: bool = False

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=LoginResponse)  # Fixed response model
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user  # Return SQLAlchemy model directly
    }

@router.post("/register", response_model=User)
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    if get_user_by_email(db, email=user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = create_user(db, user_data)
    return user  # Return the SQLAlchemy model directly