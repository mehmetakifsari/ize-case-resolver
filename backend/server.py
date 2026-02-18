from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
import time

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
from database import client, db

# Import routes
from routes.auth import router as auth_router
from routes.cases import router as cases_router
from routes.admin import router as admin_router
from routes.warranty import router as warranty_router
from routes.site_settings import router as site_settings_router
from routes.payments import router as payments_router
from routes.webhooks import router as webhooks_router
from routes.settings import router as settings_router

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
app.include_router(payments_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

async def write_system_log(entry: dict):
    """Sistem loglarını MongoDB'ye yazar."""
    try:
        await db.system_logs.insert_one(entry)
    except Exception as log_error:
        logger.error("Sistem logu yazılamadı: %s", log_error)


def detect_security_indicators(request: Request) -> list[str]:
    """Basit güvenlik sinyallerini yakala."""
    indicators = []
    full_target = f"{request.url.path}?{request.url.query}".lower()
    user_agent = (request.headers.get("user-agent") or "").lower()

    patterns = {
        "sql_injection": [" union ", "select ", "drop table", " or 1=1", "--"],
        "xss_attempt": ["<script", "javascript:", "onerror=", "onload="],
        "path_traversal": ["../", "..%2f", "%2e%2e%2f"],
        "suspicious_user_agent": ["sqlmap", "nmap", "nikto", "acunetix", "masscan"],
    }

    for indicator, checks in patterns.items():
        if any(check in full_target for check in checks):
            indicators.append(indicator)

    if any(check in user_agent for check in patterns["suspicious_user_agent"]):
        indicators.append("suspicious_user_agent")

    return sorted(set(indicators))


@app.middleware("http")
async def request_monitoring_middleware(request: Request, call_next):
    start = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    security_indicators = detect_security_indicators(request)

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        await write_system_log(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR",
                "event_type": "unhandled_exception",
                "path": request.url.path,
                "method": request.method,
                "query": request.url.query,
                "status_code": 500,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent"),
                "message": str(exc),
                "security_indicators": security_indicators,
            }
        )
        logger.exception("Beklenmeyen API hatası: %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Sunucu hatası"})

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    status_code = response.status_code
    event_type = "request"
    level = "INFO"

    if status_code >= 500:
        level = "ERROR"
        event_type = "server_error"
    elif status_code in (401, 403):
        level = "WARNING"
        event_type = "auth_failure"
    elif status_code >= 400:
        level = "WARNING"
        event_type = "client_error"

    if security_indicators:
        level = "WARNING"
        event_type = "security_alert"

    should_store = status_code >= 400 or bool(security_indicators)
    if should_store:
        await write_system_log(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "event_type": event_type,
                "path": request.url.path,
                "method": request.method,
                "query": request.url.query,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent"),
                "security_indicators": security_indicators,
            }
        )

    return response



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
