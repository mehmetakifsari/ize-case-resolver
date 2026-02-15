"""
Ödeme API Route'ları
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from typing import List, Optional
from datetime import datetime, timezone
import logging
import uuid

from models.payment import (
    PaymentMethod, PaymentStatus, Currency, PackageType,
    CreditPackage, SubscriptionPlan, PaymentTransaction, 
    BankTransferSettings, BankAccount,
    CreateCheckoutRequest, CheckoutResponse, BankTransferRequest, PaymentStatusResponse
)
from routes.auth import get_current_active_user, get_admin_user
from database import db

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = logging.getLogger(__name__)


# ==================== SABİT PAKETLER ====================
# Güvenlik için fiyatlar backend'de tanımlanır, frontend'den alınmaz

DEFAULT_CREDIT_PACKAGES = [
    {
        "id": "credit_starter",
        "name": "Başlangıç Paketi",
        "name_en": "Starter Package",
        "description": "Küçük işletmeler için ideal",
        "description_en": "Ideal for small businesses",
        "credits": 10,
        "price_try": 299.0,
        "price_usd": 15.0,
        "price_eur": 14.0,
        "discount_percent": 0,
        "is_popular": False,
        "is_active": True,
        "sort_order": 1
    },
    {
        "id": "credit_pro",
        "name": "Pro Paketi",
        "name_en": "Pro Package",
        "description": "En popüler seçim",
        "description_en": "Most popular choice",
        "credits": 50,
        "price_try": 999.0,
        "price_usd": 49.0,
        "price_eur": 45.0,
        "discount_percent": 20,
        "is_popular": True,
        "is_active": True,
        "sort_order": 2
    },
    {
        "id": "credit_enterprise",
        "name": "Kurumsal Paket",
        "name_en": "Enterprise Package",
        "description": "Büyük ekipler için",
        "description_en": "For large teams",
        "credits": 200,
        "price_try": 2999.0,
        "price_usd": 149.0,
        "price_eur": 139.0,
        "discount_percent": 40,
        "is_popular": False,
        "is_active": True,
        "sort_order": 3
    }
]

DEFAULT_SUBSCRIPTION_PLANS = [
    {
        "id": "sub_starter",
        "name": "Başlangıç",
        "name_en": "Starter",
        "description": "Aylık 20 analiz hakkı",
        "description_en": "20 analyses per month",
        "interval": "monthly",
        "credits_per_month": 20,
        "price_try": 499.0,
        "price_usd": 25.0,
        "price_eur": 23.0,
        "features": ["20 aylık analiz", "E-posta desteği", "Temel raporlama"],
        "features_en": ["20 monthly analyses", "Email support", "Basic reporting"],
        "is_popular": False,
        "is_active": True,
        "sort_order": 1
    },
    {
        "id": "sub_pro",
        "name": "Pro",
        "name_en": "Pro",
        "description": "Aylık 100 analiz hakkı",
        "description_en": "100 analyses per month",
        "interval": "monthly",
        "credits_per_month": 100,
        "price_try": 1499.0,
        "price_usd": 75.0,
        "price_eur": 69.0,
        "features": ["100 aylık analiz", "Öncelikli destek", "Gelişmiş raporlama", "API erişimi"],
        "features_en": ["100 monthly analyses", "Priority support", "Advanced reporting", "API access"],
        "is_popular": True,
        "is_active": True,
        "sort_order": 2
    },
    {
        "id": "sub_enterprise",
        "name": "Kurumsal",
        "name_en": "Enterprise",
        "description": "Sınırsız analiz hakkı",
        "description_en": "Unlimited analyses",
        "interval": "monthly",
        "credits_per_month": 9999,
        "price_try": 4999.0,
        "price_usd": 249.0,
        "price_eur": 229.0,
        "features": ["Sınırsız analiz", "7/24 destek", "Özel entegrasyonlar", "Dedicated account manager"],
        "features_en": ["Unlimited analyses", "24/7 support", "Custom integrations", "Dedicated account manager"],
        "is_popular": False,
        "is_active": True,
        "sort_order": 3
    }
]

DEFAULT_BANK_ACCOUNTS = [
    {
        "id": "bank_try",
        "bank_name": "Ziraat Bankası",
        "account_holder": "IZE Case Resolver Ltd. Şti.",
        "iban": "TR00 0000 0000 0000 0000 0000 00",
        "currency": "TRY",
        "is_active": True,
        "sort_order": 1
    },
    {
        "id": "bank_usd",
        "bank_name": "Garanti BBVA",
        "account_holder": "IZE Case Resolver Ltd. Şti.",
        "iban": "TR00 0000 0000 0000 0000 0000 01",
        "currency": "USD",
        "is_active": True,
        "sort_order": 2
    },
    {
        "id": "bank_eur",
        "bank_name": "İş Bankası",
        "account_holder": "IZE Case Resolver Ltd. Şti.",
        "iban": "TR00 0000 0000 0000 0000 0000 02",
        "currency": "EUR",
        "is_active": True,
        "sort_order": 3
    }
]


# ==================== PAKET ENDPOINTLERİ ====================

@router.get("/packages/credits")
async def get_credit_packages():
    """Kredi paketlerini getir (Public)"""
    packages = await db.credit_packages.find({"is_active": True}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    
    if not packages:
        # Varsayılan paketleri döndür
        return DEFAULT_CREDIT_PACKAGES
    
    return packages


@router.get("/packages/subscriptions")
async def get_subscription_plans():
    """Abonelik planlarını getir (Public)"""
    plans = await db.subscription_plans.find({"is_active": True}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    
    if not plans:
        # Varsayılan planları döndür
        return DEFAULT_SUBSCRIPTION_PLANS
    
    return plans


@router.get("/bank-accounts")
async def get_bank_accounts():
    """Banka hesaplarını getir (Public)"""
    settings = await db.bank_transfer_settings.find_one({"id": "bank_transfer_settings"}, {"_id": 0})
    
    if not settings or not settings.get("accounts"):
        return {
            "is_enabled": True,
            "instructions": "Ödemenizi yaptıktan sonra dekont görselini yükleyiniz.",
            "instructions_en": "After making the payment, please upload the receipt.",
            "accounts": DEFAULT_BANK_ACCOUNTS
        }
    
    return settings


# ==================== CHECKOUT ENDPOINTLERİ ====================

@router.post("/checkout/stripe", response_model=CheckoutResponse)
async def create_stripe_checkout(
    request: Request,
    checkout_data: CreateCheckoutRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Stripe checkout session oluştur"""
    from services.stripe_payment import StripePaymentService
    
    try:
        # Paket bilgilerini al
        if checkout_data.package_type == PackageType.CREDIT:
            package = next((p for p in DEFAULT_CREDIT_PACKAGES if p["id"] == checkout_data.package_id), None)
            if not package:
                db_package = await db.credit_packages.find_one({"id": checkout_data.package_id}, {"_id": 0})
                package = db_package
        else:
            package = next((p for p in DEFAULT_SUBSCRIPTION_PLANS if p["id"] == checkout_data.package_id), None)
            if not package:
                db_package = await db.subscription_plans.find_one({"id": checkout_data.package_id}, {"_id": 0})
                package = db_package
        
        if not package:
            raise HTTPException(status_code=404, detail="Paket bulunamadı")
        
        # Fiyatı al (para birimine göre)
        currency = checkout_data.currency.value.lower()
        price_key = f"price_{currency}"
        amount = package.get(price_key)
        
        if not amount:
            raise HTTPException(status_code=400, detail=f"Bu para birimi desteklenmiyor: {currency}")
        
        # URL'leri oluştur
        origin_url = checkout_data.origin_url.rstrip('/')
        success_url = f"{origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin_url}/payment/cancel"
        
        # Webhook URL
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        
        # Transaction ID oluştur
        transaction_id = str(uuid.uuid4())
        
        # Metadata
        metadata = {
            "transaction_id": transaction_id,
            "user_id": current_user["id"],
            "user_email": current_user["email"],
            "package_type": checkout_data.package_type.value,
            "package_id": checkout_data.package_id,
            "package_name": package.get("name", ""),
            "credits": str(package.get("credits", package.get("credits_per_month", 0)))
        }
        
        # Stripe servisi
        stripe_service = StripePaymentService(webhook_url=webhook_url)
        
        # Checkout session oluştur
        session = await stripe_service.create_checkout_session(
            amount=float(amount),
            currency=currency if currency != "try" else "usd",  # Stripe TRY desteklemiyor
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        # Transaction kaydı oluştur
        transaction = {
            "id": transaction_id,
            "user_id": current_user["id"],
            "user_email": current_user["email"],
            "package_type": checkout_data.package_type.value,
            "package_id": checkout_data.package_id,
            "package_name": package.get("name", ""),
            "payment_method": PaymentMethod.STRIPE.value,
            "amount": float(amount),
            "currency": checkout_data.currency.value,
            "status": PaymentStatus.PENDING.value,
            "stripe_session_id": session.session_id,
            "credits_to_add": package.get("credits", package.get("credits_per_month", 0)),
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payment_transactions.insert_one(transaction)
        logger.info(f"Stripe checkout created: {session.session_id} for user {current_user['email']}")
        
        return CheckoutResponse(
            success=True,
            checkout_url=session.url,
            session_id=session.session_id,
            transaction_id=transaction_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe checkout failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ödeme işlemi başlatılamadı: {str(e)}")


@router.post("/checkout/iyzico", response_model=CheckoutResponse)
async def create_iyzico_checkout(
    request: Request,
    checkout_data: CreateCheckoutRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """iyzico checkout form oluştur"""
    from services.iyzico_payment import IyzicoPaymentService
    
    try:
        # Paket bilgilerini al
        if checkout_data.package_type == PackageType.CREDIT:
            package = next((p for p in DEFAULT_CREDIT_PACKAGES if p["id"] == checkout_data.package_id), None)
            if not package:
                db_package = await db.credit_packages.find_one({"id": checkout_data.package_id}, {"_id": 0})
                package = db_package
        else:
            package = next((p for p in DEFAULT_SUBSCRIPTION_PLANS if p["id"] == checkout_data.package_id), None)
            if not package:
                db_package = await db.subscription_plans.find_one({"id": checkout_data.package_id}, {"_id": 0})
                package = db_package
        
        if not package:
            raise HTTPException(status_code=404, detail="Paket bulunamadı")
        
        # Fiyatı al
        currency = checkout_data.currency.value
        price_key = f"price_{currency.lower()}"
        amount = package.get(price_key)
        
        if not amount:
            raise HTTPException(status_code=400, detail=f"Bu para birimi desteklenmiyor: {currency}")
        
        # Transaction ID oluştur
        transaction_id = str(uuid.uuid4())
        conversation_id = transaction_id[:20]
        
        # URL'leri oluştur
        origin_url = checkout_data.origin_url.rstrip('/')
        host_url = str(request.base_url).rstrip('/')
        callback_url = f"{host_url}/api/payments/iyzico/callback?transaction_id={transaction_id}&origin={origin_url}"
        
        # Kullanıcı bilgileri
        name_parts = current_user.get("full_name", "Test User").split(" ", 1)
        buyer = {
            "id": current_user["id"],
            "name": name_parts[0],
            "surname": name_parts[1] if len(name_parts) > 1 else name_parts[0],
            "email": current_user["email"],
            "gsm_number": current_user.get("phone_number", "+905350000000") or "+905350000000",
            "identity_number": "11111111111",
            "address": "Turkey",
            "city": current_user.get("branch", "Istanbul") or "Istanbul",
            "country": "Turkey",
            "zip_code": "34000",
            "ip": request.client.host if request.client else "127.0.0.1"
        }
        
        address = {
            "contact_name": current_user.get("full_name", "Test User"),
            "city": current_user.get("branch", "Istanbul") or "Istanbul",
            "country": "Turkey",
            "address": "Turkey",
            "zip_code": "34000"
        }
        
        basket_items = [{
            "id": checkout_data.package_id,
            "name": package.get("name", "Kredi Paketi"),
            "category1": "Digital",
            "category2": "Credit",
            "item_type": "VIRTUAL",
            "price": amount
        }]
        
        # iyzico servisi
        iyzico_service = IyzicoPaymentService()
        
        # Checkout form oluştur
        result = iyzico_service.create_checkout_form(
            price=float(amount),
            paid_price=float(amount),
            currency=currency,
            basket_id=transaction_id,
            buyer=buyer,
            billing_address=address,
            shipping_address=address,
            basket_items=basket_items,
            callback_url=callback_url,
            conversation_id=conversation_id
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("errorMessage", "iyzico hatası"))
        
        # Transaction kaydı oluştur
        transaction = {
            "id": transaction_id,
            "user_id": current_user["id"],
            "user_email": current_user["email"],
            "package_type": checkout_data.package_type.value,
            "package_id": checkout_data.package_id,
            "package_name": package.get("name", ""),
            "payment_method": PaymentMethod.IYZICO.value,
            "amount": float(amount),
            "currency": currency,
            "status": PaymentStatus.PENDING.value,
            "iyzico_conversation_id": conversation_id,
            "credits_to_add": package.get("credits", package.get("credits_per_month", 0)),
            "metadata": {
                "iyzico_token": result.get("token"),
                "checkout_form_content": result.get("checkoutFormContent")
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payment_transactions.insert_one(transaction)
        logger.info(f"iyzico checkout created: {transaction_id} for user {current_user['email']}")
        
        return CheckoutResponse(
            success=True,
            checkout_url=result.get("paymentPageUrl"),
            session_id=result.get("token"),
            transaction_id=transaction_id,
            message=result.get("checkoutFormContent")  # HTML içerik
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"iyzico checkout failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ödeme işlemi başlatılamadı: {str(e)}")


@router.get("/iyzico/callback")
async def iyzico_callback(
    request: Request,
    transaction_id: str,
    origin: str,
    token: Optional[str] = None
):
    """iyzico callback endpoint"""
    from fastapi.responses import RedirectResponse
    from services.iyzico_payment import IyzicoPaymentService
    
    try:
        # Transaction'ı bul
        transaction = await db.payment_transactions.find_one({"id": transaction_id}, {"_id": 0})
        
        if not transaction:
            return RedirectResponse(url=f"{origin}/payment/error?message=Transaction not found")
        
        # Token'ı al
        iyzico_token = token or transaction.get("metadata", {}).get("iyzico_token")
        
        if not iyzico_token:
            return RedirectResponse(url=f"{origin}/payment/error?message=Token not found")
        
        # iyzico sonucunu al
        iyzico_service = IyzicoPaymentService()
        result = iyzico_service.retrieve_checkout_form(iyzico_token)
        
        if result.get("paymentStatus") == "SUCCESS":
            # Başarılı ödeme
            await db.payment_transactions.update_one(
                {"id": transaction_id},
                {
                    "$set": {
                        "status": PaymentStatus.COMPLETED.value,
                        "iyzico_payment_id": result.get("paymentId"),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            # Kullanıcıya kredi ekle
            credits_to_add = transaction.get("credits_to_add", 0)
            if credits_to_add > 0:
                await db.users.update_one(
                    {"id": transaction["user_id"]},
                    {"$inc": {"free_analyses_remaining": credits_to_add}}
                )
                logger.info(f"Added {credits_to_add} credits to user {transaction['user_email']}")
            
            return RedirectResponse(url=f"{origin}/payment/success?transaction_id={transaction_id}")
        else:
            # Başarısız ödeme
            await db.payment_transactions.update_one(
                {"id": transaction_id},
                {
                    "$set": {
                        "status": PaymentStatus.FAILED.value,
                        "error_message": result.get("errorMessage", "Ödeme başarısız"),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            return RedirectResponse(url=f"{origin}/payment/error?message={result.get('errorMessage', 'Ödeme başarısız')}")
        
    except Exception as e:
        logger.error(f"iyzico callback error: {str(e)}")
        return RedirectResponse(url=f"{origin}/payment/error?message=Bir hata oluştu")


# ==================== HAVALE/EFT ====================

@router.post("/checkout/bank-transfer", response_model=CheckoutResponse)
async def create_bank_transfer(
    transfer_data: BankTransferRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Havale/EFT ile ödeme kaydı oluştur"""
    try:
        # Paket bilgilerini al
        if transfer_data.package_type == PackageType.CREDIT:
            package = next((p for p in DEFAULT_CREDIT_PACKAGES if p["id"] == transfer_data.package_id), None)
            if not package:
                db_package = await db.credit_packages.find_one({"id": transfer_data.package_id}, {"_id": 0})
                package = db_package
        else:
            package = next((p for p in DEFAULT_SUBSCRIPTION_PLANS if p["id"] == transfer_data.package_id), None)
            if not package:
                db_package = await db.subscription_plans.find_one({"id": transfer_data.package_id}, {"_id": 0})
                package = db_package
        
        if not package:
            raise HTTPException(status_code=404, detail="Paket bulunamadı")
        
        # Fiyatı al
        currency = transfer_data.currency.value
        price_key = f"price_{currency.lower()}"
        amount = package.get(price_key)
        
        if not amount:
            raise HTTPException(status_code=400, detail=f"Bu para birimi desteklenmiyor: {currency}")
        
        # Transaction ID oluştur
        transaction_id = str(uuid.uuid4())
        
        # Transaction kaydı oluştur
        transaction = {
            "id": transaction_id,
            "user_id": current_user["id"],
            "user_email": current_user["email"],
            "package_type": transfer_data.package_type.value,
            "package_id": transfer_data.package_id,
            "package_name": package.get("name", ""),
            "payment_method": PaymentMethod.BANK_TRANSFER.value,
            "amount": float(amount),
            "currency": currency,
            "status": PaymentStatus.PENDING.value,
            "bank_reference": transfer_data.transfer_reference,
            "bank_transfer_proof": transfer_data.transfer_proof_url,
            "credits_to_add": package.get("credits", package.get("credits_per_month", 0)),
            "metadata": {
                "bank_account_id": transfer_data.bank_account_id
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payment_transactions.insert_one(transaction)
        logger.info(f"Bank transfer request created: {transaction_id} for user {current_user['email']}")
        
        return CheckoutResponse(
            success=True,
            transaction_id=transaction_id,
            message="Havale/EFT talebiniz alındı. Onaylandığında kredileriniz hesabınıza eklenecektir."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bank transfer creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"İşlem oluşturulamadı: {str(e)}")


# ==================== DURUM KONTROLÜ ====================

@router.get("/status/{session_id}")
async def get_payment_status(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Ödeme durumunu kontrol et (Stripe session_id veya transaction_id ile)"""
    try:
        # Önce transaction_id olarak ara
        transaction = await db.payment_transactions.find_one(
            {"id": session_id, "user_id": current_user["id"]},
            {"_id": 0}
        )
        
        # Bulunamadıysa stripe_session_id olarak ara
        if not transaction:
            transaction = await db.payment_transactions.find_one(
                {"stripe_session_id": session_id, "user_id": current_user["id"]},
                {"_id": 0}
            )
        
        if not transaction:
            raise HTTPException(status_code=404, detail="İşlem bulunamadı")
        
        # Stripe ise durumu güncelle
        if transaction.get("payment_method") == PaymentMethod.STRIPE.value and transaction.get("status") == PaymentStatus.PENDING.value:
            from services.stripe_payment import StripePaymentService
            
            try:
                host_url = "https://example.com"  # Sadece status için gerekli değil
                stripe_service = StripePaymentService(webhook_url=f"{host_url}/api/webhook/stripe")
                
                stripe_session_id = transaction.get("stripe_session_id")
                if stripe_session_id:
                    status = await stripe_service.get_checkout_status(stripe_session_id)
                    
                    if status.payment_status == "paid":
                        # Başarılı ödeme
                        await db.payment_transactions.update_one(
                            {"id": transaction["id"]},
                            {
                                "$set": {
                                    "status": PaymentStatus.COMPLETED.value,
                                    "updated_at": datetime.now(timezone.utc).isoformat(),
                                    "completed_at": datetime.now(timezone.utc).isoformat()
                                }
                            }
                        )
                        
                        # Kullanıcıya kredi ekle (sadece bir kez)
                        credits_to_add = transaction.get("credits_to_add", 0)
                        if credits_to_add > 0:
                            # Daha önce eklenmemişse ekle
                            existing = await db.payment_transactions.find_one(
                                {"id": transaction["id"], "credits_added": True}
                            )
                            if not existing:
                                await db.users.update_one(
                                    {"id": transaction["user_id"]},
                                    {"$inc": {"free_analyses_remaining": credits_to_add}}
                                )
                                await db.payment_transactions.update_one(
                                    {"id": transaction["id"]},
                                    {"$set": {"credits_added": True}}
                                )
                                logger.info(f"Added {credits_to_add} credits to user {transaction['user_email']}")
                        
                        transaction["status"] = PaymentStatus.COMPLETED.value
                        
                    elif status.status == "expired":
                        await db.payment_transactions.update_one(
                            {"id": transaction["id"]},
                            {
                                "$set": {
                                    "status": PaymentStatus.CANCELLED.value,
                                    "updated_at": datetime.now(timezone.utc).isoformat()
                                }
                            }
                        )
                        transaction["status"] = PaymentStatus.CANCELLED.value
                        
            except Exception as e:
                logger.warning(f"Could not check Stripe status: {str(e)}")
        
        return PaymentStatusResponse(
            transaction_id=transaction["id"],
            status=PaymentStatus(transaction["status"]),
            payment_status=transaction["status"],
            amount=transaction["amount"],
            currency=transaction["currency"],
            credits_added=transaction.get("credits_to_add", 0) if transaction["status"] == PaymentStatus.COMPLETED.value else 0,
            message=transaction.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Durum kontrolü başarısız: {str(e)}")


@router.get("/transactions")
async def get_user_transactions(
    current_user: dict = Depends(get_current_active_user)
):
    """Kullanıcının ödeme geçmişini getir"""
    transactions = await db.payment_transactions.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return transactions


# ==================== ADMİN ENDPOINTLERİ ====================

@router.get("/admin/transactions")
async def get_all_transactions(
    status: Optional[str] = None,
    payment_method: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """Tüm ödeme işlemlerini getir (Admin)"""
    query = {}
    
    if status:
        query["status"] = status
    if payment_method:
        query["payment_method"] = payment_method
    
    transactions = await db.payment_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    return transactions


@router.patch("/admin/transactions/{transaction_id}/approve")
async def approve_bank_transfer(
    transaction_id: str,
    admin: dict = Depends(get_admin_user)
):
    """Havale/EFT ödemesini onayla (Admin)"""
    transaction = await db.payment_transactions.find_one({"id": transaction_id}, {"_id": 0})
    
    if not transaction:
        raise HTTPException(status_code=404, detail="İşlem bulunamadı")
    
    if transaction.get("payment_method") != PaymentMethod.BANK_TRANSFER.value:
        raise HTTPException(status_code=400, detail="Bu işlem havale/EFT değil")
    
    if transaction.get("status") != PaymentStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Bu işlem zaten işlenmiş")
    
    # İşlemi onayla
    await db.payment_transactions.update_one(
        {"id": transaction_id},
        {
            "$set": {
                "status": PaymentStatus.COMPLETED.value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Kullanıcıya kredi ekle
    credits_to_add = transaction.get("credits_to_add", 0)
    if credits_to_add > 0:
        await db.users.update_one(
            {"id": transaction["user_id"]},
            {"$inc": {"free_analyses_remaining": credits_to_add}}
        )
        logger.info(f"Admin approved bank transfer: {transaction_id}, added {credits_to_add} credits to {transaction['user_email']}")
    
    return {"message": "Ödeme onaylandı ve krediler eklendi", "credits_added": credits_to_add}


@router.patch("/admin/transactions/{transaction_id}/reject")
async def reject_bank_transfer(
    transaction_id: str,
    reason: str = Body(..., embed=True),
    admin: dict = Depends(get_admin_user)
):
    """Havale/EFT ödemesini reddet (Admin)"""
    transaction = await db.payment_transactions.find_one({"id": transaction_id})
    
    if not transaction:
        raise HTTPException(status_code=404, detail="İşlem bulunamadı")
    
    if transaction.get("status") != PaymentStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Bu işlem zaten işlenmiş")
    
    # İşlemi reddet
    await db.payment_transactions.update_one(
        {"id": transaction_id},
        {
            "$set": {
                "status": PaymentStatus.FAILED.value,
                "error_message": reason,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    logger.info(f"Admin rejected bank transfer: {transaction_id}, reason: {reason}")
    
    return {"message": "Ödeme reddedildi", "reason": reason}


@router.get("/admin/analytics")
async def get_payment_analytics(admin: dict = Depends(get_admin_user)):
    """Ödeme analitiği (Admin)"""
    # Toplam işlem sayısı
    total_transactions = await db.payment_transactions.count_documents({})
    
    # Durumlara göre
    completed = await db.payment_transactions.count_documents({"status": PaymentStatus.COMPLETED.value})
    pending = await db.payment_transactions.count_documents({"status": PaymentStatus.PENDING.value})
    failed = await db.payment_transactions.count_documents({"status": PaymentStatus.FAILED.value})
    
    # Ödeme yöntemlerine göre
    stripe_count = await db.payment_transactions.count_documents({"payment_method": PaymentMethod.STRIPE.value})
    iyzico_count = await db.payment_transactions.count_documents({"payment_method": PaymentMethod.IYZICO.value})
    bank_count = await db.payment_transactions.count_documents({"payment_method": PaymentMethod.BANK_TRANSFER.value})
    
    # Toplam gelir (tamamlanan işlemler)
    pipeline = [
        {"$match": {"status": PaymentStatus.COMPLETED.value}},
        {"$group": {
            "_id": "$currency",
            "total": {"$sum": "$amount"}
        }}
    ]
    revenue_by_currency = await db.payment_transactions.aggregate(pipeline).to_list(10)
    
    return {
        "total_transactions": total_transactions,
        "by_status": {
            "completed": completed,
            "pending": pending,
            "failed": failed
        },
        "by_method": {
            "stripe": stripe_count,
            "iyzico": iyzico_count,
            "bank_transfer": bank_count
        },
        "revenue_by_currency": {item["_id"]: item["total"] for item in revenue_by_currency}
    }
