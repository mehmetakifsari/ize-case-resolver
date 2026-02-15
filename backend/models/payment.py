from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


class PaymentMethod(str, Enum):
    """Ödeme yöntemi"""
    STRIPE = "stripe"
    IYZICO = "iyzico"
    BANK_TRANSFER = "bank_transfer"


class PaymentStatus(str, Enum):
    """Ödeme durumu"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Currency(str, Enum):
    """Para birimi"""
    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"


class PackageType(str, Enum):
    """Paket tipi"""
    CREDIT = "credit"  # Tek seferlik kredi paketi
    SUBSCRIPTION = "subscription"  # Aylık abonelik


class SubscriptionInterval(str, Enum):
    """Abonelik periyodu"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


# ==================== PAKET MODELLERİ ====================

class CreditPackage(BaseModel):
    """Kredi paketi modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # "Başlangıç Paketi", "Pro Paketi" vb.
    name_en: str = ""  # İngilizce isim
    description: str = ""
    description_en: str = ""
    credits: int  # Kaç analiz hakkı
    price_try: float  # TL fiyat
    price_usd: float  # USD fiyat
    price_eur: float  # EUR fiyat
    discount_percent: int = 0  # İndirim yüzdesi
    is_popular: bool = False  # Öne çıkan paket
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubscriptionPlan(BaseModel):
    """Abonelik planı modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # "Başlangıç", "Pro", "Kurumsal"
    name_en: str = ""
    description: str = ""
    description_en: str = ""
    interval: SubscriptionInterval = SubscriptionInterval.MONTHLY
    credits_per_month: int  # Aylık analiz hakkı
    price_try: float
    price_usd: float
    price_eur: float
    features: List[str] = []  # Özellik listesi
    features_en: List[str] = []
    is_popular: bool = False
    is_active: bool = True
    sort_order: int = 0
    # iyzico ve Stripe referans kodları
    iyzico_product_code: Optional[str] = None
    iyzico_plan_code: Optional[str] = None
    stripe_price_id_try: Optional[str] = None
    stripe_price_id_usd: Optional[str] = None
    stripe_price_id_eur: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== İŞLEM MODELLERİ ====================

class PaymentTransaction(BaseModel):
    """Ödeme işlemi modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    package_type: PackageType
    package_id: str  # credit_package veya subscription_plan id'si
    package_name: str
    
    # Ödeme bilgileri
    payment_method: PaymentMethod
    amount: float
    currency: Currency
    
    # Durum
    status: PaymentStatus = PaymentStatus.PENDING
    
    # Provider referansları
    stripe_session_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    iyzico_payment_id: Optional[str] = None
    iyzico_conversation_id: Optional[str] = None
    
    # Havale/EFT için
    bank_reference: Optional[str] = None
    bank_transfer_proof: Optional[str] = None  # Dekont URL
    
    # Kredi bilgisi
    credits_to_add: int = 0
    
    # Meta
    metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class UserSubscription(BaseModel):
    """Kullanıcı aboneliği modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    plan_id: str
    plan_name: str
    
    # Durum
    status: str = "active"  # active, cancelled, expired, past_due
    
    # Dönem bilgileri
    current_period_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_period_end: Optional[datetime] = None
    
    # Provider bilgileri
    payment_method: PaymentMethod
    stripe_subscription_id: Optional[str] = None
    iyzico_subscription_code: Optional[str] = None
    
    # Krediler
    monthly_credits: int = 0
    credits_remaining: int = 0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cancelled_at: Optional[datetime] = None


# ==================== BANKA BİLGİLERİ ====================

class BankAccount(BaseModel):
    """Banka hesap bilgileri"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bank_name: str
    account_holder: str
    iban: str
    currency: Currency
    is_active: bool = True
    sort_order: int = 0


class BankTransferSettings(BaseModel):
    """Havale/EFT ayarları"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = "bank_transfer_settings"
    is_enabled: bool = True
    instructions: str = "Ödemenizi yaptıktan sonra dekont görselini yükleyiniz."
    instructions_en: str = "After making the payment, please upload the receipt."
    accounts: List[BankAccount] = []
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== REQUEST/RESPONSE MODELLERİ ====================

class CreateCheckoutRequest(BaseModel):
    """Checkout oluşturma isteği"""
    package_type: PackageType
    package_id: str
    payment_method: PaymentMethod
    currency: Currency
    origin_url: str  # Frontend URL (success/cancel URL oluşturmak için)


class CheckoutResponse(BaseModel):
    """Checkout yanıtı"""
    success: bool
    checkout_url: Optional[str] = None
    session_id: Optional[str] = None
    transaction_id: Optional[str] = None
    message: Optional[str] = None


class BankTransferRequest(BaseModel):
    """Havale/EFT isteği"""
    package_type: PackageType
    package_id: str
    currency: Currency
    bank_account_id: str
    transfer_reference: str  # Kullanıcının girdiği referans
    transfer_proof_url: Optional[str] = None  # Dekont URL


class PaymentStatusResponse(BaseModel):
    """Ödeme durumu yanıtı"""
    transaction_id: str
    status: PaymentStatus
    payment_status: str
    amount: float
    currency: str
    credits_added: int = 0
    message: Optional[str] = None
