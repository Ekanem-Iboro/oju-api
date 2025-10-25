from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash
from app.models.user import User

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email=email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user_data):
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        userType=user_data.userType,  # Change to userType to match model
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user