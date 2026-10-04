"""anore — official Python SDK for accepting payments.

Zero dependencies (stdlib only), Python 3.8+.

    from anore import AnoreClient, verify_webhook

    anore = AnoreClient(api_key="an_live_xxx")
    payment = anore.create_payment(amount=1500, description="Подписка Pro", order_id="order_42")
    print(payment.payment_url)

    status = anore.get_payment(payment.id)
    print(status.status, status.paid)
"""

from .client import AnoreClient, DEFAULT_BASE_URL
from .models import Balance, Payment, PaymentList, Payout, PayoutFees, PayoutRates, WebhookEvent
from .webhooks import verify_webhook, parse_webhook
from .errors import (
    AnoreError,
    APIError,
    AuthenticationError,
    ValidationError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    APIConnectionError,
    SignatureError,
)

__version__ = "1.2.0"

__all__ = [
    "AnoreClient",
    "DEFAULT_BASE_URL",
    "Payment",
    "PaymentList",
    "Balance",
    "PayoutFees",
    "PayoutRates",
    "Payout",
    "WebhookEvent",
    "verify_webhook",
    "parse_webhook",
    "AnoreError",
    "APIError",
    "AuthenticationError",
    "ValidationError",
    "ForbiddenError",
    "NotFoundError",
    "ServerError",
    "APIConnectionError",
    "SignatureError",
]
