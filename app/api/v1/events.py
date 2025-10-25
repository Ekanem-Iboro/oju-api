from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

# Import database session dependency
from app.api.deps import get_db, get_current_user, get_admin_user
# Import models
from app.models.event import Event
from app.models.user import User
# Import schemas for request/response validation
from app.schemas.event import EventCreate, EventUpdate, EventInDB

# Create router instance for event endpoints
router = APIRouter(
 
)

@router.get("/", response_model=List[EventInDB])
async def get_events(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    upcoming_only: bool = Query(False, description="Show only upcoming events"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of events with optional filtering and pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        is_active: Optional filter by active status
        start_date: Optional filter events from this date
        end_date: Optional filter events until this date
        upcoming_only: Show only upcoming events
        db: Database session
        
    Returns:
        List of event records matching the criteria
    """
    # Start building the query
    query = db.query(Event)
    
    # Apply active status filter if provided
    if is_active is not None:
        query = query.filter(Event.is_active == is_active)
    
    # Apply date range filters if provided
    if start_date:
        query = query.filter(Event.event_date >= start_date)
    if end_date:
        query = query.filter(Event.event_date <= end_date)
    
    # Apply upcoming events filter if requested
    if upcoming_only:
        today = date.today()
        query = query.filter(Event.event_date >= today)
    
    # Order by event date (upcoming first)
    query = query.order_by(Event.event_date.asc())
    
    # Apply pagination and execute query
    events = query.offset(skip).limit(limit).all()
    return events

@router.get("/{event_id}", response_model=EventInDB)
async def get_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific event by its ID.
    
    Args:
        event_id: Unique identifier of the event
        db: Database session
        
    Returns:
        Event record if found
        
    Raises:
        HTTPException: 404 if event not found
    """
    # Query for the specific event
    event = db.query(Event).filter(Event.id == event_id).first()
    
    # Check if event exists
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return event

@router.post("/", response_model=EventInDB)
async def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Create a new event record (admin only).
    
    Args:
        event: Event data to create
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Created event record
    """
    # Create new event instance
    db_event = Event(**event.dict())
    
    # Add to database
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event

@router.put("/{event_id}", response_model=EventInDB)
async def update_event(
    event_id: str,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update an existing event record (admin only).
    
    Args:
        event_id: Unique identifier of the event to update
        event_update: Updated event data
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Updated event record
        
    Raises:
        HTTPException: 404 if event not found
    """
    # Find the event to update
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Update only the fields that were provided
    update_data = event_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    # Save changes
    db.commit()
    db.refresh(event)
    
    return event

@router.put("/{event_id}/toggle-status")
async def toggle_event_status(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Toggle the active status of an event (admin only).
    
    Args:
        event_id: Unique identifier of the event
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Success message with current status
        
    Raises:
        HTTPException: 404 if event not found
    """
    # Find the event
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Toggle active status
    event.is_active = not event.is_active
    
    # Save changes
    db.commit()
    
    status_text = "activated" if event.is_active else "deactivated"
    return {"message": f"Event {status_text} successfully"}

@router.get("/upcoming/list", response_model=List[EventInDB])
async def get_upcoming_events(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of upcoming events to return"),
    db: Session = Depends(get_db)
):
    """
    Get a list of upcoming events.
    
    Args:
        limit: Maximum number of upcoming events to return
        db: Database session
        
    Returns:
        List of upcoming events
    """
    # Get today's date
    today = date.today()
    
    # Query for upcoming events
    events = db.query(Event).filter(
        Event.event_date >= today,
        Event.is_active == True
    ).order_by(Event.event_date.asc()).limit(limit).all()
    
    return events

@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete an event record (admin only).
    
    Args:
        event_id: Unique identifier of the event to delete
        db: Database session
        current_user: Currently authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if event not found
    """
    # Find the event to delete
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Delete the event
    db.delete(event)
    db.commit()
    
    return {"message": "Event deleted successfully"} 