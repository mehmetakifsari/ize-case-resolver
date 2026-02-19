from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid


class ContractRule(BaseModel):
    """Kontrat (garanti uzatımı) paket modeli"""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_name: str
    items: List[str] = []
    keywords: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContractRuleCreate(BaseModel):
    package_name: str
    items: List[str] = []
    keywords: List[str] = []


class ContractRuleUpdate(BaseModel):
    package_name: Optional[str] = None
    items: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None
