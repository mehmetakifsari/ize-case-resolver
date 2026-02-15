"""
Stripe Ödeme Servisi
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout,
    CheckoutSessionResponse,
    CheckoutStatusResponse,
    CheckoutSessionRequest
)

logger = logging.getLogger(__name__)


class StripePaymentService:
    """Stripe ödeme servisi"""
    
    def __init__(self, webhook_url: str):
        api_key = os.environ.get('STRIPE_API_KEY')
        if not api_key:
            raise ValueError("STRIPE_API_KEY environment variable not set")
        
        self.stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
        logger.info("Stripe payment service initialized")
    
    async def create_checkout_session(
        self,
        amount: float,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> CheckoutSessionResponse:
        """
        Checkout session oluştur
        
        Args:
            amount: Ödeme tutarı (float olmalı, örn: 100.00)
            currency: Para birimi (usd, eur, try)
            success_url: Başarılı ödeme sonrası yönlendirme URL'i
            cancel_url: İptal durumunda yönlendirme URL'i
            metadata: Ek metadata
            
        Returns:
            CheckoutSessionResponse: Checkout session bilgileri
        """
        try:
            # Para birimi küçük harfe çevir (Stripe için)
            currency_lower = currency.lower()
            if currency_lower == "try":
                currency_lower = "usd"  # Stripe TRY desteklemiyor, USD kullan
            
            checkout_request = CheckoutSessionRequest(
                amount=float(amount),
                currency=currency_lower,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {}
            )
            
            session = await self.stripe_checkout.create_checkout_session(checkout_request)
            logger.info(f"Stripe checkout session created: {session.session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Stripe checkout session creation failed: {str(e)}")
            raise
    
    async def get_checkout_status(self, session_id: str) -> CheckoutStatusResponse:
        """
        Checkout session durumunu kontrol et
        
        Args:
            session_id: Stripe session ID
            
        Returns:
            CheckoutStatusResponse: Ödeme durumu
        """
        try:
            status = await self.stripe_checkout.get_checkout_status(session_id)
            logger.info(f"Stripe checkout status for {session_id}: {status.payment_status}")
            return status
        except Exception as e:
            logger.error(f"Stripe status check failed: {str(e)}")
            raise
    
    async def handle_webhook(self, body: bytes, signature: str) -> Dict[str, Any]:
        """
        Stripe webhook'u işle
        
        Args:
            body: Webhook body (bytes)
            signature: Stripe-Signature header
            
        Returns:
            Webhook event bilgileri
        """
        try:
            webhook_response = await self.stripe_checkout.handle_webhook(body, signature)
            logger.info(f"Stripe webhook processed: {webhook_response.event_type}")
            return {
                "event_type": webhook_response.event_type,
                "event_id": webhook_response.event_id,
                "session_id": webhook_response.session_id,
                "payment_status": webhook_response.payment_status,
                "metadata": webhook_response.metadata
            }
        except Exception as e:
            logger.error(f"Stripe webhook processing failed: {str(e)}")
            raise
