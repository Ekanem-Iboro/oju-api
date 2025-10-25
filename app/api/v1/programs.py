from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

# Import database session dependency
from app.api.deps import get_db, get_current_user
# Import models
from app.models.program import Program
from app.models.user import User
# Import schemas for request/response validation
from app.schemas.program import ProgramCreate, ProgramUpdate, ProgramInDB,DeleteProgramRequest

# Create router instance for program endpoints
router = APIRouter()



@router.get("/", response_model=List[ProgramInDB])
async def get_programs(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status (active, draft, inactive)"),
    program_type: Optional[str] = Query(None, description="Filter by program type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of programs with optional filtering and pagination.

    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        status: Optional filter by program status
        program_type: Optional filter by program type
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of program records matching the criteria
    """
    # Start building the query
    query = db.query(Program)
    
    # Apply status filter if provided
    if status is not None:
        query = query.filter(Program.status == status)
    
    # Apply program type filter if provided
    if program_type:
        query = query.filter(Program.program_type == program_type)
    
    # Apply pagination and execute query
    programs = query.offset(skip).limit(limit).all()
    return programs


@router.get("/{program_id}", response_model=ProgramInDB)
async def get_program(
    program_id: int,  # Changed to int
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific program by its ID.

    Args:
        program_id: Unique identifier of the program
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Program record if found
    """
    program = db.query(Program).filter(Program.id == program_id).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )
    
    return program


@router.post("/", response_model=ProgramInDB)
async def create_program(
    program_data: ProgramCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new program record.
    
    Args:
        program_data: Program data from request body
        db: Database session
        current_user: Currently authenticated user
    
    Returns:
        Created program record
    """
    try:
        # Create program data
        program_dict = program_data.dict()
        
        # Create new program instance
        db_program = Program(**program_dict)
        
        # Add to database
        db.add(db_program)
        db.commit()
        db.refresh(db_program)
        
        return db_program
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating program: {str(e)}"
        )


@router.put("/{program_id}", response_model=ProgramInDB)
async def update_program(
    program_id: int,  # Changed to int
    program_data: ProgramUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing program record.
    
    Args:
        program_id: ID of the program to update
        program_data: Updated program data
        db: Database session
        current_user: Currently authenticated user
    
    Returns:
        Updated program record
    """
    try:
        # Find the program to update
        program = db.query(Program).filter(Program.id == program_id).first()
        
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        # Update fields if provided
        update_data = program_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(program, field, value)
        
        # Save changes
        db.commit()
        db.refresh(program)
        
        return program
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating program: {str(e)}"
        )




@router.delete("/{program_id}")
async def delete_program(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a program record using path parameter.
    
    URL: DELETE /api/v1/programs/1
    """
    try:
        program = db.query(Program).filter(Program.id == program_id).first()
        
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        db.delete(program)
        db.commit()
        
        return {
            "message": "Program deleted successfully",
            "deleted_id": program_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting program: {str(e)}"
        )