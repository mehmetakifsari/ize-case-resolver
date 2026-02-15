"""
iyzico Ödeme Servisi
"""
import os
import json
import logging
import time
from typing import Dict, Any, Optional, List
from decimal import Decimal

import iyzipay

logger = logging.getLogger(__name__)


class IyzicoPaymentService:
    """iyzico ödeme servisi"""
    
    def __init__(self):
        self.options = {
            'api_key': os.environ.get('IYZICO_API_KEY'),
            'secret_key': os.environ.get('IYZICO_SECRET_KEY'),
            'base_url': os.environ.get('IYZICO_BASE_URL', 'https://sandbox-api.iyzipay.com')
        }
        
        if not self.options['api_key'] or not self.options['secret_key']:
            raise ValueError("IYZICO_API_KEY and IYZICO_SECRET_KEY environment variables must be set")
        
        logger.info(f"iyzico payment service initialized (base_url: {self.options['base_url']})")
    
    def create_checkout_form(
        self,
        price: float,
        paid_price: float,
        currency: str,
        basket_id: str,
        buyer: Dict[str, Any],
        billing_address: Dict[str, Any],
        shipping_address: Dict[str, Any],
        basket_items: List[Dict[str, Any]],
        callback_url: str,
        conversation_id: Optional[str] = None,
        installment: int = 1
    ) -> Dict[str, Any]:
        """
        iyzico Checkout Form oluştur (3D Secure)
        
        Args:
            price: Toplam tutar
            paid_price: Ödenecek tutar
            currency: Para birimi (TRY, USD, EUR)
            basket_id: Sepet ID
            buyer: Alıcı bilgileri
            billing_address: Fatura adresi
            shipping_address: Teslimat adresi
            basket_items: Sepet içeriği
            callback_url: Ödeme sonucu callback URL
            conversation_id: İşlem ID
            installment: Taksit sayısı
            
        Returns:
            Checkout form bilgileri
        """
        try:
            request = {
                'locale': 'tr',
                'conversationId': conversation_id or str(int(time.time())),
                'price': str(price),
                'paidPrice': str(paid_price),
                'currency': currency,
                'basketId': basket_id,
                'paymentGroup': 'PRODUCT',
                'callbackUrl': callback_url,
                'enabledInstallments': [1, 2, 3, 6, 9] if installment > 1 else [1],
                'buyer': {
                    'id': buyer.get('id', str(int(time.time()))),
                    'name': buyer.get('name', 'Test'),
                    'surname': buyer.get('surname', 'User'),
                    'gsmNumber': buyer.get('gsm_number', '+905350000000'),
                    'email': buyer.get('email'),
                    'identityNumber': buyer.get('identity_number', '11111111111'),
                    'lastLoginDate': '2024-01-01 12:00:00',
                    'registrationDate': '2024-01-01 12:00:00',
                    'registrationAddress': buyer.get('address', 'Test Address'),
                    'ip': buyer.get('ip', '127.0.0.1'),
                    'city': buyer.get('city', 'Istanbul'),
                    'country': buyer.get('country', 'Turkey'),
                    'zipCode': buyer.get('zip_code', '34000')
                },
                'shippingAddress': {
                    'contactName': shipping_address.get('contact_name', buyer.get('name', '') + ' ' + buyer.get('surname', '')),
                    'city': shipping_address.get('city', 'Istanbul'),
                    'country': shipping_address.get('country', 'Turkey'),
                    'address': shipping_address.get('address', 'Test Address'),
                    'zipCode': shipping_address.get('zip_code', '34000')
                },
                'billingAddress': {
                    'contactName': billing_address.get('contact_name', buyer.get('name', '') + ' ' + buyer.get('surname', '')),
                    'city': billing_address.get('city', 'Istanbul'),
                    'country': billing_address.get('country', 'Turkey'),
                    'address': billing_address.get('address', 'Test Address'),
                    'zipCode': billing_address.get('zip_code', '34000')
                },
                'basketItems': [
                    {
                        'id': str(item.get('id', i)),
                        'name': str(item.get('name', 'Product')),
                        'category1': str(item.get('category1', 'Digital')),
                        'category2': str(item.get('category2', 'Service')),
                        'itemType': str(item.get('item_type', 'VIRTUAL')),
                        'price': str(item.get('price', price))
                    } for i, item in enumerate(basket_items)
                ]
            }
            
            checkout_form_initialize = iyzipay.CheckoutFormInitialize()
            response = checkout_form_initialize.create(request, self.options)
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('status') == 'success':
                logger.info(f"iyzico checkout form created: {result.get('token')}")
            else:
                logger.error(f"iyzico checkout form failed: {result.get('errorMessage')}")
            
            return result
            
        except Exception as e:
            logger.error(f"iyzico checkout form creation failed: {str(e)}")
            raise
    
    def retrieve_checkout_form(self, token: str) -> Dict[str, Any]:
        """
        Checkout form sonucunu al
        
        Args:
            token: Checkout form token
            
        Returns:
            Ödeme sonucu
        """
        try:
            request = {
                'locale': 'tr',
                'conversationId': str(int(time.time())),
                'token': token
            }
            
            checkout_form = iyzipay.CheckoutForm()
            response = checkout_form.retrieve(request, self.options)
            result = json.loads(response.read().decode('utf-8'))
            
            logger.info(f"iyzico checkout form retrieved: status={result.get('paymentStatus')}")
            return result
            
        except Exception as e:
            logger.error(f"iyzico checkout form retrieval failed: {str(e)}")
            raise
    
    def create_payment(
        self,
        price: float,
        paid_price: float,
        currency: str,
        basket_id: str,
        payment_card: Dict[str, Any],
        buyer: Dict[str, Any],
        billing_address: Dict[str, Any],
        shipping_address: Dict[str, Any],
        basket_items: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
        installment: int = 1
    ) -> Dict[str, Any]:
        """
        Direkt ödeme oluştur (3D Secure olmadan)
        
        Args:
            price: Toplam tutar
            paid_price: Ödenecek tutar  
            currency: Para birimi
            basket_id: Sepet ID
            payment_card: Kart bilgileri
            buyer: Alıcı bilgileri
            billing_address: Fatura adresi
            shipping_address: Teslimat adresi
            basket_items: Sepet içeriği
            conversation_id: İşlem ID
            installment: Taksit sayısı
            
        Returns:
            Ödeme sonucu
        """
        try:
            request = {
                'locale': 'tr',
                'conversationId': conversation_id or str(int(time.time())),
                'price': str(price),
                'paidPrice': str(paid_price),
                'currency': currency,
                'installment': str(installment),
                'basketId': basket_id,
                'paymentChannel': 'WEB',
                'paymentGroup': 'PRODUCT',
                'paymentCard': {
                    'cardHolderName': payment_card.get('card_holder_name'),
                    'cardNumber': payment_card.get('card_number'),
                    'expireMonth': payment_card.get('expire_month'),
                    'expireYear': payment_card.get('expire_year'),
                    'cvc': payment_card.get('cvc'),
                    'registerCard': '0'
                },
                'buyer': {
                    'id': buyer.get('id', str(int(time.time()))),
                    'name': buyer.get('name'),
                    'surname': buyer.get('surname'),
                    'gsmNumber': buyer.get('gsm_number', '+905350000000'),
                    'email': buyer.get('email'),
                    'identityNumber': buyer.get('identity_number', '11111111111'),
                    'lastLoginDate': '2024-01-01 12:00:00',
                    'registrationDate': '2024-01-01 12:00:00',
                    'registrationAddress': buyer.get('address', 'Test Address'),
                    'ip': buyer.get('ip', '127.0.0.1'),
                    'city': buyer.get('city', 'Istanbul'),
                    'country': buyer.get('country', 'Turkey'),
                    'zipCode': buyer.get('zip_code', '34000')
                },
                'shippingAddress': {
                    'contactName': shipping_address.get('contact_name'),
                    'city': shipping_address.get('city', 'Istanbul'),
                    'country': shipping_address.get('country', 'Turkey'),
                    'address': shipping_address.get('address', 'Test Address'),
                    'zipCode': shipping_address.get('zip_code', '34000')
                },
                'billingAddress': {
                    'contactName': billing_address.get('contact_name'),
                    'city': billing_address.get('city', 'Istanbul'),
                    'country': billing_address.get('country', 'Turkey'),
                    'address': billing_address.get('address', 'Test Address'),
                    'zipCode': billing_address.get('zip_code', '34000')
                },
                'basketItems': [
                    {
                        'id': item.get('id', str(i)),
                        'name': item.get('name'),
                        'category1': item.get('category1', 'Digital'),
                        'category2': item.get('category2', 'Service'),
                        'itemType': item.get('item_type', 'VIRTUAL'),
                        'price': str(item.get('price', price))
                    } for i, item in enumerate(basket_items)
                ]
            }
            
            payment = iyzipay.Payment()
            response = payment.create(request, self.options)
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('status') == 'success':
                logger.info(f"iyzico payment created: {result.get('paymentId')}")
            else:
                logger.error(f"iyzico payment failed: {result.get('errorMessage')}")
            
            return result
            
        except Exception as e:
            logger.error(f"iyzico payment creation failed: {str(e)}")
            raise
    
    def retrieve_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Ödeme detaylarını al
        
        Args:
            payment_id: iyzico payment ID
            
        Returns:
            Ödeme detayları
        """
        try:
            request = {
                'locale': 'tr',
                'conversationId': str(int(time.time())),
                'paymentId': payment_id
            }
            
            payment = iyzipay.Payment()
            response = payment.retrieve(request, self.options)
            result = json.loads(response.read().decode('utf-8'))
            
            return result
            
        except Exception as e:
            logger.error(f"iyzico payment retrieval failed: {str(e)}")
            raise
