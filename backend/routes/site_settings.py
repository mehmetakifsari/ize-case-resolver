from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from models.site_settings import SiteSettings, SiteSettingsUpdate
from routes.auth import get_admin_user
from database import db

router = APIRouter(prefix="/site-settings", tags=["Site Settings"])


@router.get("")
async def get_site_settings():
    """Site ayarlarını getir (Public)"""
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    
    if not settings:
        # Varsayılan ayarları döndür
        default = SiteSettings()
        return default.model_dump()
    
    return settings


@router.put("")
async def update_site_settings(settings_update: SiteSettingsUpdate, admin: dict = Depends(get_admin_user)):
    """Site ayarlarını güncelle (Sadece admin)"""
    settings = await db.site_settings.find_one({"id": "site_settings"})
    
    if not settings:
        # Varsayılan ayarlarla başla
        default = SiteSettings()
        settings = default.model_dump()
        settings['created_at'] = datetime.now(timezone.utc).isoformat()
    
    # Güncelle
    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            settings[key] = value
    
    settings['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.site_settings.update_one(
        {"id": "site_settings"},
        {"$set": settings},
        upsert=True
    )
    
    return {"message": "Site ayarları güncellendi", "settings": settings}
