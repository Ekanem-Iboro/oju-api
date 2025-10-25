from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

# Import database session dependency
from app.api.deps import get_db, get_current_user, get_admin_user
# Import models
from app.models.hero_slide import HeroSlide
from app.models.user import User
# Import schemas for request/response validation
from app.schemas.hero_slide import HeroSlideCreate, HeroSlideUpdate, HeroSlideInDB

# Create router instance for content endpoints
router = APIRouter()

@router.get("/hero-slides", response_model=List[HeroSlideInDB])
async def get_hero_slides(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of hero slides with optional filtering and pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        is_active: Optional filter by active status
        db: Database session
        
    Returns:
        List of hero slide records matching the criteria
    """
    # Start building the query
    query = db.query(HeroSlide)
    
    # Apply active status filter if provided
    if is_active is not None:
        query = query.filter(HeroSlide.is_active == is_active)
    
    # Order by display order
    query = query.order_by(HeroSlide.display_order.asc())
    
    # Apply pagination and execute query
    hero_slides = query.offset(skip).limit(limit).all