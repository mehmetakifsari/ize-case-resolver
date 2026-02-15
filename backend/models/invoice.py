"""
Fatura Modelleri
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


class InvoiceProvider(str, Enum):
    """Fatura sağlayıcısı"""
    PARASUT = "parasut"
    BIZIMHESAP = "bizimhesap"
    BIRFATURA = "birfatura"
    MANUAL = "manual"  # Manuel PDF oluşturma


class InvoiceStatus(str, Enum):
    """Fatura durumu"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    CANCELLED = "cancelled"


class CompanyInfo(BaseModel):
    """Şirket bilgileri"""
    model_config = ConfigDict(extra="ignore")
    
    company_name: str = "IZE Case Resolver Ltd. Şti."
    tax_office: str = "Nilüfer Vergi Dairesi"
    tax_number: str = "1234567890"
    address: str = "Nilüfer, Bursa, Türkiye"
    phone: str = "+90 224 123 45 67"
    email: str = "info@izeresolver.com"
    website: str = "https://izeresolver.com"
    logo_url: Optional[str] = None


class InvoiceItem(BaseModel):
    """Fatura kalemi"""
    model_config = ConfigDict(extra="ignore")
    
    description: str
    quantity: int = 1
    unit_price: float
    tax_rate: float = 20.0  # KDV oranı
    total: float = 0.0
    
    def calculate_total(self):
        self.total = self.quantity * self.unit_price
        return self.total


class Invoice(BaseModel):
    """Fatura modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str  # Fatura numarası (örn: IZE-2024-0001)
    
    # İlişkiler
    transaction_id: str
    user_id: str
    user_email: str
    
    # Müşteri bilgileri
    customer_name: str
    customer_email: str
    customer_address: Optional[str] = None
    customer_tax_office: Optional[str] = None
    customer_tax_number: Optional[str] = None
    
    # Fatura bilgileri
    items: List[InvoiceItem] = []
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "TRY"
    
    # Durum
    status: InvoiceStatus = InvoiceStatus.DRAFT
    provider: InvoiceProvider = InvoiceProvider.MANUAL
    provider_invoice_id: Optional[str] = None  # Dış sistemdeki ID
    
    # PDF
    pdf_url: Optional[str] = None
    
    # Meta
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    
    def calculate_totals(self):
        self.subtotal = sum(item.quantity * item.unit_price for item in self.items)
        self.tax_amount = sum((item.quantity * item.unit_price * item.tax_rate / 100) for item in self.items)
        self.total_amount = self.subtotal + self.tax_amount


class InvoiceSettings(BaseModel):
    """Fatura ayarları"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = "invoice_settings"
    
    # Aktif sağlayıcı
    active_provider: InvoiceProvider = InvoiceProvider.MANUAL
    auto_generate: bool = True  # Ödeme sonrası otomatik fatura oluştur
    
    # Şirket bilgileri
    company: CompanyInfo = Field(default_factory=CompanyInfo)
    
    # Paraşüt
    parasut_enabled: bool = False
    parasut_client_id: Optional[str] = None
    parasut_client_secret: Optional[str] = None
    parasut_company_id: Optional[str] = None
    
    # Bizimhesap
    bizimhesap_enabled: bool = False
    bizimhesap_api_key: Optional[str] = None
    bizimhesap_secret_key: Optional[str] = None
    
    # Birfatura
    birfatura_enabled: bool = False
    birfatura_api_key: Optional[str] = None
    birfatura_username: Optional[str] = None
    birfatura_password: Optional[str] = None
    
    # Fatura numarası prefix ve sayaç
    invoice_prefix: str = "IZE"
    next_invoice_number: int = 1
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaymentProviderSettings(BaseModel):
    """Ödeme sağlayıcı ayarları"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = "payment_provider_settings"
    
    # Stripe
    stripe_enabled: bool = True
    stripe_mode: str = "test"  # test veya live
    stripe_test_publishable_key: Optional[str] = None
    stripe_test_secret_key: Optional[str] = None
    stripe_live_publishable_key: Optional[str] = None
    stripe_live_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # iyzico
    iyzico_enabled: bool = True
    iyzico_mode: str = "sandbox"  # sandbox veya production
    iyzico_sandbox_api_key: Optional[str] = None
    iyzico_sandbox_secret_key: Optional[str] = None
    iyzico_production_api_key: Optional[str] = None
    iyzico_production_secret_key: Optional[str] = None
    
    # Havale/EFT
    bank_transfer_enabled: bool = True
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SocialMediaLinks(BaseModel):
    """Sosyal medya linkleri"""
    model_config = ConfigDict(extra="ignore")
    
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    youtube: Optional[str] = None
    whatsapp: Optional[str] = None


# Request/Response modelleri

class CreateInvoiceRequest(BaseModel):
    """Fatura oluşturma isteği"""
    transaction_id: str
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_tax_office: Optional[str] = None
    customer_tax_number: Optional[str] = None
    notes: Optional[str] = None


class InvoiceSettingsUpdate(BaseModel):
    """Fatura ayarları güncelleme"""
    active_provider: Optional[InvoiceProvider] = None
    auto_generate: Optional[bool] = None
    company: Optional[CompanyInfo] = None
    parasut_enabled: Optional[bool] = None
    parasut_client_id: Optional[str] = None
    parasut_client_secret: Optional[str] = None
    parasut_company_id: Optional[str] = None
    bizimhesap_enabled: Optional[bool] = None
    bizimhesap_api_key: Optional[str] = None
    bizimhesap_secret_key: Optional[str] = None
    birfatura_enabled: Optional[bool] = None
    birfatura_api_key: Optional[str] = None
    birfatura_username: Optional[str] = None
    birfatura_password: Optional[str] = None
    invoice_prefix: Optional[str] = None


class PaymentProviderSettingsUpdate(BaseModel):
    """Ödeme sağlayıcı ayarları güncelleme"""
    stripe_enabled: Optional[bool] = None
    stripe_mode: Optional[str] = None
    stripe_test_publishable_key: Optional[str] = None
    stripe_test_secret_key: Optional[str] = None
    stripe_live_publishable_key: Optional[str] = None
    stripe_live_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    iyzico_enabled: Optional[bool] = None
    iyzico_mode: Optional[str] = None
    iyzico_sandbox_api_key: Optional[str] = None
    iyzico_sandbox_secret_key: Optional[str] = None
    iyzico_production_api_key: Optional[str] = None
    iyzico_production_secret_key: Optional[str] = None
    bank_transfer_enabled: Optional[bool] = None
