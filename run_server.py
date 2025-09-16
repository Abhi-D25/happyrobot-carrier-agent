#!/usr/bin/env python3
"""
Simple script to run the FastAPI server with environment variables.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv()

# Load environment variables

# Set environment variables (only if not already set)
os.environ.setdefault("API_KEY", "secure-api-key-change-in-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///./carrier_agent.db")
os.environ.setdefault("FMCSA_API_KEY", "your-fmcsa-api-key-here")
os.environ.setdefault("FMCSA_BASE_URL", "https://mobile.fmcsa.dot.gov/qc/services/carriers")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000,https://app.happyrobot.ai")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )