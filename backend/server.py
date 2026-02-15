from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import database
from database import client

# Import routes
from routes.auth import router as auth_router
from routes.cases import router as cases_router
from routes.admin import router as admin_router
from routes.warranty import router as warranty_router
from routes.site_settings import router as site_settings_router
from routes.payments import router as payments_router
from routes.webhooks import router as webhooks_router

# Create the main app
app = FastAPI(
    title="IZE Case Resolver API",
    description="Renault Trucks garanti IZE dosyaları analiz sistemi",
    version="2.0"
)

# Include routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(warranty_router, prefix="/api")
app.include_router(site_settings_router, prefix="/api")


@app.get("/api/")
async def root():
    return {"message": "IZE Case Resolver API", "version": "2.0"}


@app.get("/api/branches")
async def get_branches():
    """Kullanılabilir şubeleri döndürür"""
    from models.user import BRANCHES
    return {"branches": BRANCHES}


# CORS middleware - must be added after routers
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
