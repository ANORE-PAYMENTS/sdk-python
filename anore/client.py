"""High-level API client."""

import math
import urllib.parse

from ._transport import Transport
from .models import (
    Balance,
    Payment,
    PaymentList,
    Payout,
    PayoutFees,
    PayoutList,
    PayoutRates,
    SubscriptionBinding,
    SubscriptionCatalog,
    SubscriptionCharge,
    SubscriptionStatus,
)

DEFAULT_BASE_URL = "https://api.anore.cc/api/v1"

class AnoreClient:
    """Client for the anore payments API.

    Args:
        api_key: key from the dashboard (an_live_… / an_test_…).
        secret: optional signing secret — when set, outgoing requests are signed
            with X-ZPay-Signature.
        base_url: API base, defaults to https://api.anore.cc/api/v1.
        timeout: per-request timeout in seconds.
        max_retries: GET retries on network errors / 5xx (exponential backoff).
    """

    def __init__(
        self,
        api_key,
        secret=None,
        base_url=DEFAULT_BASE_URL,
        timeout=30,
        max_retries=2,
    ):
        if not api_key:
            raise ValueError("AnoreClient: api_key is required")
        self._http = Transport(
            base_url=base_url,
            api_key=api_key,
            secret=secret,
            timeout=timeout,
            max_retries=max_retries,
        )

    def create_payment(
        self,
        amount,
        description,
        order_id=None,
        shop_id=None,
        currency="rub",
        methods=None,
        getback_url=None,
        success_url=None,
        fail_url=None,
        callback_url=None,
        email=None,
        user_identity=None,
        franchise=None,
    ):
        """Create a payment / invoice (POST /payments).

        Args:
            amount: amount in rubles, must be > 0.
            description: shown to the customer.
            order_id: your own order reference.
            shop_id: required only for account-level keys.

        Returns:
            Payment — use ``.payment_url`` to redirect the customer.
        """
        _validate_amount(amount, "create_payment")
        if not description:
            raise ValueError("create_payment: description is required")
        body = {"amount": amount, "description": description}
        if order_id is not None:
            body["orderId"] = order_id
        if shop_id is not None:
            body["shopId"] = shop_id
        if currency:
            body["currency"] = currency
        if methods is not None:
            body["methods"] = methods
        if getback_url is not None:
            body["getbackurl"] = getback_url
        if success_url is not None:
            body["successurl"] = success_url
        if fail_url is not None:
            body["failurl"] = fail_url
        if callback_url is not None:
            body["callbackUrl"] = callback_url
        if email is not None:
            body["email"] = email
        if user_identity is not None:
            body["user_identity"] = _user_identity(user_identity)
        if franchise is not None:
            body["franchise"] = _franchise(franchise)
        data, _ = self._http.request("POST", "/payments", body=body)
        return Payment(data)

    def get_payment(self, payment_id):
        """Fetch payment status (GET /payments/{id}).

        Returns:
            Payment — ``.status`` is 'new' | 'paid' | 'expired' | 'written_off'.
        """
        if not payment_id:
            raise ValueError("get_payment: payment_id is required")
        path = "/payments/" + urllib.parse.quote(str(payment_id), safe="")
        data, _ = self._http.request("GET", path)
        return Payment(data)

    def list_payments(
        self,
        shop_id=None,
        status=None,
        date_from=None,
        date_to=None,
        limit=50,
        offset=0,
    ):
        """List payments with server-side pagination (GET /payments)."""
        query = {"limit": limit, "offset": offset}
        if shop_id is not None:
            query["shopId"] = shop_id
        if status is not None:
            query["status"] = status
        if date_from is not None:
            query["from"] = date_from
        if date_to is not None:
            query["to"] = date_to
        data, _ = self._http.request("GET", "/payments?" + urllib.parse.urlencode(query))
        return PaymentList(data)

    def get_subscription_catalog(self):
        """List subscription plans available to this API key."""
        data, _ = self._http.request("GET", "/subscriptions/catalog")
        return SubscriptionCatalog(data)

    def create_subscription(
        self,
        plan_id,
        customer_id,
        customer_email,
        idempotency_key,
        shop_id=None,
    ):
        """Create a subscription binding QR.

        POST requests are never retried automatically. If the API returns
        ``binding_reconciling``, keep this exact key and body; do not generate a
        new key while ANORE reconciles the existing provider effect.
        """
        if not plan_id:
            raise ValueError("create_subscription: plan_id is required")
        if not customer_id:
            raise ValueError("create_subscription: customer_id is required")
        if not customer_email:
            raise ValueError("create_subscription: customer_email is required")
        _validate_idempotency_key(idempotency_key, "create_subscription")
        body = {
            "planId": plan_id,
            "customerId": customer_id,
            "customerEmail": customer_email,
        }
        if shop_id is not None:
            body["shopId"] = shop_id
        data, _ = self._http.request(
            "POST",
            "/subscriptions",
            body=body,
            headers={"Idempotency-Key": idempotency_key},
        )
        return SubscriptionBinding(data)

    def charge_subscription(self, subscription_id, idempotency_key):
        """Start a recurring charge with a caller-owned idempotency key."""
        if isinstance(subscription_id, bool) or not isinstance(subscription_id, int) or subscription_id <= 0:
            raise ValueError("charge_subscription: subscription_id must be a positive integer")
        _validate_idempotency_key(idempotency_key, "charge_subscription")
        path = "/subscriptions/%d/charges" % subscription_id
        data, _ = self._http.request(
            "POST", path, headers={"Idempotency-Key": idempotency_key}
        )
        return SubscriptionCharge(data)

    def get_subscription(self, subscription_id):
        """Fetch the safe normalized subscription status."""
        if isinstance(subscription_id, bool) or not isinstance(subscription_id, int) or subscription_id <= 0:
            raise ValueError("get_subscription: subscription_id must be a positive integer")
        data, _ = self._http.request("GET", "/subscriptions/%d" % subscription_id)
        return SubscriptionStatus(data)

    def get_balance(self, shop_id=None):
        """Fetch the shop payout balance (GET /balance)."""
        data, _ = self._http.request("GET", self._shop_path("/balance", shop_id))
        return Balance(data)

    def get_payout_fees(self, shop_id=None):
        """Fetch effective payout fees (GET /payouts/fees)."""
        data, _ = self._http.request("GET", self._shop_path("/payouts/fees", shop_id))
        return PayoutFees(data)

    def get_payout_rates(self, shop_id=None):
        """Fetch current payout rates (GET /payouts/rates)."""
        data, _ = self._http.request("GET", self._shop_path("/payouts/rates", shop_id))
        return PayoutRates(data)

    def list_payouts(self, shop_id=None, limit=50, cursor=None):
        """List non-test payouts with cursor pagination."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("list_payouts: limit must be an integer between 1 and 100")
        query = {"limit": limit}
        if shop_id is not None:
            query["shopId"] = shop_id
        if cursor is not None:
            query["cursor"] = cursor
        data, _ = self._http.request("GET", "/payouts?" + urllib.parse.urlencode(query))
        return PayoutList(data)

    def create_payout(
        self,
        amount,
        method,
        address,
        shop_id=None,
        bank=None,
        external_id=None,
    ):
        """Create a payout request (POST /payouts)."""
        _validate_amount(amount, "create_payout")
        if not method:
            raise ValueError("create_payout: method is required")
        if not address:
            raise ValueError("create_payout: address is required")
        body = {"amount": amount, "method": method, "address": address}
        if shop_id is not None:
            body["shopId"] = shop_id
        if bank is not None:
            body["bank"] = bank
        if external_id is not None:
            body["externalId"] = external_id
        data, _ = self._http.request("POST", "/payouts", body=body)
        return Payout(data)

    def get_payout(self, payout_id):
        """Fetch payout status (GET /payouts/{id})."""
        if not payout_id:
            raise ValueError("get_payout: payout_id is required")
        path = "/payouts/" + urllib.parse.quote(str(payout_id), safe="")
        data, _ = self._http.request("GET", path)
        return Payout(data)

    @staticmethod
    def _shop_path(path, shop_id):
        if shop_id is None:
            return path
        return path + "?" + urllib.parse.urlencode({"shopId": shop_id})


def _validate_idempotency_key(value, operation):
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError("%s: idempotency_key must be a string of 1 to 128 characters" % operation)


def _user_identity(value):
    operation = "create_payment: user_identity"
    if not isinstance(value, dict):
        raise ValueError(operation + " must be an object")
    allowed = {"type", "value", "telegram_username"}
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(operation + " contains unsupported fields")
    identity_type = value.get("type")
    if identity_type not in {"telegram_id", "email", "username", "external_id"}:
        raise ValueError(operation + " has an unsupported type")
    raw_value = value.get("value")
    if identity_type == "telegram_id":
        identity_value = _telegram_id(raw_value, operation + ".value")
    elif not isinstance(raw_value, str) or not raw_value.strip() or len(raw_value) > 190:
        raise ValueError(operation + ".value must be a nonempty string of at most 190 characters")
    else:
        identity_value = raw_value
    result = {"type": identity_type, "value": identity_value}
    if "telegram_username" in value:
        if identity_type != "telegram_id":
            raise ValueError(operation + ".telegram_username is allowed only with telegram_id")
        result["telegram_username"] = _telegram_username(
            value["telegram_username"], operation + ".telegram_username"
        )
    return result


def _franchise(value):
    operation = "create_payment: franchise"
    if not isinstance(value, dict):
        raise ValueError(operation + " must be an object")
    allowed = {"type", "address", "owner_telegram_id", "owner_telegram_username"}
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(operation + " contains unsupported fields")
    franchise_type = value.get("type")
    if franchise_type not in {"telegram_bot", "website"}:
        raise ValueError(operation + " has an unsupported type")
    address = value.get("address")
    if not isinstance(address, str) or not address.strip():
        raise ValueError(operation + ".address is required")
    if franchise_type == "telegram_bot":
        _telegram_username(address, operation + ".address")
    else:
        parsed = urllib.parse.urlsplit(address)
        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
        ):
            raise ValueError(operation + ".address must be a canonical HTTPS origin")
    result = {
        "type": franchise_type,
        "address": address,
        "owner_telegram_id": _telegram_id(
            value.get("owner_telegram_id"), operation + ".owner_telegram_id"
        ),
    }
    if "owner_telegram_username" in value:
        result["owner_telegram_username"] = _telegram_username(
            value["owner_telegram_username"], operation + ".owner_telegram_username"
        )
    return result


def _telegram_id(value, field):
    if isinstance(value, bool):
        raise ValueError(field + " must be a positive signed-64 integer")
    if isinstance(value, int):
        canonical = str(value)
    elif isinstance(value, str):
        canonical = value
    else:
        raise ValueError(field + " must be a positive signed-64 integer")
    if not canonical.isascii() or not canonical.isdigit() or canonical.startswith("0"):
        raise ValueError(field + " must be a positive signed-64 integer")
    parsed = int(canonical)
    if parsed <= 0 or parsed > 9223372036854775807:
        raise ValueError(field + " is out of range")
    return canonical if isinstance(value, str) else parsed


def _telegram_username(value, field):
    if not isinstance(value, str):
        raise ValueError(field + " must be a Telegram username")
    username = value[1:] if value.startswith("@") else value
    if not 5 <= len(username) <= 32 or not username.isascii() or any(
        not (character.isalnum() or character == "_") for character in username
    ):
        raise ValueError(field + " must be a Telegram username")
    return value


def _validate_amount(amount, operation):
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
        raise ValueError("%s: amount must be a finite number > 0" % operation)
