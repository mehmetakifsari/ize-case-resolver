from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
import logging
import uuid
from models.case import IZECase, IZECaseResponse
from models.user import BRANCHES
from services.pdf_processor import extract_text_from_pdf
from services.ai_analyzer import analyze_ize_with_ai
from services.email import send_analysis_email, generate_email_subject, generate_email_body
from routes.auth import get_current_active_user
from database import db

router = APIRouter(prefix="/cases", tags=["Cases"])
logger = logging.getLogger(__name__)

PDF_UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "ize_pdfs"
PDF_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/analyze", response_model=IZECase)
async def analyze_ize_pdf(
    file: UploadFile = File(...), 
    branch: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """IZE PDF dosyasını analiz eder (Authentication gerekli)"""
    
    # Kredi kontrolü (Admin ve sınırsız kredi olanlar muaf)
    has_unlimited = current_user.get('has_unlimited_credits', False)
    is_admin = current_user['role'] == 'admin'
    
    if not is_admin and not has_unlimited:
        if current_user.get('free_analyses_remaining', 0) <= 0:
            raise HTTPException(
                status_code=403, 
                detail="Analiz krediniz bitti. Lütfen kredi satın alın veya yönetici ile iletişime geçin."
            )
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyası yükleyebilirsiniz")
    
    # Şube kontrolü - veritabanından şubeleri al
    user_branch = branch or current_user.get('branch', '')
    # Şube validasyonunu kaldırdık - dinamik şubeler kullanılıyor
    
    # PDF'i oku
    pdf_content = await file.read()

    pdf_storage_name = f"{uuid.uuid4().hex}.pdf"
    pdf_storage_path = PDF_UPLOAD_DIR / pdf_storage_name
    with open(pdf_storage_path, "wb") as pdf_handle:
        pdf_handle.write(pdf_content)
    
    # Metni çıkar
    logger.info(f"PDF okunuyor: {file.filename} (User: {current_user['email']})")
    extracted_text = extract_text_from_pdf(pdf_content)
    
    if not extracted_text or len(extracted_text) < 50:
        raise HTTPException(status_code=400, detail="PDF'den yeterli metin çıkarılamadı")
    
    # Garanti kurallarını al
    warranty_rules = await db.warranty_rules.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    if not warranty_rules:
        logger.warning("Garanti kuralı bulunamadı, varsayılan kurallar kullanılıyor")
        warranty_rules = [{
            'rule_version': "1.0",
            'rule_text': "2 yıl içindeki araçlar garanti kapsamındadır. Üretim hatalarından kaynaklanan arızalar garanti kapsamındadır.",
            'keywords': ["garanti", "warranty", "2 yıl", "üretim hatası"]
        }]

    contract_rules = await db.contract_rules.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)    
    
    # AI ile analiz et
    logger.info("AI analizi başlatılıyor...")
    
    # Panel'deki API ayarlarını al
    api_settings = await db.api_settings.find_one({"id": "api_settings"}, {"_id": 0})
    
    analysis_result = await analyze_ize_with_ai(extracted_text, warranty_rules, contract_rules, api_settings)
    analysis_result["email_subject"] = generate_email_subject(analysis_result, "tr")
    analysis_result["email_body"] = generate_email_body(analysis_result, "tr")
    
    # IZE Case oluştur
    case_title = f"{analysis_result.get('ize_no', 'N/A')} - {analysis_result.get('company', 'N/A')} - {analysis_result.get('plate', 'N/A')}"
    
    # Tarihten ay ve yıl çıkar
    created_at = datetime.now(timezone.utc)
    
    ize_case = IZECase(
        user_id=current_user['id'],
        branch=user_branch,
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
        has_active_contract=analysis_result.get('has_active_contract', False),
        contract_package_name=analysis_result.get('contract_package_name'),
        contract_decision=analysis_result.get('contract_decision', 'NO_CONTRACT_COVERAGE'),
        contract_covered_parts=analysis_result.get('contract_covered_parts', []),
        failure_complaint=analysis_result.get('failure_complaint', ''),
        failure_cause=analysis_result.get('failure_cause', ''),
        operations_performed=analysis_result.get('operations_performed', []),
        parts_replaced=analysis_result.get('parts_replaced', []),
        repair_process_summary=analysis_result.get('repair_process_summary', ''),
        email_subject=analysis_result.get('email_subject', ''),
        email_body=analysis_result.get('email_body', ''),
        pdf_file_name=file.filename,
        pdf_storage_name=pdf_storage_name,
        extracted_text=extracted_text[:2000],
        binder_version_used=warranty_rules[0].get('rule_version', 'default') if warranty_rules else "default",
        month=created_at.month,
        year=created_at.year
    )
    
    # Veritabanına kaydet
    doc = ize_case.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.ize_cases.insert_one(doc)
    logger.info(f"IZE Case kaydedildi: {ize_case.id}")
    
    # Krediyi azalt (Admin hariç)
    if current_user['role'] != 'admin':
        await db.users.update_one(
            {"id": current_user['id']},
            {
                "$inc": {
                    "free_analyses_remaining": -1,
                    "total_analyses": 1
                }
            }
        )
        logger.info(f"Kullanıcı kredisi güncellendi: {current_user['email']}")
    
    # E-posta gönder (arka planda)
    try:
        email_result = await send_analysis_email(
            to_email=current_user['email'],
            case_data=analysis_result,
            attachment_bytes=pdf_content,
            attachment_filename=file.filename,
            language="tr"
        )
        if email_result.get("success"):
            # E-posta sayacını artır
            await db.users.update_one(
                {"id": current_user['id']},
                {"$inc": {"emails_sent": 1}}
            )
            logger.info(f"E-posta gönderildi: {current_user['email']}")
        else:
            logger.warning(f"E-posta gönderilemedi: {email_result.get('message')}")
    except Exception as e:
        logger.warning(f"E-posta gönderim hatası: {str(e)}")
    
    return ize_case


@router.get("", response_model=List[IZECaseResponse])
async def get_cases(
    branch: Optional[str] = None,
    archived: Optional[bool] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """IZE analiz sonuçlarını getirir (Kullanıcıya göre filtrelenir)"""
    # Admin tüm case'leri görebilir, user sadece kendisininkini
    if current_user['role'] == 'admin':
        query = {}
    else:
        query = {"user_id": current_user['id']}
    
    # Şube filtresi
    if branch:
        query["branch"] = branch
    
    # Arşiv filtresi
    if archived is not None:
        query["is_archived"] = archived
    
    cases = await db.ize_cases.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for case in cases:
        if isinstance(case.get('created_at'), str):
            case['created_at'] = datetime.fromisoformat(case['created_at'])
    
    # Sadece özet bilgileri döndür
    response = [
        IZECaseResponse(
            id=case['id'],
            case_title=case['case_title'],
            ize_no=case['ize_no'],
            company=case['company'],
            warranty_decision=case['warranty_decision'],
            branch=case.get('branch', ''),
            is_archived=case.get('is_archived', False),
            created_at=case['created_at']
        )
        for case in cases
    ]
    
    return response


@router.get("/{case_id}", response_model=IZECase)
async def get_case_by_id(case_id: str, current_user: dict = Depends(get_current_active_user)):
    """Belirli bir IZE case'ini getirir"""
    case = await db.ize_cases.find_one({"id": case_id}, {"_id": 0})
    
    if not case:
        raise HTTPException(status_code=404, detail="Case bulunamadı")
    
    # User sadece kendi case'lerini görebilir, admin hepsini görebilir
    if current_user['role'] != 'admin' and case.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Bu case'i görme yetkiniz yok")
    
    if isinstance(case.get('created_at'), str):
        case['created_at'] = datetime.fromisoformat(case['created_at'])
    
    return IZECase(**case)

@router.get("/{case_id}/pdf")
async def get_case_pdf(case_id: str, current_user: dict = Depends(get_current_active_user)):
    """Yüklenen IZE PDF dosyasını indirir/sekmede açar."""
    case = await db.ize_cases.find_one({"id": case_id}, {"_id": 0})

    if not case:
        raise HTTPException(status_code=404, detail="Case bulunamadı")

    if current_user['role'] != 'admin' and case.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Bu case'i görme yetkiniz yok")

    pdf_storage_name = case.get("pdf_storage_name")
    if not pdf_storage_name:
        raise HTTPException(status_code=404, detail="Bu case için PDF dosyası bulunamadı")

    pdf_path = (PDF_UPLOAD_DIR / pdf_storage_name).resolve()
    if not pdf_path.exists() or pdf_path.parent != PDF_UPLOAD_DIR.resolve():
        raise HTTPException(status_code=404, detail="PDF dosyası sistemde bulunamadı")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=case.get("pdf_file_name") or "ize.pdf",
        headers={"Content-Disposition": f'inline; filename="{case.get("pdf_file_name") or "ize.pdf"}"'}
    )



@router.delete("/{case_id}")
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


@router.patch("/{case_id}/archive")
async def archive_case(case_id: str, current_user: dict = Depends(get_current_active_user)):
    """IZE case'ini arşivler/arşivden çıkarır"""
    case = await db.ize_cases.find_one({"id": case_id})
    
    if not case:
        raise HTTPException(status_code=404, detail="Case bulunamadı")
    
    # User sadece kendi case'lerini arşivleyebilir, admin hepsini arşivleyebilir
    if current_user['role'] != 'admin' and case.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Bu case'i arşivleme yetkiniz yok")
    
    new_status = not case.get('is_archived', False)
    archived_at = datetime.now(timezone.utc).isoformat() if new_status else None
    
    await db.ize_cases.update_one(
        {"id": case_id},
        {"$set": {"is_archived": new_status, "archived_at": archived_at}}
    )
    
    return {"message": "Case arşiv durumu güncellendi", "is_archived": new_status}
