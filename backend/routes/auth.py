from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import User, UserInDB, UserCreate, UserLogin, Token
from services.auth import verify_password, get_password_hash, create_access_token, decode_access_token
from services.email import send_verification_email
from database import db
import uuid
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Token'dan mevcut kullanıcıyı alır"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Aktif kullanıcıyı kontrol eder"""
    if not current_user.get("is_active"):
        raise HTTPException(status_code=400, detail="Hesabınız pasif durumda")
    return current_user


async def get_admin_user(current_user: dict = Depends(get_current_active_user)) -> dict:
    """Admin yetkisi kontrol eder"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gereklidir")
    return current_user


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """Yeni kullanıcı kaydı"""
    # Email kontrolü
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu email adresi zaten kayıtlı")
    
    # E-posta doğrulama tokenı oluştur
    verification_token = str(uuid.uuid4())
    verification_expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    
    # Kullanıcı oluştur
    hashed_password = get_password_hash(user_data.password)
    user = UserInDB(
        email=user_data.email,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        branch=user_data.branch,
        role=user_data.role,
        hashed_password=hashed_password,
        is_email_verified=False  # Varsayılan: doğrulanmamış
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    user_dict['verification_token'] = verification_token
    user_dict['verification_expires'] = verification_expires
    
    await db.users.insert_one(user_dict)
    
    # Doğrulama e-postası gönder (arka planda)
    try:
        await send_verification_email(user.email, user.full_name, verification_token)
    except Exception as e:
        print(f"E-posta doğrulama gönderimi hatası: {e}")
    
    # Token oluştur
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    
    user_response = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "branch": user.branch,
        "role": user.role,
        "free_analyses_remaining": user.free_analyses_remaining,
        "total_analyses": user.total_analyses,
        "is_email_verified": False
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Kullanıcı girişi"""
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user or not verify_password(credentials.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı")
    
    if not user.get('is_active', True):
        raise HTTPException(status_code=400, detail="Hesabınız pasif durumda. Yönetici ile iletişime geçin.")
    
    # Token oluştur
    access_token = create_access_token(data={"sub": user['id'], "role": user['role']})
    
    user_response = {
        "id": user['id'],
        "email": user['email'],
        "full_name": user['full_name'],
        "phone_number": user.get('phone_number', ''),
        "branch": user.get('branch', ''),
        "role": user['role'],
        "free_analyses_remaining": user.get('free_analyses_remaining', 0),
        "total_analyses": user.get('total_analyses', 0)
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """Mevcut kullanıcı bilgisi"""
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "full_name": current_user['full_name'],
        "phone_number": current_user.get('phone_number', ''),
        "branch": current_user.get('branch', ''),
        "role": current_user['role'],
        "is_active": current_user['is_active'],
        "free_analyses_remaining": current_user.get('free_analyses_remaining', 0),
        "total_analyses": current_user.get('total_analyses', 0)
    }
