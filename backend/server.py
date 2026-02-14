from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import PyPDF2
import io
from emergentintegrations.llm.chat import LlmChat, UserMessage

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


class IZECase(BaseModel):
    """IZE Case analiz sonuç modeli"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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


class IZECaseResponse(BaseModel):
    """API response modeli"""
    id: str
    case_title: str
    ize_no: str
    company: str
    warranty_decision: str
    created_at: datetime


# ==================== HELPER FUNCTIONS ====================

def extract_text_from_pdf(pdf_file: bytes) -> str:
    """PDF'den metin çıkarır - geliştirilmiş versiyon"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
        text = ""
        total_pages = len(pdf_reader.pages)
        
        logger.info(f"PDF toplam {total_pages} sayfa içeriyor")
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text()
            text += f"\n\n--- SAYFA {page_num} ---\n{page_text}"
            logger.info(f"Sayfa {page_num} işlendi: {len(page_text)} karakter")
        
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
        
        # Analiz mesajı oluştur - Daha detaylı prompt
        prompt = f"""
IZE DOSYASI ANALİZ TALEBİ

--- RENAULT TRUCKS GARANTİ KURALLARI ---
{rules_text}

--- IZE DOSYASI HAM İÇERİK ---
{pdf_text[:12000]}

--- ANALİZ TALİMATLARI ---
1. Yukarıdaki IZE dosyasındaki TÜM bilgileri dikkatle oku
2. Araç bilgilerini çıkar (IZE no, firma, plaka, VIN, tarihler, km)
3. Yapılan TÜM işlemleri detaylıca listele (hiçbirini atlama)
4. Değiştirilen TÜM parçaları belirt (orijinal isim + Türkçe açıklama)
5. Teslimat tarihi ile işlem tarihi arasındaki farkı hesapla
6. Garanti kurallarına göre değerlendirme yap:
   - MHDV: 12 ay temel garanti
   - Powertrain bileşenleri: +12 ay (toplam 24 ay)
   - LCV: 36 ay
7. Garanti dışı parçaları kontrol et (batarya, fren, debriyaj, lastik vb.)
8. Profesyonel ve kibar bir email metni oluştur

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

@api_router.get("/")
async def root():
    return {"message": "IZE Case Resolver API", "version": "1.0"}


@api_router.post("/warranty-rules", response_model=WarrantyRule)
async def create_warranty_rule(rule: WarrantyRuleCreate):
    """Yeni garanti kuralı ekler"""
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
async def delete_warranty_rule(rule_id: str):
    """Garanti kuralını siler"""
    result = await db.warranty_rules.delete_one({"id": rule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    return {"message": "Kural silindi", "id": rule_id}


@api_router.post("/analyze", response_model=IZECase)
async def analyze_ize_pdf(file: UploadFile = File(...)):
    """IZE PDF dosyasını analiz eder"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyası yükleyebilirsiniz")
    
    # PDF'i oku
    pdf_content = await file.read()
    
    # Metni çıkar
    logger.info(f"PDF okunuyor: {file.filename}")
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
    
    ize_case = IZECase(
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
        binder_version_used=warranty_rules[0]['rule_version'] if warranty_rules else "default"
    )
    
    # Veritabanına kaydet
    doc = ize_case.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.ize_cases.insert_one(doc)
    logger.info(f"IZE Case kaydedildi: {ize_case.id}")
    
    return ize_case


@api_router.get("/cases", response_model=List[IZECaseResponse])
async def get_all_cases():
    """Tüm IZE analiz sonuçlarını getirir"""
    cases = await db.ize_cases.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
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
async def get_case_by_id(case_id: str):
    """Belirli bir IZE case'ini getirir"""
    case = await db.ize_cases.find_one({"id": case_id}, {"_id": 0})
    
    if not case:
        raise HTTPException(status_code=404, detail="Case bulunamadı")
    
    if isinstance(case['created_at'], str):
        case['created_at'] = datetime.fromisoformat(case['created_at'])
    
    return IZECase(**case)


@api_router.delete("/cases/{case_id}")
async def delete_case(case_id: str):
    """IZE case'ini siler"""
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
