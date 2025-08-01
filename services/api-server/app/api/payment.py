#!/usr/bin/env python3
"""
Production-Ready Payment Gateway for Bkmrk'd Bookstore
Supports multiple payment providers with advanced error handling
"""

import os
import asyncio
import logging
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
import stripe
import paypalrestsdk
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.book import Book
from app.models.order import Order, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.services.auth_service import get_current_user
from app.services.notification_service import NotificationService
from app.database import get_db

logger = logging.getLogger(__name__)

# Initialize payment providers
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe.api_version = "2023-10-16"

paypalrestsdk.configure({
    "mode": os.getenv("PAYPAL_MODE", "sandbox"),
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
})

router = APIRouter(prefix="/api/payment", tags=["payment"])

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"

class PaymentMethodType(str, Enum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"
    CRYPTO = "crypto"

class PaymentIntentRequest(BaseModel):
    amount: Decimal = Field(..., ge=0.01, description="Amount in USD")
    currency: str = Field(default="usd", regex="^[a-z]{3}$")
    books: List[Dict[str, Any]] = Field(..., min_items=1)
    customer_email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    customer_name: str = Field(..., min_length=1, max_length=100)
    payment_method: PaymentMethodType = Field(default=PaymentMethodType.CARD)
    provider: PaymentProvider = Field(default=PaymentProvider.STRIPE)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    provider: PaymentProvider
    amount: Decimal
    currency: str
    status: str
    created_at: datetime

class PaymentConfirmationRequest(BaseModel):
    payment_intent_id: str
    provider: PaymentProvider
    order_id: Optional[str] = None

class PaymentService:
    """Production-ready payment service with multiple providers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService()
    
    async def create_payment_intent(
        self, 
        request: PaymentIntentRequest,
        user: User
    ) -> PaymentIntentResponse:
        """Create payment intent with multiple provider support"""
        try:
            # Create payment record
            payment = Payment(
                user_id=user.id,
                amount=float(request.amount),
                currency=request.currency,
                provider=request.provider.value,
                method=request.payment_method.value,
                status=PaymentStatus.PENDING,
                metadata=json.dumps(request.metadata)
            )
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            
            # Create payment intent based on provider
            if request.provider == PaymentProvider.STRIPE:
                return await self._create_stripe_payment_intent(request, payment)
            elif request.provider == PaymentProvider.PAYPAL:
                return await self._create_paypal_payment_intent(request, payment)
            else:
                raise HTTPException(status_code=400, detail="Unsupported payment provider")
                
        except Exception as e:
            logger.error(f"Error creating payment intent: {e}")
            raise HTTPException(status_code=500, detail="Payment intent creation failed")
    
    async def _create_stripe_payment_intent(
        self, 
        request: PaymentIntentRequest, 
        payment: Payment
    ) -> PaymentIntentResponse:
        """Create Stripe payment intent"""
        try:
            # Get or create Stripe customer
            customer = await self._get_or_create_stripe_customer(
                request.customer_email, 
                request.customer_name
            )
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(request.amount * 100),  # Convert to cents
                currency=request.currency,
                customer=customer.id,
                metadata={
                    "payment_id": str(payment.id),
                    "user_id": str(payment.user_id),
                    "books": json.dumps(request.books)
                },
                automatic_payment_methods={"enabled": True}
            )
            
            # Update payment record
            payment.provider_payment_id = payment_intent.id
            self.db.commit()
            
            return PaymentIntentResponse(
                client_secret=payment_intent.client_secret,
                payment_intent_id=payment_intent.id,
                provider=request.provider,
                amount=request.amount,
                currency=request.currency,
                status=payment_intent.status,
                created_at=datetime.fromtimestamp(payment_intent.created)
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def _create_paypal_payment_intent(
        self, 
        request: PaymentIntentRequest, 
        payment: Payment
    ) -> PaymentIntentResponse:
        """Create PayPal payment intent"""
        try:
            # Create PayPal payment
            paypal_payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": str(request.amount),
                        "currency": request.currency.upper()
                    },
                    "description": f"Book purchase - {len(request.books)} books"
                }],
                "redirect_urls": {
                    "return_url": f"{os.getenv('FRONTEND_URL')}/payment/success",
                    "cancel_url": f"{os.getenv('FRONTEND_URL')}/payment/cancel"
                }
            })
            
            if paypal_payment.create():
                # Update payment record
                payment.provider_payment_id = paypal_payment.id
                self.db.commit()
                
                return PaymentIntentResponse(
                    client_secret=paypal_payment.id,
                    payment_intent_id=paypal_payment.id,
                    provider=request.provider,
                    amount=request.amount,
                    currency=request.currency,
                    status="created",
                    created_at=datetime.now()
                )
            else:
                raise HTTPException(status_code=400, detail="PayPal payment creation failed")
                
        except Exception as e:
            logger.error(f"PayPal error: {e}")
            raise HTTPException(status_code=400, detail="PayPal payment creation failed")
    
    async def _get_or_create_stripe_customer(self, email: str, name: str) -> stripe.Customer:
        """Get or create Stripe customer"""
        try:
            # Search for existing customer
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                return customers.data[0]
            
            # Create new customer
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"source": "bookstore"}
            )
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Error with Stripe customer: {e}")
            raise HTTPException(status_code=400, detail="Customer creation failed")
    
    async def confirm_payment(
        self, 
        request: PaymentConfirmationRequest,
        user: User
    ) -> Dict[str, Any]:
        """Confirm payment and process order"""
        try:
            # Get payment record
            payment = self.db.query(Payment).filter(
                Payment.provider_payment_id == request.payment_intent_id
            ).first()
            
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            if payment.user_id != user.id:
                raise HTTPException(status_code=403, detail="Payment belongs to different user")
            
            # Confirm payment based on provider
            if request.provider == PaymentProvider.STRIPE:
                return await self._confirm_stripe_payment(payment, request)
            elif request.provider == PaymentProvider.PAYPAL:
                return await self._confirm_paypal_payment(payment, request)
            else:
                raise HTTPException(status_code=400, detail="Unsupported payment provider")
                
        except Exception as e:
            logger.error(f"Error confirming payment: {e}")
            raise HTTPException(status_code=500, detail="Payment confirmation failed")
    
    async def _confirm_stripe_payment(
        self, 
        payment: Payment, 
        request: PaymentConfirmationRequest
    ) -> Dict[str, Any]:
        """Confirm Stripe payment"""
        try:
            # Retrieve payment intent
            payment_intent = stripe.PaymentIntent.retrieve(request.payment_intent_id)
            
            if payment_intent.status == "succeeded":
                # Update payment status
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = datetime.now()
                self.db.commit()
                
                # Create order
                order = await self._create_order_from_payment(payment)
                
                # Send notification
                await self.notification_service.send_payment_confirmation(
                    payment.user_id, order.id, payment.amount, self.db
                )
                
                return {
                    "status": "success",
                    "message": "Payment confirmed and order processed",
                    "order_id": order.id,
                    "payment_id": payment.id
                }
            else:
                raise HTTPException(status_code=400, detail="Payment not successful")
                
        except stripe.error.StripeError as e:
            logger.error(f"Stripe confirmation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def _confirm_paypal_payment(
        self, 
        payment: Payment, 
        request: PaymentConfirmationRequest
    ) -> Dict[str, Any]:
        """Confirm PayPal payment"""
        try:
            # Execute PayPal payment
            paypal_payment = paypalrestsdk.Payment.find(request.payment_intent_id)
            
            if paypal_payment.execute({"payer_id": request.order_id}):
                # Update payment status
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = datetime.now()
                self.db.commit()
                
                # Create order
                order = await self._create_order_from_payment(payment)
                
                # Send notification
                await self.notification_service.send_payment_confirmation(
                    payment.user_id, order.id, payment.amount, self.db
                )
                
                return {
                    "status": "success",
                    "message": "PayPal payment confirmed and order processed",
                    "order_id": order.id,
                    "payment_id": payment.id
                }
            else:
                raise HTTPException(status_code=400, detail="PayPal payment execution failed")
                
        except Exception as e:
            logger.error(f"PayPal confirmation error: {e}")
            raise HTTPException(status_code=400, detail="PayPal payment confirmation failed")
    
    async def _create_order_from_payment(self, payment: Payment) -> Order:
        """Create order from successful payment"""
        try:
            # Parse books from metadata
            metadata = json.loads(payment.metadata or "{}")
            books = metadata.get("books", [])
            
            # Calculate total
            total_amount = payment.amount
            
            # Create order
            order = Order(
                user_id=payment.user_id,
                payment_id=payment.id,
                order_number=f"ORD-{int(time.time())}",
                total_amount=total_amount,
                status=OrderStatus.PROCESSING,
                shipping_address=metadata.get("shipping_address", ""),
                billing_address=metadata.get("billing_address", "")
            )
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            
            # Create order items
            for book_data in books:
                order_item = OrderItem(
                    order_id=order.id,
                    book_id=book_data.get("id"),
                    quantity=book_data.get("quantity", 1),
                    price=book_data.get("price", 0.0)
                )
                self.db.add(order_item)
            
            self.db.commit()
            return order
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise HTTPException(status_code=500, detail="Order creation failed")

# Payment endpoints
@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a payment intent"""
    payment_service = PaymentService(db)
    return await payment_service.create_payment_intent(request, current_user)

@router.post("/confirm-payment")
async def confirm_payment(
    request: PaymentConfirmationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm a payment"""
    payment_service = PaymentService(db)
    return await payment_service.confirm_payment(request, current_user)

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    try:
        # Get the webhook secret
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        # Get the webhook data
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Process the event
        await _process_stripe_webhook(event, db)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

async def _process_stripe_webhook(event: stripe.Event, db: Session):
    """Process Stripe webhook events"""
    try:
        if event.type == "payment_intent.succeeded":
            await _handle_successful_payment(event.data.object, db)
        elif event.type == "payment_intent.payment_failed":
            await _handle_failed_payment(event.data.object, db)
        else:
            logger.info(f"Unhandled event type: {event.type}")
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")

async def _handle_successful_payment(payment_intent: stripe.PaymentIntent, db: Session):
    """Handle successful payment"""
    try:
        # Get payment record
        payment = db.query(Payment).filter(
            Payment.provider_payment_id == payment_intent.id
        ).first()
        
        if payment:
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.now()
            db.commit()
            
            # Create order and send notification
            payment_service = PaymentService(db)
            order = await payment_service._create_order_from_payment(payment)
            await payment_service.notification_service.send_payment_confirmation(
                payment.user_id, order.id, payment.amount, db
            )
            
    except Exception as e:
        logger.error(f"Error handling successful payment: {e}")

async def _handle_failed_payment(payment_intent: stripe.PaymentIntent, db: Session):
    """Handle failed payment"""
    try:
        # Get payment record
        payment = db.query(Payment).filter(
            Payment.provider_payment_id == payment_intent.id
        ).first()
        
        if payment:
            payment.status = PaymentStatus.FAILED
            db.commit()
            
            # Send failure notification
            payment_service = PaymentService(db)
            await payment_service.notification_service.send_payment_failure_notification(
                payment.user_id, payment.id, db
            )
            
    except Exception as e:
        logger.error(f"Error handling failed payment: {e}")

@router.get("/payment-methods")
async def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's saved payment methods"""
    try:
        # Get user's payment methods from database
        payments = db.query(Payment).filter(
            Payment.user_id == current_user.id,
            Payment.status == PaymentStatus.COMPLETED
        ).all()
        
        return {
            "payment_methods": [
                {
                    "id": payment.id,
                    "provider": payment.provider,
                    "method": payment.method,
                    "last_used": payment.completed_at
                }
                for payment in payments
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment methods")

@router.get("/health")
async def payment_health_check():
    """Health check for payment service"""
    try:
        # Test Stripe connection
        stripe.PaymentIntent.list(limit=1)
        return {"status": "healthy", "stripe": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)} 