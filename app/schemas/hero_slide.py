from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HeroSlideBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    image_url: str
    is_active: bool = True
    order: int

class HeroSlideCreate(HeroSlideBase):
    pass

class HeroSlideUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

class HeroSlide(HeroSlideBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class HeroSlideInDB(HeroSlide):
    pass
