from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from typing import List, Optional
from datetime import datetime, timezone
from models.warranty import (
    WarrantyRule,
    WarrantyRuleCreate,
    WarrantyRuleTextCreate,
    WarrantyRuleUpdate,
)
from routes.auth import get_admin_user
from database import db
import pdfplumber
import pytesseract
from PIL import Image
import io
import uuid
import base64

router = APIRouter(prefix="/warranty-rules", tags=["Warranty Rules"])


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """PDF'den metin çıkarır (OCR destekli)"""
    text_content = ""
    
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_content += page_text + "\n"
                
                # Eğer metin çıkarılamadıysa OCR dene
                if not page_text.strip():
                    try:
                        img = page.to_image(resolution=300)
                        pil_image = img.original
                        ocr_text = pytesseract.image_to_string(pil_image, lang='tur+eng')
                        text_content += ocr_text + "\n"
                    except Exception:
                        pass
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF okunamadı: {str(e)}")
    
    return text_content.strip()


@router.post("", response_model=WarrantyRule)
async def create_warranty_rule(rule: WarrantyRuleCreate, admin: dict = Depends(get_admin_user)):
    """Yeni garanti kuralı ekler (Sadece admin)"""
    rule_dict = rule.model_dump()
    rule_obj = WarrantyRule(**rule_dict, source_type="manual")
    
    doc = rule_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.warranty_rules.insert_one(doc)
    return rule_obj


@router.post("/upload-text", response_model=WarrantyRule)
async def upload_warranty_text(rule: WarrantyRuleTextCreate, admin: dict = Depends(get_admin_user)):
    """PDF yerine düz metin garanti kuralı yükler (Sadece admin)."""
    normalized_text = rule.rule_text.strip()
    if not normalized_text:
        raise HTTPException(status_code=400, detail="Kural metni boş olamaz")

    rule_obj = WarrantyRule(
        rule_version=rule.rule_version,
        rule_text=normalized_text,
        keywords=rule.keywords,
        source_type="text",
        source_filename=rule.source_reference,
        is_active=True,
    )

    doc = rule_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()

    await db.warranty_rules.insert_one(doc)
    return rule_obj


@router.post("/upload-pdf")
async def upload_warranty_pdf(
    file: UploadFile = File(...),
    rule_version: str = Form(...),
    keywords: str = Form(default=""),
    admin: dict = Depends(get_admin_user)
):
    """PDF'den garanti kuralı oluşturur (Sadece admin)"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilir")
    
    # PDF'i oku
    file_bytes = await file.read()
    
    # Metin çıkar
    extracted_text = extract_text_from_pdf(file_bytes)
    
    if not extracted_text:
        raise HTTPException(status_code=400, detail="PDF'den metin çıkarılamadı")
    
    # Keywords'leri parse et
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
    
    # Kural oluştur
    rule_obj = WarrantyRule(
        rule_version=rule_version,
        rule_text=extracted_text,
        keywords=keyword_list,
        source_type="pdf",
        source_filename=file.filename,
        is_active=True
    )
    
    doc = rule_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['pdf_binary'] = base64.b64encode(file_bytes).decode('utf-8')

    
    await db.warranty_rules.insert_one(doc)
    
    return {
        "message": "PDF başarıyla yüklendi ve kural oluşturuldu",
        "rule": rule_obj.model_dump(),
        "extracted_chars": len(extracted_text)
    }


@router.get("", response_model=List[WarrantyRule])
async def get_warranty_rules(active_only: bool = False):
    """Tüm garanti kurallarını getirir"""
    query = {"is_active": True} if active_only else {}
    rules = await db.warranty_rules.find(query, {"_id": 0, "pdf_binary": 0}).sort("created_at", -1).to_list(1000)
    
    for rule in rules:
        if isinstance(rule.get('created_at'), str):
            rule['created_at'] = datetime.fromisoformat(rule['created_at'])
        # Eski kayıtlar için varsayılan değerler
        if 'source_type' not in rule:
            rule['source_type'] = 'manual'
        if 'is_active' not in rule:
            rule['is_active'] = True
    
    return rules


@router.get("/{rule_id}", response_model=WarrantyRule)
async def get_warranty_rule(rule_id: str):
    """Belirli bir garanti kuralını getirir"""
    rule = await db.warranty_rules.find_one({"id": rule_id}, {"_id": 0, "pdf_binary": 0})
    
    if not rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    if isinstance(rule.get('created_at'), str):
        rule['created_at'] = datetime.fromisoformat(rule['created_at'])
    
    # Eski kayıtlar için varsayılan değerler
    if 'source_type' not in rule:
        rule['source_type'] = 'manual'
    if 'is_active' not in rule:
        rule['is_active'] = True
    
    return WarrantyRule(**rule)

@router.get("/{rule_id}/pdf")
async def get_warranty_rule_pdf(rule_id: str, admin: dict = Depends(get_admin_user)):
    """PDF olarak yüklenen garanti kuralının orijinal dosyasını döndürür."""
    rule = await db.warranty_rules.find_one(
        {"id": rule_id},
        {"_id": 0, "pdf_binary": 1, "source_filename": 1, "source_type": 1}
    )

    if not rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")

    if rule.get("source_type") != "pdf":
        raise HTTPException(status_code=400, detail="Bu kural PDF kaynağından yüklenmemiş")

    pdf_binary = rule.get("pdf_binary")
    if not pdf_binary:
        raise HTTPException(status_code=404, detail="PDF içeriği bulunamadı")

    try:
        pdf_bytes = base64.b64decode(pdf_binary)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="PDF içeriği çözümlenemedi") from exc

    filename = rule.get("source_filename") or f"warranty-rule-{rule_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )




@router.put("/{rule_id}")
async def update_warranty_rule(rule_id: str, rule_update: WarrantyRuleUpdate, admin: dict = Depends(get_admin_user)):
    """Garanti kuralını günceller (Sadece admin)"""
    rule = await db.warranty_rules.find_one({"id": rule_id})
    
    if not rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    update_data = rule_update.model_dump(exclude_unset=True)
    
    if update_data:
        await db.warranty_rules.update_one({"id": rule_id}, {"$set": update_data})
    
    updated_rule = await db.warranty_rules.find_one({"id": rule_id}, {"_id": 0})
    return {"message": "Kural güncellendi", "rule": updated_rule}


@router.patch("/{rule_id}/toggle-active")
async def toggle_rule_active(rule_id: str, admin: dict = Depends(get_admin_user)):
    """Kuralı aktif/pasif yapar (Sadece admin)"""
    rule = await db.warranty_rules.find_one({"id": rule_id})
    
    if not rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    new_status = not rule.get('is_active', True)
    await db.warranty_rules.update_one({"id": rule_id}, {"$set": {"is_active": new_status}})
    
    return {"message": "Kural durumu güncellendi", "is_active": new_status}


@router.delete("/{rule_id}")
async def delete_warranty_rule(rule_id: str, admin: dict = Depends(get_admin_user)):
    """Garanti kuralını siler (Sadece admin)"""
    result = await db.warranty_rules.delete_one({"id": rule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    return {"message": "Kural silindi", "id": rule_id}
