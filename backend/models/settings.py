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
