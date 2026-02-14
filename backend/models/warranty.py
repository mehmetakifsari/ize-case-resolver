from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid


class WarrantyRule(BaseModel):
    """Garanti kuralı modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_version: str
    rule_text: str
    keywords: List[str] = []
    source_type: str = "manual"  # "manual" veya "pdf"
    source_filename: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WarrantyRuleCreate(BaseModel):
    """Garanti kuralı oluşturma modeli"""
    rule_version: str
    rule_text: str
    keywords: List[str] = []


class WarrantyRuleUpdate(BaseModel):
    """Garanti kuralı güncelleme modeli"""
    rule_version: Optional[str] = None
    rule_text: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None
