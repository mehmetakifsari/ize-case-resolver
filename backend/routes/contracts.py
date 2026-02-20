from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from database import db
from models.contract import ContractRule, ContractRuleCreate, ContractRuleUpdate
from routes.auth import get_admin_user

router = APIRouter(prefix="/contract-rules", tags=["Contract Rules"])


@router.post("", response_model=ContractRule)
async def create_contract_rule(rule: ContractRuleCreate, admin: dict = Depends(get_admin_user)):
    package_name = rule.package_name.strip()
    if not package_name:
        raise HTTPException(status_code=400, detail="Paket adı boş olamaz")

    rule_obj = ContractRule(
        package_name=package_name,
        items=[item.strip() for item in rule.items if item.strip()],
        keywords=[keyword.strip() for keyword in rule.keywords if keyword.strip()],
    )

    doc = rule_obj.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.contract_rules.insert_one(doc)
    return rule_obj


@router.get("", response_model=List[ContractRule])
async def get_contract_rules(active_only: bool = False):
    query = {"is_active": True} if active_only else {}
    rules = await db.contract_rules.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)

    for rule in rules:
        if isinstance(rule.get("created_at"), str):
            rule["created_at"] = datetime.fromisoformat(rule["created_at"])

    return rules


@router.patch("/{rule_id}/toggle-active")
async def toggle_contract_rule_active(rule_id: str, admin: dict = Depends(get_admin_user)):
    rule = await db.contract_rules.find_one({"id": rule_id})
    if not rule:
        raise HTTPException(status_code=404, detail="Kontrat kuralı bulunamadı")

    new_status = not rule.get("is_active", True)
    await db.contract_rules.update_one({"id": rule_id}, {"$set": {"is_active": new_status}})
    return {"message": "Kontrat kuralı güncellendi", "is_active": new_status}


@router.put("/{rule_id}")
async def update_contract_rule(rule_id: str, rule_update: ContractRuleUpdate, admin: dict = Depends(get_admin_user)):
    rule = await db.contract_rules.find_one({"id": rule_id})
    if not rule:
        raise HTTPException(status_code=404, detail="Kontrat kuralı bulunamadı")

    update_data = rule_update.model_dump(exclude_unset=True)
    if "package_name" in update_data:
        update_data["package_name"] = update_data["package_name"].strip()

    if "items" in update_data:
        update_data["items"] = [item.strip() for item in update_data["items"] if item.strip()]
    if "keywords" in update_data:
        update_data["keywords"] = [item.strip() for item in update_data["keywords"] if item.strip()]

    if update_data:
        await db.contract_rules.update_one({"id": rule_id}, {"$set": update_data})

    updated_rule = await db.contract_rules.find_one({"id": rule_id}, {"_id": 0})
    return {"message": "Kontrat kuralı güncellendi", "rule": updated_rule}


@router.delete("/{rule_id}")
async def delete_contract_rule(rule_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.contract_rules.delete_one({"id": rule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kontrat kuralı bulunamadı")
    return {"message": "Kontrat kuralı silindi", "id": rule_id}
