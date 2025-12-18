"""
Vercel Serverless Handler for FastAPI
"""

from mangum import Mangum
from app.main import app

# Create the serverless handler
handler = Mangum(app, lifespan="off")
