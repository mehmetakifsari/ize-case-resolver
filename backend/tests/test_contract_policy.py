import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.ai_analyzer import _enforce_contract_policy


def test_damage_case_disables_contract_coverage():
    payload = {
        "is_within_2_year_warranty": False,
        "has_active_contract": True,
        "contract_package_name": "PERFORMANCE REFERENCE",
        "contract_decision": "CONTRACT_COVERED",
        "contract_covered_parts": ["Turbo"],
        "failure_cause": "Original: External damage on turbo housing | TR: Turbo gövdesinde dış hasar",
    }

    normalized = _enforce_contract_policy(payload, "Kaza sonrası hasar tespiti")

    assert normalized["has_active_contract"] is False
    assert normalized["contract_package_name"] is None
    assert normalized["contract_decision"] == "NO_CONTRACT_COVERAGE"
    assert normalized["contract_covered_parts"] == []


def test_within_base_warranty_disables_contract_coverage():
    payload = {
        "is_within_2_year_warranty": True,
        "has_active_contract": True,
        "contract_package_name": "PERFORMANCE REFERENCE STANDARD",
        "contract_decision": "CONTRACT_COVERED",
        "contract_covered_parts": ["Enjektör"],
    }

    normalized = _enforce_contract_policy(payload, "")

    assert normalized["has_active_contract"] is False
    assert normalized["contract_package_name"] is None
    assert normalized["contract_decision"] == "NO_CONTRACT_COVERAGE"
    assert normalized["contract_covered_parts"] == []