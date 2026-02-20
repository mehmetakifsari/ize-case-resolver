from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid


class PartReplaced(BaseModel):
    """Değiştirilen parça modeli"""
    part_name: str
    description: str
    qty: int = 1


class IZECase(BaseModel):
    """IZE Case analiz sonuç modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Yükleyen kullanıcı
    branch: str = ""  # Şube
    case_title: str
    ize_no: str
    company: str
    plate: str
    vin: str
    warranty_start_date: Optional[str] = None
    repair_date: Optional[str] = None
    vehicle_age_months: int = 0
    repair_km: int = 0
    request_type: str
    
    is_within_2_year_warranty: bool
    warranty_decision: str  # COVERED / OUT_OF_COVERAGE / ADDITIONAL_INFO_REQUIRED
    decision_rationale: List[str] = []
    has_active_contract: bool = False
    contract_package_name: Optional[str] = None
    contract_decision: str = "NO_CONTRACT_COVERAGE"
    contract_covered_parts: List[str] = []
    
    failure_complaint: str
    failure_cause: str
    
    operations_performed: List[str] = []
    parts_replaced: List[Dict[str, Any]] = []
    
    repair_process_summary: str
    attachments: List[str] = []
    
    email_subject: str
    email_body: str
    
    pdf_file_name: str
    pdf_storage_name: Optional[str] = None
    extracted_text: str
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    binder_version_used: str = "default"
    month: int = Field(default_factory=lambda: datetime.now(timezone.utc).month)
    year: int = Field(default_factory=lambda: datetime.now(timezone.utc).year)
    
    is_archived: bool = False
    archived_at: Optional[datetime] = None


class IZECaseResponse(BaseModel):
    """API response modeli"""
    id: str
    case_title: str
    ize_no: str
    company: str
    warranty_decision: str
    branch: str = ""
    is_archived: bool = False
    created_at: datetime
