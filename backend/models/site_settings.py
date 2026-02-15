from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime, timezone


class SiteSettings(BaseModel):
    """Site genel ayarları modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default="site_settings")
    
    # Site Bilgileri
    site_name: str = "IZE Case Resolver"
    site_title: str = "IZE Case Resolver - AI ile Garanti Analizi"
    site_description: str = "Yurtdışı garanti dosyalarınızı yapay zeka ile otomatik analiz edin."
    site_logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    
    # Banka/Ödeme Bilgileri
    bank_name: Optional[str] = None  # Banka adı
    bank_iban: Optional[str] = None  # IBAN numarası
    bank_account_holder: Optional[str] = None  # Hesap sahibi adı
    bank_swift: Optional[str] = None  # SWIFT kodu (uluslararası transferler için)
    
    # Dil Ayarları
    default_language: str = "tr"  # tr veya en
    
    # SEO Ayarları
    meta_title: str = "IZE Case Resolver - Garanti Dosyası Analiz Sistemi"
    meta_description: str = "Renault Trucks yurtdışı garanti IZE dosyalarını yapay zeka ile analiz edin. OCR destekli PDF okuma, otomatik garanti değerlendirmesi."
    meta_keywords: str = "ize, garanti, warranty, renault trucks, pdf analiz, ocr, yapay zeka, ai"
    meta_author: str = ""
    canonical_url: Optional[str] = None
    og_image_url: Optional[str] = None
    
    # Analytics
    google_analytics_id: Optional[str] = None  # G-XXXXXXXXXX veya UA-XXXXXXXX-X
    google_tag_manager_id: Optional[str] = None  # GTM-XXXXXXX
    yandex_metrica_id: Optional[str] = None  # XXXXXXXX
    facebook_pixel_id: Optional[str] = None
    
    # İletişim
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    
    # Sosyal Medya
    social_facebook: Optional[str] = None
    social_twitter: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_instagram: Optional[str] = None
    
    # Footer
    footer_text: str = "© 2026 IZE Case Resolver. Tüm hakları saklıdır."
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SiteSettingsUpdate(BaseModel):
    """Site ayarları güncelleme modeli"""
    # Site Bilgileri
    site_name: Optional[str] = None
    site_title: Optional[str] = None
    site_description: Optional[str] = None
    site_logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    
    # Dil
    default_language: Optional[str] = None
    
    # SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    meta_author: Optional[str] = None
    canonical_url: Optional[str] = None
    og_image_url: Optional[str] = None
    
    # Analytics
    google_analytics_id: Optional[str] = None
    google_tag_manager_id: Optional[str] = None
    yandex_metrica_id: Optional[str] = None
    facebook_pixel_id: Optional[str] = None
    
    # İletişim
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    
    # Sosyal Medya
    social_facebook: Optional[str] = None
    social_twitter: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_instagram: Optional[str] = None
    
    # Footer
    footer_text: Optional[str] = None
