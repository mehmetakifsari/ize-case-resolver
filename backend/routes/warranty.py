from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from models.warranty import WarrantyRule, WarrantyRuleCreate
from routes.auth import get_admin_user
from database import db

router = APIRouter(prefix="/warranty-rules", tags=["Warranty Rules"])


@router.post("", response_model=WarrantyRule)
async def create_warranty_rule(rule: WarrantyRuleCreate, admin: dict = Depends(get_admin_user)):
    """Yeni garanti kuralı ekler (Sadece admin)"""
    rule_dict = rule.model_dump()
    rule_obj = WarrantyRule(**rule_dict)
    
    doc = rule_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.warranty_rules.insert_one(doc)
    return rule_obj


@router.get("", response_model=List[WarrantyRule])
async def get_warranty_rules():
    """Tüm garanti kurallarını getirir"""
    rules = await db.warranty_rules.find({}, {"_id": 0}).to_list(1000)
    
    for rule in rules:
        if isinstance(rule.get('created_at'), str):
            rule['created_at'] = datetime.fromisoformat(rule['created_at'])
    
    return rules


@router.get("/{rule_id}", response_model=WarrantyRule)
async def get_warranty_rule(rule_id: str):
    """Belirli bir garanti kuralını getirir"""
    rule = await db.warranty_rules.find_one({"id": rule_id}, {"_id": 0})
    
    if not rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    if isinstance(rule.get('created_at'), str):
        rule['created_at'] = datetime.fromisoformat(rule['created_at'])
    
    return WarrantyRule(**rule)


@router.delete("/{rule_id}")
async def delete_warranty_rule(rule_id: str, admin: dict = Depends(get_admin_user)):
    """Garanti kuralını siler (Sadece admin)"""
    result = await db.warranty_rules.delete_one({"id": rule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    return {"message": "Kural silindi", "id": rule_id}
