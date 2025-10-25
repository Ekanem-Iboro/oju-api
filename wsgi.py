import os
import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import and expose the FastAPI app
from app.main import app

# For Gunicorn
if __name__ == "__main__":
    app.run()