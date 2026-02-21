from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel
from models.site_settings import SiteSettings, SiteSettingsUpdate
from routes.auth import get_admin_user
from services.email import send_contact_form_email
from database import db

router = APIRouter(prefix="/site-settings", tags=["Site Settings"])

class ContactFormMessage(BaseModel):
    name: str
    email: str
    subject: str
    message: str



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
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    
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
    
    # Exclude _id if present before updating
    if '_id' in settings:
        del settings['_id']
    
    await db.site_settings.update_one(
        {"id": "site_settings"},
        {"$set": settings},
        upsert=True
    )
    
    return {"message": "Site ayarları güncellendi", "settings": settings}



@router.post("/contact-message")
async def send_contact_message(payload: ContactFormMessage):
    """İletişim formundan gelen mesajı şirket e-posta adresine ilet."""
    settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0}) or {}
    recipient_email = settings.get("contact_form_recipient_email") or settings.get("contact_email")

    if not recipient_email:
        raise HTTPException(status_code=400, detail="İletişim alıcı e-posta adresi tanımlı değil")

    if not payload.name.strip() or not payload.email.strip() or not payload.subject.strip() or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Tüm iletişim formu alanları zorunludur")

    result = await send_contact_form_email(
        recipient_email=recipient_email,
        sender_name=payload.name,
        sender_email=str(payload.email),
        subject=payload.subject,
        message=payload.message,
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message", "Mesaj gönderilemedi"))

    return {"message": "Mesajınız iletildi"}
