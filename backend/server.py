from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import PyPDF2
import io
from emergentintegrations.llm.chat import LlmChat, UserMessage
from auth import verify_password, get_password_hash, create_access_token, decode_access_token

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== DATA MODELS ====================

# Auth Models
security = HTTPBearer()

class User(BaseModel):
    """Kullanıcı modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: str = "user"  # admin veya user
    is_active: bool = True
    free_analyses_remaining: int = 5  # Ücretsiz analiz hakkı
    total_analyses: int = 0  # Toplam yapılan analiz sayısı
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserInDB(User):
    """Database'deki kullanıcı (şifre hash'li)"""
    hashed_password: str


class UserCreate(BaseModel):
    """Kullanıcı oluşturma modeli"""
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"


class UserLogin(BaseModel):
    """Login modeli"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Token response modeli"""
    access_token: str
    token_type: str
    user: dict


class PartReplaced(BaseModel):
    """Değiştirilen parça modeli"""
    part_name: str
    description: str
    qty: int = 1


class WarrantyRule(BaseModel):
    """Garanti kuralı modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_version: str
    rule_text: str
    keywords: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WarrantyRuleCreate(BaseModel):
    """Garanti kuralı oluşturma modeli"""
    rule_version: str
    rule_text: str
    keywords: List[str] = []




class APISettings(BaseModel):
    """API anahtarları ayarları modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: "api_settings")  # Tek kayıt
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    google_key: Optional[str] = None
    other_keys: Dict[str, str] = {}
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class APISettingsUpdate(BaseModel):
    """API ayarları güncelleme modeli"""
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    google_key: Optional[str] = None
    other_keys: Optional[Dict[str, str]] = None


class IZECase(BaseModel):
    """IZE Case analiz sonuç modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Yükleyen kullanıcı
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
    
    failure_complaint: str
    failure_cause: str
    
    operations_performed: List[str] = []
    parts_replaced: List[Dict[str, Any]] = []
    
    repair_process_summary: str
    attachments: List[str] = []
    
    email_subject: str
    email_body: str
    
    pdf_file_name: str
    extracted_text: str
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    binder_version_used: str = "default"
    month: int = Field(default_factory=lambda: datetime.now(timezone.utc).month)
    year: int = Field(default_factory=lambda: datetime.now(timezone.utc).year)


class IZECaseResponse(BaseModel):
    """API response modeli"""
    id: str
    case_title: str
    ize_no: str
    company: str
    warranty_decision: str
    created_at: datetime


# ==================== HELPER FUNCTIONS ====================

# Auth helper functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Token'dan mevcut kullanıcıyı alır"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Aktif kullanıcıyı kontrol eder"""
    if not current_user.get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_admin_user(current_user: dict = Depends(get_current_active_user)) -> dict:
    """Admin yetkisi kontrol eder"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


# PDF extraction
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

def extract_text_from_pdf(pdf_file: bytes) -> str:
    """PDF'den metin çıkarır - OCR destekli geliştirilmiş versiyon"""
    try:
        text = ""
        
        # Önce pdfplumber ile dene
        with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF toplam {total_pages} sayfa içeriyor")
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                
                if page_text and len(page_text.strip()) > 50:
                    # Normal metin çıkarma başarılı
                    text += f"\n\n--- SAYFA {page_num} ---\n{page_text}"
                    logger.info(f"Sayfa {page_num} işlendi (normal): {len(page_text)} karakter")
                else:
                    # Sayfa boş veya çok az metin - OCR dene
                    logger.warning(f"Sayfa {page_num} boş/az metin, OCR ile deneniyor...")
                    try:
                        # PDF sayfasını görüntüye çevir
                        images = convert_from_bytes(
                            pdf_file, 
                            first_page=page_num, 
                            last_page=page_num,
                            dpi=300
                        )
                        
                        if images:
                            # OCR uygula (Almanca ve Türkçe dil desteği)
                            ocr_text = pytesseract.image_to_string(
                                images[0], 
                                lang='deu+tur+eng',
                                config='--psm 6'
                            )
                            
                            if ocr_text and len(ocr_text.strip()) > 20:
                                text += f"\n\n--- SAYFA {page_num} (OCR) ---\n{ocr_text}"
                                logger.info(f"Sayfa {page_num} OCR ile işlendi: {len(ocr_text)} karakter")
                            else:
                                logger.warning(f"Sayfa {page_num} OCR sonuç vermedi")
                    except Exception as ocr_error:
                        logger.error(f"Sayfa {page_num} OCR hatası: {str(ocr_error)}")
        
        if not text or len(text) < 100:
            logger.error("PDF'den yeterli metin çıkarılamadı")
            raise HTTPException(status_code=400, detail="PDF'den yeterli metin çıkarılamadı")
        
        logger.info(f"Toplam çıkarılan metin: {len(text)} karakter")
        return text.strip()
    except Exception as e:
        logger.error(f"PDF okuma hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=f"PDF okunamadı: {str(e)}")


async def analyze_ize_with_ai(pdf_text: str, warranty_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """OpenAI ile IZE dosyasını analiz eder"""
    try:
        # Garanti kurallarını birleştir
        rules_text = "\n\n".join([
            f"Kural Versiyonu: {rule['rule_version']}\n{rule['rule_text']}\nAnahtar Kelimeler: {', '.join(rule['keywords'])}"
            for rule in warranty_rules
        ])
        
        # LLM Chat oluştur - OpenAI key kontrolü
        api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('EMERGENT_LLM_KEY', '')
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message="""Sen Renault Trucks için yurtdışı garanti IZE dosyalarını analiz eden uzman bir sistemsin.
            
GÖREVİN: PDF'deki tüm teknik detayları dikkatle okuyup yapılandırılmış JSON formatında çıkartmak.

ÖNEMLİ TALIMATLAR:
1. Parça isimlerini ve işlemleri Almanca veya İngilizce orijinal hallerinde de belirt
2. Tüm tarihleri YYYY-MM-DD formatına çevir (ör: 22.12.2023 → 2023-12-22)
3. Araç yaşını teslimat tarihi ile işlem tarihi arasındaki fark olarak hesapla
4. Yapılan tüm işlemleri madde madde listele (eksik bırakma)
5. Değiştirilen her parçayı ayrı ayrı belirt
6. Garanti değerlendirmesini kurallara göre yap (MHDV: 12 ay, Powertrain: +12 ay)
7. Email metnini profesyonel, kibar ve Türkçe yaz

ÇIKTI FORMATI (SADECE JSON):
{
    "ize_no": "IZE numarası (ör: IZE26006539)",
    "company": "Müşteri firma adı tam hali",
    "plate": "Plaka numarası",
    "vin": "VIN/Şasi numarası tam hali",
    "warranty_start_date": "YYYY-MM-DD (Teslimat/Zul. Datum)",
    "repair_date": "YYYY-MM-DD (İşlem tarihi)",
    "vehicle_age_months": araç_yaşı_ay_cinsinden_sayı,
    "repair_km": kilometre_sayısı,
    "request_type": "WARRANTY SUPPORT veya BREAKDOWN ASSISTANCE",
    "is_within_2_year_warranty": true/false (24 ay içinde mi?),
    "warranty_decision": "COVERED veya OUT_OF_COVERAGE veya ADDITIONAL_INFO_REQUIRED",
    "decision_rationale": [
        "Garanti kararının detaylı gerekçeleri",
        "Araç yaşı, parça türü, kapsam durumu"
    ],
    "failure_complaint": "Müşteri şikayeti veya arıza belirtisi (varsa)",
    "failure_cause": "Teknik arıza nedeni (hangi parça/sistem arızalandı)",
    "operations_performed": [
        "İşlem 1: Tam açıklama (ör: Tachometer Geber auswechseln - Takometre sensörü değişimi)",
        "İşlem 2: Tam açıklama (ör: Tachoprüfung Digital nach § 57b - Dijital takograf testi)",
        "... tüm işlemler"
    ],
    "parts_replaced": [
        {
            "partName": "Parça adı (orijinal + Türkçe)",
            "description": "Parçanın fonksiyonu ve neden değiştirildiği",
            "qty": 1
        }
    ],
    "repair_process_summary": "Yapılan işlemlerin kronolojik özeti: Ne yapıldı, hangi parçalar değişti, sonuç nedir",
    "email_subject": "Yurtdışı IZE Dosyası Hk. - IZE NO - PLAKA - ŞASİ",
    "email_body": "Sayın İlgili,\\n\\nYurtdışı [Firma] firmasından gelen IZE NO: [numara] numaralı dosya incelenmiştir...\\n\\nDetaylı ve kibar email metni"
}

SADECE JSON ÇIKTISI VER, BAŞKA AÇIKLAMA EKLEME!"""
        ).with_model("openai", "gpt-4o")
        
        # Analiz mesajı oluştur - Daha detaylı prompt ve daha fazla içerik
        prompt = f"""
IZE DOSYASI ANALİZ TALEBİ

--- RENAULT TRUCKS GARANTİ KURALLARI ---
{rules_text}

--- IZE DOSYASI HAM İÇERİK (TÜM SAYFALAR) ---
{pdf_text[:20000]}

--- ANALİZ TALİMATLARI ---
1. Yukarıdaki IZE dosyasındaki TÜM bilgileri dikkatle oku (özellikle WERKSTATTRECHNUNG ve fatura sayfalarını)
2. Araç bilgilerini çıkar (IZE no, firma, plaka, VIN, tarihler, km)
3. WERKSTATTRECHNUNG (atölye faturası) bölümünü bul ve yapılan TÜM işlemleri detaylıca listele
4. Her işlemin kod numarasını, Almanca ismini ve Türkçe açıklamasını belirt
5. Değiştirilen TÜM parçaları belirt (RT ile başlayan parça kodları, orijinal isim + Türkçe)
6. Teslimat tarihi (Zul. Datum veya Delivery Date) ile işlem tarihi (Leistungsdatum) arasındaki farkı hesapla
7. Garanti kurallarına göre değerlendirme yap:
   - MHDV: 12 ay temel garanti
   - Powertrain bileşenleri (motor, şanzıman, aks): +12 ay (toplam 24 ay)
   - LCV: 36 ay
   - Garanti dışı parçalar: Batarya, fren, debriyaj, cam, lastik, kayış, burç
8. Profesyonel ve kibar bir email metni oluştur (Türkçe)

ÖNEMLİ: İşlemler ve parçalar bölümünü boş bırakma! WERKSTATTRECHNUNG bölümündeki her satırı oku!

SADECE JSON formatında çıktı ver. Başka hiçbir metin ekleme!
"""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # JSON parse et
        import json
        # Response'dan JSON'ı çıkar (bazen markdown kod bloğu içinde gelir)
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        analysis_result = json.loads(response_text.strip())
        return analysis_result
        
    except Exception as e:
        logger.error(f"AI analiz hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {str(e)}")


# ==================== API ENDPOINTS ====================



# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Yeni kullanıcı kaydı"""
    # Email kontrolü
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Kullanıcı oluştur
    hashed_password = get_password_hash(user_data.password)
    user = UserInDB(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=hashed_password
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Token oluştur
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    
    user_response = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }


@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Kullanıcı girişi"""
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user or not verify_password(credentials.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user['is_active']:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Token oluştur
    access_token = create_access_token(data={"sub": user['id'], "role": user['role']})
    
    user_response = {
        "id": user['id'],
        "email": user['email'],
        "full_name": user['full_name'],
        "role": user['role']
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }


@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """Mevcut kullanıcı bilgisi"""
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "full_name": current_user['full_name'],
        "role": current_user['role'],
        "is_active": current_user['is_active']
    }


# ==================== ADMIN USER MANAGEMENT ====================

@api_router.get("/admin/users")
async def get_all_users(admin: dict = Depends(get_admin_user)):
    """Tüm kullanıcıları listele (Sadece admin)"""
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    return users


@api_router.post("/admin/users", response_model=User)
async def create_user(user_data: UserCreate, admin: dict = Depends(get_admin_user)):
    """Yeni kullanıcı oluştur (Sadece admin)"""
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    user = UserInDB(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=hashed_password
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    return User(**{k: v for k, v in user_dict.items() if k != 'hashed_password'})


@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Kullanıcıyı sil (Sadece admin)"""
    if user_id == admin['id']:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted", "id": user_id}


@api_router.patch("/admin/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: str, admin: dict = Depends(get_admin_user)):
    """Kullanıcıyı aktif/pasif yap (Sadece admin)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not user['is_active']
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": new_status}})
    
    return {"message": "User status updated", "is_active": new_status}


@api_router.get("/")
async def root():
    return {"message": "IZE Case Resolver API", "version": "1.0"}


@api_router.post("/warranty-rules", response_model=WarrantyRule)
async def create_warranty_rule(rule: WarrantyRuleCreate, admin: dict = Depends(get_admin_user)):
    """Yeni garanti kuralı ekler (Sadece admin)"""
    rule_dict = rule.model_dump()
    rule_obj = WarrantyRule(**rule_dict)
    
    doc = rule_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.warranty_rules.insert_one(doc)
    return rule_obj


@api_router.get("/warranty-rules", response_model=List[WarrantyRule])
async def get_warranty_rules():
    """Tüm garanti kurallarını getirir"""
    rules = await db.warranty_rules.find({}, {"_id": 0}).to_list(1000)
    
    for rule in rules:
        if isinstance(rule['created_at'], str):
            rule['created_at'] = datetime.fromisoformat(rule['created_at'])
    
    return rules


@api_router.delete("/warranty-rules/{rule_id}")
async def delete_warranty_rule(rule_id: str, admin: dict = Depends(get_admin_user)):
    """Garanti kuralını siler (Sadece admin)"""
    result = await db.warranty_rules.delete_one({"id": rule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    return {"message": "Kural silindi", "id": rule_id}


@api_router.post("/analyze", response_model=IZECase)
async def analyze_ize_pdf(file: UploadFile = File(...), current_user: dict = Depends(get_current_active_user)):
    """IZE PDF dosyasını analiz eder (Authentication gerekli)"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyası yükleyebilirsiniz")
    
    # PDF'i oku
    pdf_content = await file.read()
    
    # Metni çıkar
    logger.info(f"PDF okunuyor: {file.filename} (User: {current_user['email']})")
    extracted_text = extract_text_from_pdf(pdf_content)
    
    if not extracted_text or len(extracted_text) < 50:
        raise HTTPException(status_code=400, detail="PDF'den yeterli metin çıkarılamadı")
    
    # Garanti kurallarını al
    warranty_rules = await get_warranty_rules()
    
    if not warranty_rules:
        logger.warning("Garanti kuralı bulunamadı, varsayılan kurallar kullanılıyor")
        # Varsayılan kural
        warranty_rules = [{
            'rule_version': "1.0",
            'rule_text': "2 yıl içindeki araçlar garanti kapsamındadır. Üretim hatalarından kaynaklanan arızalar garanti kapsamındadır.",
            'keywords': ["garanti", "warranty", "2 yıl", "üretim hatası"]
        }]
    
    # AI ile analiz et
    logger.info("AI analizi başlatılıyor...")
    analysis_result = await analyze_ize_with_ai(extracted_text, warranty_rules)
    
    # IZE Case oluştur
    case_title = f"{analysis_result.get('ize_no', 'N/A')} - {analysis_result.get('company', 'N/A')} - {analysis_result.get('plate', 'N/A')}"
    
    # Tarihten ay ve yıl çıkar
    created_at = datetime.now(timezone.utc)
    
    ize_case = IZECase(
        user_id=current_user['id'],  # Yükleyen kullanıcı
        case_title=case_title,
        ize_no=analysis_result.get('ize_no', 'N/A'),
        company=analysis_result.get('company', 'N/A'),
        plate=analysis_result.get('plate', 'N/A'),
        vin=analysis_result.get('vin', 'N/A'),
        warranty_start_date=analysis_result.get('warranty_start_date'),
        repair_date=analysis_result.get('repair_date'),
        vehicle_age_months=analysis_result.get('vehicle_age_months', 0),
        repair_km=analysis_result.get('repair_km', 0),
        request_type=analysis_result.get('request_type', 'WARRANTY SUPPORT'),
        is_within_2_year_warranty=analysis_result.get('is_within_2_year_warranty', False),
        warranty_decision=analysis_result.get('warranty_decision', 'ADDITIONAL_INFO_REQUIRED'),
        decision_rationale=analysis_result.get('decision_rationale', []),
        failure_complaint=analysis_result.get('failure_complaint', ''),
        failure_cause=analysis_result.get('failure_cause', ''),
        operations_performed=analysis_result.get('operations_performed', []),
        parts_replaced=analysis_result.get('parts_replaced', []),
        repair_process_summary=analysis_result.get('repair_process_summary', ''),
        email_subject=analysis_result.get('email_subject', ''),
        email_body=analysis_result.get('email_body', ''),
        pdf_file_name=file.filename,
        extracted_text=extracted_text[:2000],  # İlk 2000 karakter
        binder_version_used=warranty_rules[0]['rule_version'] if warranty_rules else "default",
        month=created_at.month,
        year=created_at.year
    )
    
    # Veritabanına kaydet
    doc = ize_case.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.ize_cases.insert_one(doc)
    logger.info(f"IZE Case kaydedildi: {ize_case.id}")
    
    return ize_case


@api_router.get("/cases", response_model=List[IZECaseResponse])
async def get_all_cases(current_user: dict = Depends(get_current_active_user)):
    """IZE analiz sonuçlarını getirir (Kullanıcıya göre filtrelenir)"""
    # Admin tüm case'leri görebilir, user sadece kendisininkini
    if current_user['role'] == 'admin':
        query = {}
    else:
        query = {"user_id": current_user['id']}
    
    cases = await db.ize_cases.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for case in cases:
        if isinstance(case['created_at'], str):
            case['created_at'] = datetime.fromisoformat(case['created_at'])
    
    # Sadece özet bilgileri döndür
    response = [
        IZECaseResponse(
            id=case['id'],
            case_title=case['case_title'],
            ize_no=case['ize_no'],
            company=case['company'],
            warranty_decision=case['warranty_decision'],
            created_at=case['created_at']
        )
        for case in cases
    ]
    
    return response


@api_router.get("/cases/{case_id}", response_model=IZECase)
async def get_case_by_id(case_id: str, current_user: dict = Depends(get_current_active_user)):
    """Belirli bir IZE case'ini getirir"""
    case = await db.ize_cases.find_one({"id": case_id}, {"_id": 0})
    
    if not case:
        raise HTTPException(status_code=404, detail="Case bulunamadı")
    
    # User sadece kendi case'lerini görebilir, admin hepsini görebilir
    if current_user['role'] != 'admin' and case.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Bu case'i görme yetkiniz yok")
    
    if isinstance(case['created_at'], str):
        case['created_at'] = datetime.fromisoformat(case['created_at'])
    
    return IZECase(**case)


@api_router.delete("/cases/{case_id}")
async def delete_case(case_id: str, current_user: dict = Depends(get_current_active_user)):
    """IZE case'ini siler"""
    case = await db.ize_cases.find_one({"id": case_id})
    
    if not case:
        raise HTTPException(status_code=404, detail="Case bulunamadı")
    
    # User sadece kendi case'lerini silebilir, admin hepsini silebilir
    if current_user['role'] != 'admin' and case.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Bu case'i silme yetkiniz yok")
    
    result = await db.ize_cases.delete_one({"id": case_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Case bulunamadı")
    return {"message": "Case silindi", "id": case_id}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],


)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
