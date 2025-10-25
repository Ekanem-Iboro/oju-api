from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pytest import Session
from app.api.v1 import auth, users, members, testimonials, donations, programs, events, content,upload
from app.core.database import create_tables, get_db
from app.models import user, member, testimonial, donation, program, event, hero_slide

# Create ONE FastAPI instance with CORS
app = FastAPI(
    title="Oju Mountain API",
    description="API for Oju Mountain Web Application",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware to the same app instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    print("Database tables created successfully!")

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(members.router, prefix="/api/v1/members", tags=["Members"])
app.include_router(testimonials.router, prefix="/api/v1/testimonials", tags=["Testimonials"])
app.include_router(donations.router, prefix="/api/v1/donations", tags=["Donations"])
app.include_router(programs.router, prefix="/api/v1/programs", tags=["Programs"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])

@app.get("/")
async def root():
    return {"message": "Welcome to Oju Mountain API"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy"}
    except:
        return {"status": "database error"}