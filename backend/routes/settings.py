"""
Ayarlar API Route'ları (Ödeme Sağlayıcıları, Fatura, Sosyal Medya)
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, timezone
import logging

from models.invoice import (
    InvoiceSettings, PaymentProviderSettings, SocialMediaLinks,
    InvoiceSettingsUpdate, PaymentProviderSettingsUpdate, CompanyInfo
)
from routes.auth import get_admin_user
from database import db

router = APIRouter(prefix="/settings", tags=["Settings"])
logger = logging.getLogger(__name__)


# ==================== ÖDEME SAĞLAYICI AYARLARI ====================

@router.get("/payment-providers")
async def get_payment_provider_settings(admin: dict = Depends(get_admin_user)):
    """Ödeme sağlayıcı ayarlarını getir (Admin)"""
    settings = await db.payment_provider_settings.find_one({"id": "payment_provider_settings"}, {"_id": 0})
    
    if not settings:
        default = PaymentProviderSettings()
        return default.model_dump()
    
    # API anahtarlarını maskele
    masked = dict(settings)
    sensitive_fields = [
        'stripe_test_secret_key', 'stripe_live_secret_key', 'stripe_webhook_secret',
        'iyzico_sandbox_secret_key', 'iyzico_production_secret_key'
    ]
    
    for field in sensitive_fields:
        if masked.get(field):
            masked[field] = masked[field][:8] + '****' + masked[field][-4:] if len(masked[field]) > 12 else '****'
    
    return masked


@router.put("/payment-providers")
async def update_payment_provider_settings(
    update: PaymentProviderSettingsUpdate,
    admin: dict = Depends(get_admin_user)
):
    """Ödeme sağlayıcı ayarlarını güncelle (Admin)"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.payment_provider_settings.update_one(
        {"id": "payment_provider_settings"},
        {"$set": update_data},
        upsert=True
    )
    
    logger.info(f"Payment provider settings updated by {admin['email']}")
    return {"message": "Ödeme sağlayıcı ayarları güncellendi"}


# ==================== FATURA AYARLARI ====================

@router.get("/invoice")
async def get_invoice_settings(admin: dict = Depends(get_admin_user)):
    """Fatura ayarlarını getir (Admin)"""
    settings = await db.invoice_settings.find_one({"id": "invoice_settings"}, {"_id": 0})
    
    if not settings:
        default = InvoiceSettings()
        return default.model_dump()
    
    # API anahtarlarını maskele
    masked = dict(settings)
    sensitive_fields = [
        'parasut_client_secret', 'bizimhesap_secret_key', 'birfatura_password'
    ]
    
    for field in sensitive_fields:
        if masked.get(field):
            masked[field] = '****' + masked[field][-4:] if len(str(masked[field])) > 4 else '****'
    
    return masked


@router.put("/invoice")
async def update_invoice_settings(
    update: InvoiceSettingsUpdate,
    admin: dict = Depends(get_admin_user)
):
    """Fatura ayarlarını güncelle (Admin)"""
    update_data = {}
    
    for k, v in update.model_dump().items():
        if v is not None:
            if k == 'company' and isinstance(v, dict):
                for ck, cv in v.items():
                    if cv is not None:
                        update_data[f'company.{ck}'] = cv
            else:
                update_data[k] = v
    
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.invoice_settings.update_one(
        {"id": "invoice_settings"},
        {"$set": update_data},
        upsert=True
    )
    
    logger.info(f"Invoice settings updated by {admin['email']}")
    return {"message": "Fatura ayarları güncellendi"}


# ==================== SOSYAL MEDYA AYARLARI ====================

@router.get("/social-media")
async def get_social_media_settings():
    """Sosyal medya linklerini getir (Public)"""
    settings = await db.site_settings.find_one({}, {"_id": 0})
    
    if settings and settings.get('social_media'):
        return settings['social_media']
    
    return SocialMediaLinks().model_dump()


@router.put("/social-media")
async def update_social_media_settings(
    links: SocialMediaLinks,
    admin: dict = Depends(get_admin_user)
):
    """Sosyal medya linklerini güncelle (Admin)"""
    await db.site_settings.update_one(
        {},
        {"$set": {"social_media": links.model_dump()}},
        upsert=True
    )
    
    logger.info(f"Social media settings updated by {admin['email']}")
    return {"message": "Sosyal medya ayarları güncellendi"}


# ==================== FATURALAR ====================

@router.get("/invoices")
async def get_all_invoices(
    status: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """Tüm faturaları getir (Admin)"""
    query = {}
    if status:
        query['status'] = status
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return invoices


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, admin: dict = Depends(get_admin_user)):
    """Fatura detayı getir (Admin)"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura bulunamadı")
    
    return invoice


@router.post("/invoices/generate/{transaction_id}")
async def generate_invoice_for_transaction(
    transaction_id: str,
    customer_name: Optional[str] = None,
    customer_address: Optional[str] = None,
    customer_tax_office: Optional[str] = None,
    customer_tax_number: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """Transaction için fatura oluştur (Admin)"""
    from services.invoice_service import InvoiceService, get_invoice_settings
    
    # Transaction'ı bul
    transaction = await db.payment_transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not transaction:
        raise HTTPException(status_code=404, detail="İşlem bulunamadı")
    
    # Zaten fatura var mı kontrol et
    existing = await db.invoices.find_one({"transaction_id": transaction_id})
    if existing:
        raise HTTPException(status_code=400, detail="Bu işlem için zaten fatura oluşturulmuş")
    
    # Kullanıcıyı bul
    user = await db.users.find_one({"id": transaction['user_id']}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    # Fatura ayarlarını al
    settings = await get_invoice_settings(db)
    
    # Fatura oluştur
    service = InvoiceService(settings)
    invoice = await service.create_invoice(
        transaction=transaction,
        user=user,
        db=db,
        customer_name=customer_name or user.get('full_name'),
        customer_address=customer_address,
        customer_tax_office=customer_tax_office,
        customer_tax_number=customer_tax_number
    )
    
    return {"message": "Fatura oluşturuldu", "invoice_number": invoice.invoice_number}


# ==================== PUBLIC ENDPOINTS (Auth Gerektirmez) ====================

@router.get("/public/pricing-plans")
async def get_public_pricing_plans():
    """Fiyatlandırma planlarını getir (Public - herkes erişebilir)"""
    plans = await db.pricing_plans.find({"is_active": True}, {"_id": 0}).sort("price", 1).to_list(100)
    
    # Varsayılan planları döndür
    if not plans:
        return [
            {"id": "free", "name": "Ücretsiz", "credits": 5, "price": 0, "currency": "TRY", "is_popular": False, "features": ["5 Ücretsiz Analiz", "E-posta Desteği"], "plan_type": "package"},
            {"id": "starter", "name": "Başlangıç", "credits": 10, "price": 100, "currency": "TRY", "is_popular": False, "features": ["10 IZE Analizi", "E-posta Desteği"], "plan_type": "package"},
            {"id": "pro", "name": "Pro", "credits": 50, "price": 400, "currency": "TRY", "is_popular": True, "features": ["50 IZE Analizi", "Öncelikli Destek", "Detaylı Raporlar"], "plan_type": "package"},
            {"id": "enterprise", "name": "Enterprise", "credits": 200, "price": 1200, "currency": "TRY", "is_popular": False, "features": ["200 IZE Analizi", "7/24 Destek", "Özel Entegrasyon", "API Erişimi"], "plan_type": "package"},
        ]
    
    return plans


@router.get("/public/branches")
async def get_public_branches():
    """Aktif şubeleri getir (Public - kayıt için)"""
    branches = await db.branches.find({"is_active": True}, {"_id": 0, "name": 1}).sort("name", 1).to_list(100)
    
    if not branches:
        from models.user import DEFAULT_BRANCHES
        return [{"name": name} for name in DEFAULT_BRANCHES]
    
    return branches

