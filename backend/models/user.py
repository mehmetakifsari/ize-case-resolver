from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import re

# Varsayılan şube listesi (dinamik olarak DB'den de alınabilir)
DEFAULT_BRANCHES = ["Bursa", "İzmit", "Orhanlı", "Hadımköy", "Keşan"]
BRANCHES = DEFAULT_BRANCHES  # Geriye uyumluluk için


class User(BaseModel):
    """Kullanıcı modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    phone_number: str = ""
    branch: str = ""  # Şube
    role: str = "user"  # admin veya user
    is_active: bool = True
    is_email_verified: bool = False  # E-posta doğrulama durumu
    free_analyses_remaining: int = 5
    has_unlimited_credits: bool = False  # Sınırsız kredi
    total_analyses: int = 0
    emails_sent: int = 0  # Gönderilen e-posta sayısı
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserInDB(User):
    """Database'deki kullanıcı (şifre hash'li)"""
    hashed_password: str


class UserCreate(BaseModel):
    """Kullanıcı oluşturma modeli"""
    email: EmailStr
    password: str
    full_name: str
    phone_number: str = ""
    branch: str = ""
    role: str = "user"
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Şifre karmaşıklık kontrolü: 8+ karakter, büyük/küçük harf, özel karakter"""
        if len(v) < 8:
            raise ValueError('Şifre en az 8 karakter olmalıdır')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Şifre en az bir büyük harf içermelidir')
        if not re.search(r'[a-z]', v):
            raise ValueError('Şifre en az bir küçük harf içermelidir')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Şifre en az bir özel karakter içermelidir (!@#$%^&*(),.?":{}|<>)')
        return v
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Ad soyad en az 2 karakter olmalıdır')
        return v.strip()
    
    @field_validator('branch')
    @classmethod
    def validate_branch(cls, v):
        if v and v not in BRANCHES:
            raise ValueError(f'Geçersiz şube. Şubeler: {", ".join(BRANCHES)}')
        return v


class UserUpdate(BaseModel):
    """Kullanıcı güncelleme modeli"""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    branch: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_email_verified: Optional[bool] = None
    free_analyses_remaining: Optional[int] = None
    has_unlimited_credits: Optional[bool] = None


class UserLogin(BaseModel):
    """Login modeli"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Token response modeli"""
    access_token: str
    token_type: str
    user: dict


# Şube yönetimi modelleri
class Branch(BaseModel):
    """Şube modeli"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BranchCreate(BaseModel):
    """Şube oluşturma modeli"""
    name: str


# Fiyatlandırma modelleri
class PricingPlan(BaseModel):
    """Fiyatlandırma planı modeli"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Plan adı (ör: Başlangıç, Pro, Enterprise)
    credits: int  # Kredi miktarı
    price: float  # Fiyat
    currency: str = "TRY"  # Para birimi
    is_popular: bool = False  # Öne çıkan plan
    is_active: bool = True
    features: List[str] = []  # Özellikler listesi
    plan_type: str = "package"  # package veya subscription
    billing_period: str = "one_time"  # one_time, monthly, yearly
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PricingPlanCreate(BaseModel):
    """Fiyatlandırma planı oluşturma"""
    name: str
    credits: int
    price: float
    currency: str = "TRY"
    is_popular: bool = False
    features: List[str] = []
    plan_type: str = "package"
    billing_period: str = "one_time"


class PricingPlanUpdate(BaseModel):
    """Fiyatlandırma planı güncelleme"""
    name: Optional[str] = None
    credits: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None
    features: Optional[List[str]] = None
    plan_type: Optional[str] = None
    billing_period: Optional[str] = None
