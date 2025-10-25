# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .member import Member
from .testimonial import Testimonial
from .donation import Donation
from .program import Program
from .event import Event
from .hero_slide import HeroSlide

__all__ = [
    "User",
    "Member", 
    "Testimonial",
    "Donation",
    "Program",
    "Event",
    "HeroSlide"
]
