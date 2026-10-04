"""Webhook signature verification and payload parsing."""

import hashlib
import hmac
import json
import re

from .errors import SignatureError
from .models import WebhookEvent

def verify_webhook(raw_body, signature, secret):
    """Verify an incoming webhook signature.

    Args:
        raw_body: the RAW request body (bytes or str) — never the re-serialized JSON.
        signature: the Anore-Signature header value.
        secret: signing secret from the dashboard (Webhooks tab).

    Returns:
        True if the signature matches, False otherwise.
    """
    if not isinstance(raw_body, (bytes, bytearray, str)) or not raw_body or not isinstance(signature, str) or not isinstance(secret, str) or not secret:
        return False
    if not re.fullmatch(r"[0-9a-fA-F]{64}", signature.strip()):
        return False
    if isinstance(raw_body, str):
        raw_body = raw_body.encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, str(signature).strip().lower())

def parse_webhook(raw_body, signature, secret):
    """Verify the signature and return the parsed event.

    Raises:
        SignatureError: if the signature does not match.
        ValueError: if the body is not valid JSON.

    Returns:
        WebhookEvent.
    """
    if not verify_webhook(raw_body, signature, secret):
        raise SignatureError("webhook signature verification failed")
    if isinstance(raw_body, (bytes, bytearray)):
        raw_body = raw_body.decode("utf-8")
    payload = json.loads(raw_body)
    if not isinstance(payload, dict):
        raise ValueError("webhook payload must be a JSON object")
    return WebhookEvent(payload)
