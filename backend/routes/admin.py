from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from datetime import datetime, timezone
import os
import uuid
import shutil
from pathlib import Path
from models.user import (
    User, UserInDB, UserCreate, UserUpdate, DEFAULT_BRANCHES,
    Branch, BranchCreate, PricingPlan, PricingPlanCreate, PricingPlanUpdate
)
from models.settings import APISettings, APISettingsUpdate, EmailSettings, EmailSettingsUpdate
from services.auth import get_password_hash
from services.email import test_smtp_connection
from routes.auth import get_admin_user
from database import db

# Upload dizini - frontend/public/uploads
UPLOAD_DIR = Path(__file__).parent.parent.parent / "frontend" / "public" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== ANALYTICS ====================

@router.get("/analytics")
async def get_analytics(admin: dict = Depends(get_admin_user)):
    """Admin analytics dashboard verileri"""
    # Toplam kullanıcı sayısı
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    
    # Toplam case sayısı
    total_cases = await db.ize_cases.count_documents({})
    archived_cases = await db.ize_cases.count_documents({"is_archived": True})
    
    # Şubeleri veritabanından al
    branches = await db.branches.find({"is_active": True}, {"_id": 0}).to_list(100)
    branch_names = [b["name"] for b in branches] if branches else DEFAULT_BRANCHES
    
    # Şubelere göre case dağılımı
    branch_stats = {}
    for branch in branch_names:
        count = await db.ize_cases.count_documents({"branch": branch})
        branch_stats[branch] = count
    
    # Garanti kararlarına göre dağılım
    decision_stats = {
        "COVERED": await db.ize_cases.count_documents({"warranty_decision": "COVERED"}),
        "OUT_OF_COVERAGE": await db.ize_cases.count_documents({"warranty_decision": "OUT_OF_COVERAGE"}),
        "ADDITIONAL_INFO_REQUIRED": await db.ize_cases.count_documents({"warranty_decision": "ADDITIONAL_INFO_REQUIRED"})
    }
    
    # Son 7 gündeki analizler
    from datetime import timedelta
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_cases = await db.ize_cases.count_documents({"created_at": {"$gte": week_ago}})
    
    # Toplam analiz sayısı (tüm kullanıcıların total_analyses toplamı)
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$total_analyses"}}}
    ]
    result = await db.users.aggregate(pipeline).to_list(1)
    total_analyses = result[0]["total"] if result else 0
    
    # Toplam gönderilen e-posta sayısı
    email_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$emails_sent"}}}
    ]
    email_result = await db.users.aggregate(email_pipeline).to_list(1)
    total_emails_sent = email_result[0]["total"] if email_result else 0
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users
        },
        "cases": {
            "total": total_cases,
            "archived": archived_cases,
            "active": total_cases - archived_cases,
            "recent_week": recent_cases
        },
        "branches": branch_stats,
        "decisions": decision_stats,
        "total_analyses": total_analyses,
        "total_emails_sent": total_emails_sent
    }


# ==================== USER MANAGEMENT ====================

@router.get("/users")
async def get_all_users(
    branch: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: dict = Depends(get_admin_user)
):
    """Tüm kullanıcıları listele (Sadece admin)"""
    query = {}
    
    if branch:
        query["branch"] = branch
    if role:
        query["role"] = role
    if is_active is not None:
        query["is_active"] = is_active
    
    users = await db.users.find(query, {"_id": 0, "hashed_password": 0}).sort("created_at", -1).to_list(1000)
    return users


@router.get("/users/{user_id}")
async def get_user_by_id(user_id: str, admin: dict = Depends(get_admin_user)):
    """Belirli bir kullanıcıyı getir (Sadece admin)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user


@router.post("/users")
async def create_user(user_data: UserCreate, admin: dict = Depends(get_admin_user)):
    """Yeni kullanıcı oluştur (Sadece admin)"""
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu email adresi zaten kayıtlı")
    
    hashed_password = get_password_hash(user_data.password)
    user = UserInDB(
        email=user_data.email,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        branch=user_data.branch,
        role=user_data.role,
        hashed_password=hashed_password
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Şifreyi çıkar
    response = {k: v for k, v in user_dict.items() if k != 'hashed_password'}
    return response


@router.put("/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate, admin: dict = Depends(get_admin_user)):
    """Kullanıcıyı güncelle (Sadece admin)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    return updated_user


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Kullanıcıyı sil (Sadece admin)"""
    if user_id == admin['id']:
        raise HTTPException(status_code=400, detail="Kendinizi silemezsiniz")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    return {"message": "Kullanıcı silindi", "id": user_id}


@router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: str, admin: dict = Depends(get_admin_user)):
    """Kullanıcıyı aktif/pasif yap (Sadece admin)"""
    if user_id == admin['id']:
        raise HTTPException(status_code=400, detail="Kendinizi pasif yapamazsınız")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    new_status = not user.get('is_active', True)
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": new_status}})
    
    return {"message": "Kullanıcı durumu güncellendi", "is_active": new_status}


@router.patch("/users/{user_id}/add-credit")
async def add_user_credit(user_id: str, amount: int = 5, admin: dict = Depends(get_admin_user)):
    """Kullanıcıya kredi ekle (Sadece admin)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"free_analyses_remaining": amount}}
    )
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    return {
        "message": f"{amount} kredi eklendi",
        "new_balance": updated_user.get('free_analyses_remaining', 0)
    }


# ==================== API SETTINGS ====================

def mask_api_key(key: str) -> str:
    """API key'i maskele (ilk 4 ve son 4 karakter göster)"""
    if not key or len(key) < 10:
        return "***"
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


@router.get("/settings")
async def get_api_settings(admin: dict = Depends(get_admin_user)):
    """API ayarlarını getir (Sadece admin) - Maskelenmiş"""
    settings = await db.api_settings.find_one({"id": "api_settings"}, {"_id": 0})
    
    if not settings:
        return {
            "id": "api_settings",
            "emergent_key": None,
            "emergent_key_masked": None,
            "openai_key": None,
            "openai_key_masked": None,
            "anthropic_key": None,
            "anthropic_key_masked": None,
            "google_key": None,
            "google_key_masked": None,
            "other_keys": {}
        }
    
    # Maskelenmiş versiyonları ekle
    response = {
        "id": settings.get("id", "api_settings"),
        "emergent_key": settings.get("emergent_key"),
        "emergent_key_masked": mask_api_key(settings.get("emergent_key") or ""),
        "openai_key": settings.get("openai_key"),
        "openai_key_masked": mask_api_key(settings.get("openai_key") or ""),
        "anthropic_key": settings.get("anthropic_key"),
        "anthropic_key_masked": mask_api_key(settings.get("anthropic_key") or ""),
        "google_key": settings.get("google_key"),
        "google_key_masked": mask_api_key(settings.get("google_key") or ""),
        "other_keys": settings.get("other_keys", {}),
        "updated_at": settings.get("updated_at")
    }
    
    return response


@router.put("/settings")
async def update_api_settings(settings_update: APISettingsUpdate, admin: dict = Depends(get_admin_user)):
    """API ayarlarını güncelle (Sadece admin)"""
    settings = await db.api_settings.find_one({"id": "api_settings"})
    
    if not settings:
        settings = {
            "id": "api_settings",
            "emergent_key": None,
            "openai_key": None,
            "anthropic_key": None,
            "google_key": None,
            "other_keys": {}
        }
    
    # Güncelle
    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            settings[key] = value
    
    settings['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.api_settings.update_one(
        {"id": "api_settings"},
        {"$set": settings},
        upsert=True
    )
    
    return {"message": "API ayarları güncellendi"}


# ==================== CASE MANAGEMENT ====================

@router.get("/cases")
async def get_all_cases_admin(
    branch: Optional[str] = None,
    archived: Optional[bool] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    admin: dict = Depends(get_admin_user)
):
    """Tüm case'leri listele (Sadece admin)"""
    query = {}
    
    if branch:
        query["branch"] = branch
    if archived is not None:
        query["is_archived"] = archived
    if year:
        query["year"] = year
    if month:
        query["month"] = month
    
    cases = await db.ize_cases.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for case in cases:
        if isinstance(case.get('created_at'), str):
            case['created_at'] = datetime.fromisoformat(case['created_at'])
    
    return cases


@router.delete("/cases/{case_id}")
async def admin_delete_case(case_id: str, admin: dict = Depends(get_admin_user)):
    """Case'i sil (Sadece admin)"""
    result = await db.ize_cases.delete_one({"id": case_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Case bulunamadı")
    return {"message": "Case silindi", "id": case_id}


@router.patch("/cases/{case_id}/archive")
async def admin_archive_case(case_id: str, admin: dict = Depends(get_admin_user)):
    """Case'i arşivle/arşivden çıkar (Sadece admin)"""
    case = await db.ize_cases.find_one({"id": case_id})
    
    if not case:
        raise HTTPException(status_code=404, detail="Case bulunamadı")
    
    new_status = not case.get('is_archived', False)
    archived_at = datetime.now(timezone.utc).isoformat() if new_status else None
    
    await db.ize_cases.update_one(
        {"id": case_id},
        {"$set": {"is_archived": new_status, "archived_at": archived_at}}
    )
    
    return {"message": "Case arşiv durumu güncellendi", "is_archived": new_status}



# ==================== EMAIL SETTINGS ====================

def mask_password(password: str) -> str:
    """Şifreyi maskele"""
    if not password or len(password) < 4:
        return "***"
    return f"{password[:2]}{'*' * (len(password) - 2)}"


@router.get("/email-settings")
async def get_email_settings(admin: dict = Depends(get_admin_user)):
    """E-posta ayarlarını getir (Sadece admin) - Maskelenmiş"""
    settings = await db.email_settings.find_one({"id": "email_settings"}, {"_id": 0})
    
    if not settings:
        return {
            "id": "email_settings",
            "smtp_host": "smtp.visupanel.com",
            "smtp_port": 587,
            "smtp_user": "info@visupanel.com",
            "smtp_password": None,
            "smtp_password_masked": None,
            "sender_name": "IZE Case Resolver",
            "sender_email": "info@visupanel.com",
            "email_enabled": True
        }
    
    # Maskelenmiş versiyonu ekle
    response = {
        "id": settings.get("id", "email_settings"),
        "smtp_host": settings.get("smtp_host", "smtp.visupanel.com"),
        "smtp_port": settings.get("smtp_port", 587),
        "smtp_user": settings.get("smtp_user", "info@visupanel.com"),
        "smtp_password": settings.get("smtp_password"),
        "smtp_password_masked": mask_password(settings.get("smtp_password") or ""),
        "sender_name": settings.get("sender_name", "IZE Case Resolver"),
        "sender_email": settings.get("sender_email", "info@visupanel.com"),
        "email_enabled": settings.get("email_enabled", True),
        "updated_at": settings.get("updated_at")
    }
    
    return response


@router.put("/email-settings")
async def update_email_settings(settings_update: EmailSettingsUpdate, admin: dict = Depends(get_admin_user)):
    """E-posta ayarlarını güncelle (Sadece admin)"""
    settings = await db.email_settings.find_one({"id": "email_settings"}, {"_id": 0})
    
    if not settings:
        settings = {
            "id": "email_settings",
            "smtp_host": "smtp.visupanel.com",
            "smtp_port": 587,
            "smtp_user": "info@visupanel.com",
            "smtp_password": None,
            "sender_name": "IZE Case Resolver",
            "sender_email": "info@visupanel.com",
            "email_enabled": True
        }
    
    # Güncelle
    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            settings[key] = value
    
    settings['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # _id varsa sil
    if '_id' in settings:
        del settings['_id']
    
    await db.email_settings.update_one(
        {"id": "email_settings"},
        {"$set": settings},
        upsert=True
    )
    
    return {"message": "E-posta ayarları güncellendi"}


@router.post("/email-settings/test")
async def test_email_connection(admin: dict = Depends(get_admin_user)):
    """SMTP bağlantısını test et (Sadece admin)"""
    result = await test_smtp_connection()
    return result



# ==================== BRANCH MANAGEMENT ====================

@router.get("/branches")
async def get_branches(admin: dict = Depends(get_admin_user)):
    """Tüm şubeleri listele"""
    branches = await db.branches.find({}, {"_id": 0}).sort("name", 1).to_list(100)
    
    # Eğer veritabanında şube yoksa, varsayılanları ekle
    if not branches:
        for name in DEFAULT_BRANCHES:
            branch = Branch(name=name)
            branch_dict = branch.model_dump()
            branch_dict['created_at'] = branch_dict['created_at'].isoformat()
            await db.branches.insert_one(branch_dict)
        branches = await db.branches.find({}, {"_id": 0}).sort("name", 1).to_list(100)
    
    return branches


@router.post("/branches")
async def create_branch(branch_data: BranchCreate, admin: dict = Depends(get_admin_user)):
    """Yeni şube ekle"""
    existing = await db.branches.find_one({"name": branch_data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Bu şube zaten mevcut")
    
    branch = Branch(name=branch_data.name)
    branch_dict = branch.model_dump()
    branch_dict['created_at'] = branch_dict['created_at'].isoformat()
    
    await db.branches.insert_one(branch_dict)
    
    return {"message": "Şube eklendi", "branch": branch_dict}


@router.delete("/branches/{branch_id}")
async def delete_branch(branch_id: str, admin: dict = Depends(get_admin_user)):
    """Şube sil"""
    result = await db.branches.delete_one({"id": branch_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Şube bulunamadı")
    
    return {"message": "Şube silindi"}


@router.patch("/branches/{branch_id}/toggle")
async def toggle_branch(branch_id: str, admin: dict = Depends(get_admin_user)):
    """Şube aktif/pasif yap"""
    branch = await db.branches.find_one({"id": branch_id})
    if not branch:
        raise HTTPException(status_code=404, detail="Şube bulunamadı")
    
    new_status = not branch.get('is_active', True)
    await db.branches.update_one({"id": branch_id}, {"$set": {"is_active": new_status}})
    
    return {"message": "Şube durumu güncellendi", "is_active": new_status}


# ==================== PRICING PLANS MANAGEMENT ====================

@router.get("/pricing-plans")
async def get_pricing_plans(admin: dict = Depends(get_admin_user)):
    """Tüm fiyatlandırma planlarını listele"""
    plans = await db.pricing_plans.find({}, {"_id": 0}).sort("price", 1).to_list(100)
    
    # Varsayılan planları ekle
    if not plans:
        default_plans = [
            PricingPlan(name="Başlangıç", credits=10, price=100, currency="TRY", features=["10 IZE Analizi", "E-posta Desteği"]),
            PricingPlan(name="Pro", credits=50, price=400, currency="TRY", is_popular=True, features=["50 IZE Analizi", "Öncelikli Destek", "Detaylı Raporlar"]),
            PricingPlan(name="Enterprise", credits=200, price=1200, currency="TRY", features=["200 IZE Analizi", "7/24 Destek", "Özel Entegrasyon", "API Erişimi"]),
        ]
        for plan in default_plans:
            plan_dict = plan.model_dump()
            plan_dict['created_at'] = plan_dict['created_at'].isoformat()
            await db.pricing_plans.insert_one(plan_dict)
        plans = await db.pricing_plans.find({}, {"_id": 0}).sort("price", 1).to_list(100)
    
    return plans


@router.post("/pricing-plans")
async def create_pricing_plan(plan_data: PricingPlanCreate, admin: dict = Depends(get_admin_user)):
    """Yeni fiyatlandırma planı ekle"""
    plan = PricingPlan(**plan_data.model_dump())
    plan_dict = plan.model_dump()
    plan_dict['created_at'] = plan_dict['created_at'].isoformat()
    
    await db.pricing_plans.insert_one(plan_dict)
    
    return {"message": "Plan eklendi", "plan": plan_dict}


@router.put("/pricing-plans/{plan_id}")
async def update_pricing_plan(plan_id: str, plan_update: PricingPlanUpdate, admin: dict = Depends(get_admin_user)):
    """Fiyatlandırma planını güncelle"""
    plan = await db.pricing_plans.find_one({"id": plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan bulunamadı")
    
    update_data = plan_update.model_dump(exclude_unset=True)
    if update_data:
        await db.pricing_plans.update_one({"id": plan_id}, {"$set": update_data})
    
    updated_plan = await db.pricing_plans.find_one({"id": plan_id}, {"_id": 0})
    return updated_plan


@router.delete("/pricing-plans/{plan_id}")
async def delete_pricing_plan(plan_id: str, admin: dict = Depends(get_admin_user)):
    """Fiyatlandırma planını sil"""
    result = await db.pricing_plans.delete_one({"id": plan_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan bulunamadı")
    
    return {"message": "Plan silindi"}


# ==================== USER CREDIT MANAGEMENT ====================

@router.patch("/users/{user_id}/set-unlimited-credits")
async def set_unlimited_credits(user_id: str, unlimited: bool = True, admin: dict = Depends(get_admin_user)):
    """Kullanıcıya sınırsız kredi ver/kaldır"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    await db.users.update_one({"id": user_id}, {"$set": {"has_unlimited_credits": unlimited}})
    
    return {"message": f"Sınırsız kredi {'verildi' if unlimited else 'kaldırıldı'}", "has_unlimited_credits": unlimited}


@router.patch("/users/{user_id}/set-credits")
async def set_user_credits(user_id: str, amount: int, admin: dict = Depends(get_admin_user)):
    """Kullanıcının kredi miktarını ayarla"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    await db.users.update_one({"id": user_id}, {"$set": {"free_analyses_remaining": amount}})
    
    return {"message": f"Kredi {amount} olarak ayarlandı", "credits": amount}
