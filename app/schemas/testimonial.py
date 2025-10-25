from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TestimonialBase(BaseModel):
    name: str
    content: str
    rating: int
    image_url: Optional[str] = None

class TestimonialCreate(TestimonialBase):
    pass

class TestimonialUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    rating: Optional[int] = None
    image_url: Optional[str] = None

class Testimonial(TestimonialBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class TestimonialInDB(Testimonial):
    pass
