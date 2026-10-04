"""High-level API client."""

import math
import urllib.parse

from ._transport import Transport
from .models import Balance, Payment, PaymentList, Payout, PayoutFees, PayoutRates

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


def _validate_amount(amount, operation):
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
        raise ValueError("%s: amount must be a finite number > 0" % operation)
