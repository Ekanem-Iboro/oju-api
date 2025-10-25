from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProgramBase(BaseModel):
    title: str
    description: str
    categories: str
    program_type: str
    status: str = "active"

class ProgramCreate(ProgramBase):
    image_url: Optional[str] = None

class ProgramUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[str] = None
    program_type: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None

class Program(ProgramBase):
    id: int
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProgramInDB(Program):
    pass

class ImageUploadResponse(BaseModel):
    image_url: str
    filename: str

class DeleteProgramRequest(BaseModel):
    programId: int  # Direct integer, no nesting
