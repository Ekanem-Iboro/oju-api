from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

# Import database session dependency
from app.api.deps import get_db, get_current_user, get_admin_user
# Import models
from app.models.donation import Donation, DonationType, PaymentStatus
from app.models.user import User
# Import schemas for request/response validation
from app.schemas.donation import DonationCreate, DonationUpdate, DonationInDB

# Create router instance for donation endpoints
router = APIRouter(
   
)

@router.get("/", response_model=List[DonationInDB])
async def get_donations(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    donation_type: Optional[DonationType] = Query(None, description="Filter by donation type"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    start_date: Optional[date] = Query(None, description="Filter donations from this date"),
    end_date: Optional[date] = Query(None, description="Filter donations until this date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a list of donations with optional filtering and pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        donation_type: Optional filter by donation type
        payment_status: Optional filter by payment status
        start_date: Optional filter donations from this date
        end_date: Optional filter donations until this date
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        List of donation records matching the criteria
    """
    # Start building the query
    query = db.query(Donation)
    
    # Apply donation type filter if provided
    if donation_type:
        query = query.filter(Donation.donation_type == donation_type)
    
    # Apply payment status filter if provided
    if payment_status:
        query = query.filter(Donation.payment_status == payment_status)
    
    # Apply date range filters if provided
    if start_date:
        query = query.filter(Donation.transaction_date >= start_date)
    if end_date:
        query = query.filter(Donation.transaction_date <= end_date)
    
    # Apply pagination and execute query
    donations = query.offset(skip).limit(limit).all()
    return donations

@router.get("/{donation_id}", response_model=DonationInDB)
async def get_donation(
    donation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific donation by its ID.
    
    Args:
        donation_id: Unique identifier of the donation
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Donation record if found
        
    Raises:
        HTTPException: 404 if donation not found
    """
    # Query for the specific donation
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    
    # Check if donation exists
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found"
        )
    
    return donation

@router.post("/", response_model=DonationInDB)
async def create_donation(
    donation: DonationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new donation record.
    
    Args:
        donation: Donation data to create
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Created donation record
    """
    # Create new donation instance
    db_donation = Donation(**donation.dict())
    
    # Add to database
    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)
    
    return db_donation

@router.put("/{donation_id}", response_model=DonationInDB)
async def update_donation(
    donation_id: str,
    donation_update: DonationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update an existing donation record (admin only).
    
    Args:
        donation_id: Unique identifier of the donation to update
        donation_update: Updated donation data
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Updated donation record
        
    Raises:
        HTTPException: 404 if donation not found
    """
    # Find the donation to update
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found"
        )
    
    # Update only the fields that were provided
    update_data = donation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(donation, field, value)
    
    # Save changes
    db.commit()
    db.refresh(donation)
    
    return donation

@router.put("/{donation_id}/status")
async def update_donation_status(
    donation_id: str,
    payment_status: PaymentStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update the payment status of a donation (admin only).
    
    Args:
        donation_id: Unique identifier of the donation
        payment_status: New payment status
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if donation not found
    """
    # Find the donation
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found"
        )
    
    # Update payment status
    donation.payment_status = payment_status
    
    # Save changes
    db.commit()
    
    return {"message": f"Donation status updated to {payment_status.value}"}

@router.get("/stats/summary")
async def get_donation_stats(
    start_date: Optional[date] = Query(None, description="Start date for statistics"),
    end_date: Optional[date] = Query(None, description="End date for statistics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get donation statistics summary (admin only).
    
    Args:
        start_date: Optional start date for statistics
        end_date: Optional end date for statistics
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Dictionary containing donation statistics
    """
    # Start building the query
    query = db.query(Donation)
    
    # Apply date range filters if provided
    if start_date:
        query = query.filter(Donation.transaction_date >= start_date)
    if end_date:
        query = query.filter(Donation.transaction_date <= end_date)
    
    # Get all donations in the date range
    donations = query.all()
    
    # Calculate statistics
    total_donations = len(donations)
    total_amount = sum(float(d.amount) for d in donations)
    completed_donations = len([d for d in donations if d.payment_status == PaymentStatus.COMPLETED])
    pending_donations = len([d for d in donations if d.payment_status == PaymentStatus.PENDING])
    
    # Calculate average donation amount
    avg_donation = total_amount / total_donations if total_donations > 0 else 0
    
    return {
        "total_donations": total_donations,
        "total_amount": total_amount,
        "average_donation": round(avg_donation, 2),
        "completed_donations": completed_donations,
        "pending_donations": pending_donations,
        "completion_rate": round((completed_donations / total_donations * 100), 2) if total_donations > 0 else 0
    }

@router.delete("/{donation_id}")
async def delete_donation(
    donation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a donation record (admin only).
    
    Args:
        donation_id: Unique identifier of the donation to delete
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if donation not found
    """
    # Find the donation to delete
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found"
        )
    
    # Delete the donation
    db.delete(donation)
    db.commit()
    
    return {"message": "Donation deleted successfully"} 