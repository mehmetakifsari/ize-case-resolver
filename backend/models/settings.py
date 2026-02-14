from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime, timezone


class APISettings(BaseModel):
    """API anahtarları ayarları modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default="api_settings")
    emergent_key: Optional[str] = None
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    google_key: Optional[str] = None
    other_keys: Dict[str, str] = {}
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class APISettingsUpdate(BaseModel):
    """API ayarları güncelleme modeli"""
    emergent_key: Optional[str] = None
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    google_key: Optional[str] = None
    other_keys: Optional[Dict[str, str]] = None


class EmailSettings(BaseModel):
    """E-posta SMTP ayarları modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default="email_settings")
    smtp_host: str = "smtp.visupanel.com"
    smtp_port: int = 587
    smtp_user: str = "info@visupanel.com"
    smtp_password: str = ""
    sender_name: str = "IZE Case Resolver"
    sender_email: str = "info@visupanel.com"
    email_enabled: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmailSettingsUpdate(BaseModel):
    """E-posta ayarları güncelleme modeli"""
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    email_enabled: Optional[bool] = None
