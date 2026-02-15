"""
Webhook Endpoint'leri
"""
from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone
import logging

from models.payment import PaymentStatus
from database import db

router = APIRouter(tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook handler"""
    from services.stripe_payment import StripePaymentService
    
    try:
        # Body'yi al
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        if not signature:
            logger.warning("Stripe webhook received without signature")
            raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
        
        # Webhook URL (gerekli ama burada kullanılmıyor)
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        
        # Servisi başlat
        stripe_service = StripePaymentService(webhook_url=webhook_url)
        
        # Webhook'u işle
        event = await stripe_service.handle_webhook(body, signature)
        
        logger.info(f"Stripe webhook received: {event['event_type']}")
        
        # Event tipine göre işle
        if event["event_type"] == "checkout.session.completed":
            session_id = event.get("session_id")
            payment_status = event.get("payment_status")
            metadata = event.get("metadata", {})
            
            if payment_status == "paid":
                # Transaction'ı bul ve güncelle
                transaction = await db.payment_transactions.find_one(
                    {"stripe_session_id": session_id}
                )
                
                if transaction and transaction.get("status") == PaymentStatus.PENDING.value:
                    # Başarılı ödeme
                    await db.payment_transactions.update_one(
                        {"stripe_session_id": session_id},
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
                        existing = await db.payment_transactions.find_one(
                            {"stripe_session_id": session_id, "credits_added": True}
                        )
                        if not existing:
                            await db.users.update_one(
                                {"id": transaction["user_id"]},
                                {"$inc": {"free_analyses_remaining": credits_to_add}}
                            )
                            await db.payment_transactions.update_one(
                                {"stripe_session_id": session_id},
                                {"$set": {"credits_added": True}}
                            )
                            logger.info(f"Webhook: Added {credits_to_add} credits to user {transaction['user_email']}")
        
        elif event["event_type"] == "checkout.session.expired":
            session_id = event.get("session_id")
            
            await db.payment_transactions.update_one(
                {"stripe_session_id": session_id, "status": PaymentStatus.PENDING.value},
                {
                    "$set": {
                        "status": PaymentStatus.CANCELLED.value,
                        "error_message": "Session expired",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            logger.info(f"Stripe session expired: {session_id}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/iyzico")
async def iyzico_webhook(request: Request):
    """iyzico webhook handler"""
    try:
        # Body'yi al
        body = await request.json()
        
        logger.info(f"iyzico webhook received: {body}")
        
        # iyzico webhook yapısı
        payment_id = body.get("paymentId")
        status = body.get("status")
        conversation_id = body.get("paymentConversationId")
        
        if status == "SUCCESS":
            # Transaction'ı bul ve güncelle
            transaction = await db.payment_transactions.find_one(
                {"iyzico_conversation_id": conversation_id}
            )
            
            if transaction and transaction.get("status") == PaymentStatus.PENDING.value:
                await db.payment_transactions.update_one(
                    {"iyzico_conversation_id": conversation_id},
                    {
                        "$set": {
                            "status": PaymentStatus.COMPLETED.value,
                            "iyzico_payment_id": payment_id,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "completed_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                # Kullanıcıya kredi ekle
                credits_to_add = transaction.get("credits_to_add", 0)
                if credits_to_add > 0:
                    existing = await db.payment_transactions.find_one(
                        {"iyzico_conversation_id": conversation_id, "credits_added": True}
                    )
                    if not existing:
                        await db.users.update_one(
                            {"id": transaction["user_id"]},
                            {"$inc": {"free_analyses_remaining": credits_to_add}}
                        )
                        await db.payment_transactions.update_one(
                            {"iyzico_conversation_id": conversation_id},
                            {"$set": {"credits_added": True}}
                        )
                        logger.info(f"iyzico webhook: Added {credits_to_add} credits to user {transaction['user_email']}")
        
        elif status == "FAILURE":
            await db.payment_transactions.update_one(
                {"iyzico_conversation_id": conversation_id, "status": PaymentStatus.PENDING.value},
                {
                    "$set": {
                        "status": PaymentStatus.FAILED.value,
                        "error_message": body.get("errorMessage", "Payment failed"),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"iyzico webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
