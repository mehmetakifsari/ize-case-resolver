from .user import User, UserInDB, UserCreate, UserLogin, UserUpdate, Token
from .case import IZECase, IZECaseResponse, PartReplaced
from .warranty import WarrantyRule, WarrantyRuleCreate
from .settings import APISettings, APISettingsUpdate

# Şube listesi
BRANCHES = ["Bursa", "İzmit", "Orhanlı", "Hadımköy", "Keşan"]

__all__ = [
    "User", "UserInDB", "UserCreate", "UserLogin", "UserUpdate", "Token",
    "IZECase", "IZECaseResponse", "PartReplaced",
    "WarrantyRule", "WarrantyRuleCreate",
    "APISettings", "APISettingsUpdate",
    "BRANCHES"
]
