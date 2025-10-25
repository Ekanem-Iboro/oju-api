from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

# Import database session dependency
from app.api.deps import get_db, get_current_user
# Import models
from app.models.member import Member
from app.models.user import User
# Import schemas for request/response validation
from app.schemas.member import MemberCreate, MemberUpdate, MemberInDB

# Create router instance for member endpoints
router = APIRouter(
   
)

@router.get("/", response_model=List[MemberInDB])
async def get_members(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for filtering members by name or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a list of members with optional filtering and pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        search: Optional search term to filter by name or email
        is_active: Optional filter by active status
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        List of member records matching the criteria
    """
    # Start building the query
    query = db.query(Member)
    
    # Apply search filter if provided
    if search:
        # Search in first name, last name, or email
        query = query.filter(
            (Member.first_name.ilike(f"%{search}%")) |
            (Member.last_name.ilike(f"%{search}%")) |
            (Member.email.ilike(f"%{search}%"))
        )
    
    # Apply active status filter if provided
    if is_active is not None:
        query = query.filter(Member.is_active == is_active)
    
    # Apply pagination and execute query
    members = query.offset(skip).limit(limit).all()
    return members

@router.get("/{member_id}", response_model=MemberInDB)
async def get_member(
    member_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific member by their ID.
    
    Args:
        member_id: Unique identifier of the member
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Member record if found
        
    Raises:
        HTTPException: 404 if member not found
    """
    # Query for the specific member
    member = db.query(Member).filter(Member.id == member_id).first()
    
    # Check if member exists
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    return member

@router.post("/", response_model=MemberInDB)
async def create_member(
    member: MemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new member record.
    
    Args:
        member: Member data to create
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Created member record
        
    Raises:
        HTTPException: 400 if email already exists
    """
    # Check if member with this email already exists
    existing_member = db.query(Member).filter(Member.email == member.email).first()
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Member with this email already exists"
        )
    
    # Create new member instance
    db_member = Member(**member.dict())
    
    # Add to database
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    return db_member

@router.put("/{member_id}", response_model=MemberInDB)
async def update_member(
    member_id: str,
    member_update: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing member record.
    
    Args:
        member_id: Unique identifier of the member to update
        member_update: Updated member data
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Updated member record
        
    Raises:
        HTTPException: 404 if member not found
    """
    # Find the member to update
    member = db.query(Member).filter(Member.id == member_id).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Update only the fields that were provided
    update_data = member_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)
    
    # Save changes
    db.commit()
    db.refresh(member)
    
    return member

@router.delete("/{member_id}")
async def delete_member(
    member_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a member record (soft delete by setting is_active to False).
    
    Args:
        member_id: Unique identifier of the member to delete
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if member not found
    """
    # Find the member to delete
    member = db.query(Member).filter(Member.id == member_id).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Soft delete by setting is_active to False
    member.is_active = False
    member.updated_at = datetime.utcnow()
    
    # Save changes
    db.commit()
    
    return {"message": "Member deleted successfully"} 