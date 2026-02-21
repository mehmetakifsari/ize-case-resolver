from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List, Optional
from datetime import datetime, timezone
import os
import uuid
import shutil
from pathlib import Path
from models.user import (
    User, UserInDB, UserCreate, UserUpdate, UserPasswordUpdate, DEFAULT_BRANCHES,
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


@router.get("/ai-analytics")
async def get_ai_analytics(
    provider: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(get_admin_user)
):
    """AI sağlayıcılarına göre kullanım ve maliyet analitiği"""
    from datetime import timedelta

    providers = [
        "openai",
        "google_gemini",
        "emergent",
        "anthropic_claude",
        "other",
    ]

    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    base_match = {"created_at": {"$gte": start_date}}

    if provider and provider != "all":
        base_match["ai_provider"] = provider

    provider_pipeline = [
        {"$match": base_match},
        {
            "$group": {
                "_id": {"$ifNull": ["$ai_provider", "other"]},
                "total_queries": {"$sum": 1},
                "total_tokens": {"$sum": {"$ifNull": ["$ai_total_tokens", 0]}},
                "total_cost_usd": {"$sum": {"$ifNull": ["$ai_estimated_cost_usd", 0]}},
            }
        },
    ]

    by_provider_raw = await db.ize_cases.aggregate(provider_pipeline).to_list(20)
    by_provider = {item["_id"]: item for item in by_provider_raw}

    provider_cards = {}
    for item in providers:
        stats = by_provider.get(item, {})
        provider_cards[item] = {
            "total_queries": stats.get("total_queries", 0),
            "total_tokens": stats.get("total_tokens", 0),
            "total_cost_usd": round(stats.get("total_cost_usd", 0), 6),
        }

    trend_pipeline = [
        {"$match": base_match},
        {
            "$group": {
                "_id": {"$substr": ["$created_at", 0, 10]},
                "queries": {"$sum": 1},
                "tokens": {"$sum": {"$ifNull": ["$ai_total_tokens", 0]}},
                "cost_usd": {"$sum": {"$ifNull": ["$ai_estimated_cost_usd", 0]}},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    trend_raw = await db.ize_cases.aggregate(trend_pipeline).to_list(400)

    api_settings = await db.api_settings.find_one({"id": "api_settings"}, {"_id": 0}) or {}
    configured = {
        "openai": bool(api_settings.get("openai_key")),
        "google_gemini": bool(api_settings.get("google_key")),
        "emergent": bool(api_settings.get("emergent_key")),
        "anthropic_claude": bool(api_settings.get("anthropic_key")),
        "other": bool(api_settings.get("other_keys")),
    }

    totals = {
        "queries": sum(item["total_queries"] for item in provider_cards.values()),
        "tokens": sum(item["total_tokens"] for item in provider_cards.values()),
        "cost_usd": round(sum(item["total_cost_usd"] for item in provider_cards.values()), 6),
    }

    return {
        "provider": provider or "all",
        "days": days,
        "totals": totals,
        "providers": provider_cards,
        "configured": configured,
        "trend": [
            {
                "date": item["_id"],
                "queries": item.get("queries", 0),
                "tokens": item.get("tokens", 0),
                "cost_usd": round(item.get("cost_usd", 0), 6),
            }
            for item in trend_raw
        ],
    }


def build_system_log_query(level: Optional[str], event_type: Optional[str], search: Optional[str]):
    query = {}
    if level:
        query["level"] = level.upper()
    if event_type:
        query["event_type"] = event_type
    if search:
        query["$or"] = [
            {"path": {"$regex": search, "$options": "i"}},
            {"method": {"$regex": search, "$options": "i"}},
            {"client_ip": {"$regex": search, "$options": "i"}},
            {"user_agent": {"$regex": search, "$options": "i"}},
        ]
    return query


@router.get("/system-logs")
async def get_system_logs(
    level: Optional[str] = None,
    event_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=250),
    admin: dict = Depends(get_admin_user)
):
    """Sistem loglarını filtreli ve sayfalı listele (Sadece admin)"""
    query = build_system_log_query(level, event_type, search)

    skip = (page - 1) * page_size
    total = await db.system_logs.count_documents(query)
    logs = await db.system_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)

    return {
        "items": logs,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max((total + page_size - 1) // page_size, 1),
        }
    }


@router.get("/system-logs/export")
async def export_system_logs(
    level: Optional[str] = None,
    event_type: Optional[str] = None,
    search: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """Sistem loglarını txt olarak dışa aktar"""
    query = build_system_log_query(level, event_type, search)
    logs = await db.system_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(2000).to_list(2000)

    lines = []
    for log in logs:
        indicators = ", ".join(log.get("security_indicators", [])) or "-"
        line = (
            f"[{log.get('created_at', '-')}] {log.get('level', '-')} {log.get('event_type', '-')} "
            f"{log.get('method', '-')} {log.get('path', '-')} "
            f"status={log.get('status_code', '-')} ip={log.get('client_ip', '-')} "
            f"indicators={indicators}"
        )
        lines.append(line)

    content = "\n".join(lines) if lines else "Kayıt bulunamadı"
    return {
        "filename": f"system-logs-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.txt",
        "content": content,
        "count": len(logs),
    }


@router.get("/system-logs/summary")
async def get_system_logs_summary(admin: dict = Depends(get_admin_user)):
    """Sistem logları için özet istatistikler"""
    total = await db.system_logs.count_documents({})
    error_count = await db.system_logs.count_documents({"level": "ERROR"})
    warning_count = await db.system_logs.count_documents({"level": "WARNING"})
    security_count = await db.system_logs.count_documents({"event_type": "security_alert"})

    from datetime import timedelta
    day_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent_24h = await db.system_logs.count_documents({"created_at": {"$gte": day_ago}})

    top_paths = await db.system_logs.aggregate([
        {"$group": {"_id": "$path", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]).to_list(5)

    top_security_indicators = await db.system_logs.aggregate([
        {"$unwind": "$security_indicators"},
        {"$group": {"_id": "$security_indicators", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]).to_list(5)

    return {
        "total": total,
        "errors": error_count,
        "warnings": warning_count,
        "security_alerts": security_count,
        "recent_24h": recent_24h,
        "top_paths": [{"path": item.get("_id") or "-", "count": item.get("count", 0)} for item in top_paths],
        "top_security_indicators": [{"indicator": item.get("_id"), "count": item.get("count", 0)} for item in top_security_indicators],
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

@router.patch("/users/{user_id}/password")
async def update_user_password(user_id: str, payload: UserPasswordUpdate, admin: dict = Depends(get_admin_user)):
    """Kullanıcı şifresini güncelle (Sadece admin)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    hashed = get_password_hash(payload.new_password)
    await db.users.update_one({"id": user_id}, {"$set": {"hashed_password": hashed}})

    return {"message": "Şifre güncellendi"}

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
            PricingPlan(name="Abonelik Basic", credits=20, price=299, currency="TRY", plan_type="subscription", billing_period="monthly", features=["Aylık 20 IZE Analizi", "Öncelikli Destek"]),
            PricingPlan(name="Abonelik Pro", credits=300, price=2990, currency="TRY", is_popular=True, plan_type="subscription", billing_period="yearly", features=["Yıllık 300 IZE Analizi", "Öncelikli Destek", "Detaylı Raporlar"]),
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
    # Motor/PyMongo insert işlemi sonrası sözlüğe otomatik _id (ObjectId) ekler.
    # Bu alan JSON serialize edilemediği için response'tan temizliyoruz.
    plan_dict.pop("_id", None)
    
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


# ==================== IMAGE UPLOAD ====================

ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    image_type: str = "logo",
    admin: dict = Depends(get_admin_user)
):
    """Logo veya favicon yükle (Sadece admin)"""
    # Dosya uzantısını kontrol et
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Geçersiz dosya tipi. İzin verilen: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    # Dosya boyutunu kontrol et
    file.file.seek(0, 2)  # Dosya sonuna git
    file_size = file.file.tell()
    file.file.seek(0)  # Başa dön
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Dosya boyutu çok büyük. Maksimum: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Benzersiz dosya adı oluştur
    unique_filename = f"{image_type}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Dosyayı kaydet
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya kaydedilemedi: {str(e)}")
    
    # Public URL oluştur
    public_url = f"/uploads/{unique_filename}"
    
    return {
        "message": "Dosya başarıyla yüklendi",
        "filename": unique_filename,
        "url": public_url,
        "image_type": image_type
    }


@router.delete("/delete-image/{filename}")
async def delete_image(filename: str, admin: dict = Depends(get_admin_user)):
    """Yüklenen görsel dosyasını sil (Sadece admin)"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")
    
    # Güvenlik: sadece uploads dizinindeki dosyaları sil
    try:
        file_path = file_path.resolve()
        upload_dir = UPLOAD_DIR.resolve()
        if not str(file_path).startswith(str(upload_dir)):
            raise HTTPException(status_code=403, detail="Bu dosyaya erişim izni yok")
        
        os.remove(file_path)
        return {"message": "Dosya silindi", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya silinemedi: {str(e)}")
