from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

# Import database session dependency
from app.api.deps import get_db, get_current_user, get_admin_user
# Import models
from app.models.testimonial import Testimonial, TestimonialStatus
from app.models.user import User
# Import schemas for request/response validation
from app.schemas.testimonial import TestimonialCreate, TestimonialUpdate, TestimonialInDB

# Create router instance for testimonial endpoints
router = APIRouter(
  
)

@router.get("/", response_model=List[TestimonialInDB])
async def get_testimonials(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[TestimonialStatus] = Query(None, description="Filter by testimonial status"),
    featured_only: bool = Query(False, description="Show only featured testimonials"),
    category: Optional[str] = Query(None, description="Filter by testimonial category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)

):
    """
    Retrieve a list of testimonials with optional filtering and pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        status: Optional filter by testimonial status
        featured_only: Show only featured testimonials
        category: Optional filter by testimonial category
        db: Database session
        
    Returns:
        List of testimonial records matching the criteria
    """
    # Start building the query
    query = db.query(Testimonial)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Testimonial.status == status)
    
    # Apply featured filter if requested
    if featured_only:
        query = query.filter(Testimonial.is_featured == True)
    
    # Apply category filter if provided
    if category:
        query = query.filter(Testimonial.category == category)
    
    # Apply pagination and execute query
    testimonials = query.offset(skip).limit(limit).all()
    return testimonials

@router.get("/{testimonial_id}", response_model=TestimonialInDB)
async def get_testimonial(
    testimonial_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)

):
    """
    Retrieve a specific testimonial by its ID.
    
    Args:
        testimonial_id: Unique identifier of the testimonial
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Testimonial record if found
        
    Raises:
        HTTPException: 404 if testimonial not found
    """
    # Query for the specific testimonial
    testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
    
    # Check if testimonial exists
    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found"
        )
    
    return testimonial

@router.post("/", response_model=TestimonialInDB)
async def create_testimonial(
    testimonial: TestimonialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new testimonial record.
    
    Args:
        testimonial: Testimonial data to create
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Created testimonial record
    """
    # Create new testimonial instance
    db_testimonial = Testimonial(**testimonial.dict())
    
    # Add to database
    db.add(db_testimonial)
    db.commit()
    db.refresh(db_testimonial)
    
    return db_testimonial

@router.put("/{testimonial_id}", response_model=TestimonialInDB)
async def update_testimonial(
    testimonial_id: str,
    testimonial_update: TestimonialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing testimonial record.
    
    Args:
        testimonial_id: Unique identifier of the testimonial to update
        testimonial_update: Updated testimonial data
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Updated testimonial record
        
    Raises:
        HTTPException: 404 if testimonial not found
    """
    # Find the testimonial to update
    testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
    
    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found"
        )
    
    # Update only the fields that were provided
    update_data = testimonial_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(testimonial, field, value)
    
    # Save changes
    db.commit()
    db.refresh(testimonial)
    
    return testimonial

@router.put("/{testimonial_id}/approve")
async def approve_testimonial(
    testimonial_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Approve a testimonial (admin only).
    
    Args:
        testimonial_id: Unique identifier of the testimonial to approve
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if testimonial not found
    """
    # Find the testimonial to approve
    testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
    
    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found"
        )
    
    # Update testimonial status and approval details
    testimonial.status = TestimonialStatus.APPROVED
    testimonial.approved_by = current_user.id
    testimonial.approval_date = datetime.utcnow()
    
    # Save changes
    db.commit()
    
    return {"message": "Testimonial approved successfully"}

@router.put("/{testimonial_id}/reject")
async def reject_testimonial(
    testimonial_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Reject a testimonial (admin only).
    
    Args:
        testimonial_id: Unique identifier of the testimonial to reject
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if testimonial not found
    """
    # Find the testimonial to reject
    testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
    
    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found"
        )
    
    # Update testimonial status
    testimonial.status = TestimonialStatus.REJECTED
    
    # Save changes
    db.commit()
    
    return {"message": "Testimonial rejected"}

@router.get("/pending/list", response_model=List[TestimonialInDB])
async def get_pending_testimonials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get all pending testimonials (admin only).
    
    Args:
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        List of pending testimonials
    """
    # Query for pending testimonials
    testimonials = db.query(Testimonial).filter(
        Testimonial.status == TestimonialStatus.PENDING
    ).all()
    
    return testimonials

@router.put("/{testimonial_id}/feature")
async def toggle_feature_testimonial(
    testimonial_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Toggle featured status of a testimonial (admin only).
    
    Args:
        testimonial_id: Unique identifier of the testimonial
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Success message with current featured status
        
    Raises:
        HTTPException: 404 if testimonial not found
    """
    # Find the testimonial
    testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
    
    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found"
        )
    
    # Toggle featured status
    testimonial.is_featured = not testimonial.is_featured
    
    # Save changes
    db.commit()
    
    action = "featured" if testimonial.is_featured else "unfeatured"
    return {"message": f"Testimonial {action} successfully"}

@router.delete("/{testimonial_id}")
async def delete_testimonial(
    testimonial_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a testimonial (admin only).
    
    Args:
        testimonial_id: Unique identifier of the testimonial to delete
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if testimonial not found
    """
    # Find the testimonial to delete
    testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
    
    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found"
        )
    
    # Delete the testimonial
    db.delete(testimonial)
    db.commit()
    
    return {"message": "Testimonial deleted successfully"} 