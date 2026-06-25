"""anore — official Python SDK for accepting payments.

Zero dependencies (stdlib only), Python 3.8+.

    from anore import AnoreClient, verify_webhook

    anore = AnoreClient(api_key="an_live_xxx")
    payment = anore.create_payment(amount=1500, description="Подписка Pro", order_id="order_42")
    print(payment.payment_url)

    status = anore.get_payment(payment.id)
    print(status.status, status.paid)
"""

from .client import AnoreClient
from .models import Payment, WebhookEvent
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

__version__ = "1.0.0"

__all__ = [
    "AnoreClient",
    "Payment",
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
