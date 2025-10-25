from app.schemas.program import ImageUploadResponse
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from datetime import datetime
import shutil
from pathlib import Path
import os

router = APIRouter()

# Configuration for image storage
IMAGE_STORAGE_PATH = Path("static/images/programs")
IMAGE_BASE_URL = "/static/images/programs"

# Ensure storage directory exists
IMAGE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


@router.post("/", response_model=ImageUploadResponse)  # Added /upload endpoint
async def upload_program_image(
    image: UploadFile = File(...),
    # current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image for programs and return the image URL.
    
    Args:
        image: Image file to upload
        current_user: Currently authenticated user
        db: Database session
    
    Returns:
        Image URL and filename
    """
    # Validate file type
    allowed_content_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if image.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Only JPEG, PNG, GIF, and WebP are allowed."
        )
    
    # Validate file size (5MB limit)
    max_size = 5 * 1024 * 1024  # 5MB
    content = await image.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size too large. Maximum size is 5MB."
        )
    
    # Reset file pointer
    await image.seek(0)
    
    # Generate unique filename
    file_extension = Path(image.filename).suffix.lower()
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    unique_filename = f"program_{timestamp}{file_extension}"
    file_path = IMAGE_STORAGE_PATH / unique_filename
    
    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving image: {str(e)}"
        )
    
    # Generate URL for database - use absolute URL for frontend
    image_url = f"{IMAGE_BASE_URL}/{unique_filename}"
    
    return ImageUploadResponse(
        image_url=image_url,
        filename=unique_filename
    )


@router.delete("/{filename}")
async def delete_program_image(
    filename: str,
    # current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an uploaded program image by filename.
    
    Args:
        filename: Name of the file to delete (e.g., "program_20240115_120530_123456.jpg")
        current_user: Currently authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    # Validate filename format to prevent directory traversal attacks
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename format"
        )
    
    # Ensure filename starts with 'program_' to prevent deleting unrelated files
    if not filename.startswith("program_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )
    
    # Construct full file path
    file_path = IMAGE_STORAGE_PATH / filename
    
    # Check if file exists
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found"
        )
    
    # Check if it's actually a file (not a directory)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )
    
    # Delete the file
    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting image: {str(e)}"
        )
    
    return {
        "message": "Image deleted successfully",
        "filename": filename
    }