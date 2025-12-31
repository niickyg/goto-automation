"""
Stripe Billing Integration for CallWise (GoTo Automation)

Handles:
- Subscription creation and management
- Customer portal
- Webhook processing
- Usage-based billing (call counts)

Setup:
1. Create Stripe account at stripe.com
2. Get API keys from Dashboard > Developers > API Keys
3. Create products/prices in Dashboard > Products
4. Set up webhook endpoint: Dashboard > Developers > Webhooks

Environment Variables:
    STRIPE_SECRET_KEY      - Stripe secret key (sk_live_... or sk_test_...)
    STRIPE_PUBLISHABLE_KEY - Stripe publishable key (pk_live_... or pk_test_...)
    STRIPE_WEBHOOK_SECRET  - Webhook signing secret (whsec_...)
    STRIPE_PRICE_STARTER   - Price ID for Starter plan
    STRIPE_PRICE_PRO       - Price ID for Professional plan
    STRIPE_PRICE_BUSINESS  - Price ID for Business plan
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])

# Check if Stripe is available
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe not installed. Run: pip install stripe")

# Configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Price IDs (create these in Stripe Dashboard)
PRICE_IDS = {
    'starter': os.environ.get('STRIPE_PRICE_STARTER', 'price_starter'),
    'professional': os.environ.get('STRIPE_PRICE_PRO', 'price_professional'),
    'business': os.environ.get('STRIPE_PRICE_BUSINESS', 'price_business'),
}

# Plan limits
PLAN_LIMITS = {
    'starter': {'calls_per_month': 100, 'team_members': 3},
    'professional': {'calls_per_month': 500, 'team_members': 10},
    'business': {'calls_per_month': float('inf'), 'team_members': float('inf')},
}

if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# Request/Response Models
class CreateCheckoutRequest(BaseModel):
    """Request to create checkout session."""
    email: EmailStr
    plan: str  # 'starter', 'professional', 'business'
    success_url: str = "https://app.callwise.io/billing/success"
    cancel_url: str = "https://app.callwise.io/billing/cancel"


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str


class CustomerPortalRequest(BaseModel):
    """Request for customer portal."""
    customer_id: str
    return_url: str = "https://app.callwise.io/settings"


class SubscriptionStatus(BaseModel):
    """Subscription status response."""
    active: bool
    plan: Optional[str]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    usage: Dict[str, int]


# API Endpoints
@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(request: CreateCheckoutRequest):
    """
    Create a Stripe Checkout session for subscription.

    Returns a URL to redirect the customer to.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(500, "Stripe not configured")

    if request.plan not in PRICE_IDS:
        raise HTTPException(400, f"Invalid plan: {request.plan}")

    try:
        # Create or retrieve customer
        customers = stripe.Customer.list(email=request.email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=request.email,
                metadata={'source': 'callwise_web'}
            )

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': PRICE_IDS[request.plan],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{request.success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=request.cancel_url,
            metadata={
                'plan': request.plan,
                'source': 'callwise_web'
            },
            subscription_data={
                'metadata': {'plan': request.plan}
            },
            allow_promotion_codes=True,
        )

        logger.info(f"Created checkout session for {request.email}, plan: {request.plan}")

        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(500, f"Payment error: {str(e)}")


@router.post("/customer-portal")
async def create_customer_portal(request: CustomerPortalRequest):
    """
    Create a Stripe Customer Portal session.

    Allows customers to manage their subscription.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(500, "Stripe not configured")

    try:
        session = stripe.billing_portal.Session.create(
            customer=request.customer_id,
            return_url=request.return_url,
        )

        return {"portal_url": session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(500, f"Portal error: {str(e)}")


@router.get("/subscription/{customer_id}", response_model=SubscriptionStatus)
async def get_subscription_status(customer_id: str):
    """
    Get subscription status for a customer.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(500, "Stripe not configured")

    try:
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='active',
            limit=1
        )

        if not subscriptions.data:
            return SubscriptionStatus(
                active=False,
                plan=None,
                current_period_end=None,
                cancel_at_period_end=False,
                usage={'calls_this_month': 0}
            )

        sub = subscriptions.data[0]
        plan = sub.metadata.get('plan', 'starter')

        return SubscriptionStatus(
            active=True,
            plan=plan,
            current_period_end=datetime.fromtimestamp(sub.current_period_end),
            cancel_at_period_end=sub.cancel_at_period_end,
            usage={'calls_this_month': 0}  # TODO: Track actual usage
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(500, f"Error fetching subscription: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.

    Events handled:
    - checkout.session.completed: New subscription created
    - customer.subscription.updated: Subscription changed
    - customer.subscription.deleted: Subscription cancelled
    - invoice.payment_failed: Payment failed
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(500, "Stripe not configured")

    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    # Handle events
    event_type = event['type']
    data = event['data']['object']

    logger.info(f"Received Stripe webhook: {event_type}")

    if event_type == 'checkout.session.completed':
        # New subscription created
        customer_id = data['customer']
        subscription_id = data.get('subscription')
        email = data.get('customer_email')
        plan = data.get('metadata', {}).get('plan', 'starter')

        logger.info(f"New subscription: {email}, plan: {plan}")
        # TODO: Create/update user in database
        # TODO: Send welcome email

    elif event_type == 'customer.subscription.updated':
        # Subscription changed (upgrade, downgrade, renewal)
        customer_id = data['customer']
        status = data['status']
        plan = data.get('metadata', {}).get('plan', 'starter')

        logger.info(f"Subscription updated: {customer_id}, status: {status}")
        # TODO: Update user plan in database

    elif event_type == 'customer.subscription.deleted':
        # Subscription cancelled
        customer_id = data['customer']

        logger.info(f"Subscription cancelled: {customer_id}")
        # TODO: Downgrade user to free tier
        # TODO: Send cancellation email

    elif event_type == 'invoice.payment_failed':
        # Payment failed
        customer_id = data['customer']
        attempt_count = data.get('attempt_count', 1)

        logger.warning(f"Payment failed: {customer_id}, attempt: {attempt_count}")
        # TODO: Send payment failure email
        # TODO: Notify admin

    return {"status": "ok"}


# Usage tracking (for metered billing)
class UsageTracker:
    """Track usage for billing purposes."""

    def __init__(self):
        self.usage = {}  # In production, use Redis or database

    def record_call(self, customer_id: str):
        """Record a call for usage-based billing."""
        if customer_id not in self.usage:
            self.usage[customer_id] = {'calls': 0, 'minutes': 0}
        self.usage[customer_id]['calls'] += 1

    def get_usage(self, customer_id: str) -> Dict[str, int]:
        """Get usage for a customer."""
        return self.usage.get(customer_id, {'calls': 0, 'minutes': 0})

    def check_limit(self, customer_id: str, plan: str) -> bool:
        """Check if customer is within plan limits."""
        usage = self.get_usage(customer_id)
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['starter'])
        return usage['calls'] < limits['calls_per_month']


usage_tracker = UsageTracker()


# Middleware for checking subscription
async def require_subscription(customer_id: str, required_plan: str = None):
    """
    Dependency to check if customer has active subscription.

    Usage:
        @app.get("/protected")
        async def protected_route(customer_id: str = Depends(require_subscription)):
            ...
    """
    if not STRIPE_AVAILABLE or not STRIPE_SECRET_KEY:
        # Allow access if Stripe not configured (development)
        return customer_id

    try:
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='active',
            limit=1
        )

        if not subscriptions.data:
            raise HTTPException(402, "Active subscription required")

        sub = subscriptions.data[0]
        plan = sub.metadata.get('plan', 'starter')

        if required_plan:
            plan_order = {'starter': 1, 'professional': 2, 'business': 3}
            if plan_order.get(plan, 0) < plan_order.get(required_plan, 0):
                raise HTTPException(402, f"Requires {required_plan} plan or higher")

        return customer_id

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error checking subscription: {e}")
        raise HTTPException(500, "Error checking subscription")


# Helper to get pricing info
@router.get("/prices")
async def get_prices():
    """Get current pricing information."""
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price": 49,
                "interval": "month",
                "features": [
                    "Up to 100 calls/month",
                    "AI transcription",
                    "Sentiment analysis",
                    "3 team members",
                    "Email support"
                ],
                "limits": PLAN_LIMITS['starter']
            },
            {
                "id": "professional",
                "name": "Professional",
                "price": 99,
                "interval": "month",
                "popular": True,
                "features": [
                    "Up to 500 calls/month",
                    "Everything in Starter",
                    "Action item extraction",
                    "10 team members",
                    "Priority support"
                ],
                "limits": PLAN_LIMITS['professional']
            },
            {
                "id": "business",
                "name": "Business",
                "price": 199,
                "interval": "month",
                "features": [
                    "Unlimited calls",
                    "Everything in Professional",
                    "Advanced analytics",
                    "Unlimited team members",
                    "Dedicated support"
                ],
                "limits": PLAN_LIMITS['business']
            }
        ],
        "currency": "usd"
    }
