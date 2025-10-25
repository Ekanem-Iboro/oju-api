from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class DonationBase(BaseModel):
    donor_name: str
    donor_email: EmailStr
    amount: float
    currency: str = "USD"

class DonationCreate(DonationBase):
    pass

class DonationUpdate(BaseModel):
    status: str
    payment_id: Optional[str] = None

class Donation(DonationBase):
    id: int
    status: str
    payment_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class DonationInDB(Donation):
    pass
