"""High-level API client."""

from ._transport import Transport
from .models import Payment

DEFAULT_BASE_URL = "https://api.anore.cc/v1"


class AnoreClient:
    """Client for the anore payments API.

    Args:
        api_key: key from the dashboard (an_live_… / an_test_…).
        secret: optional signing secret — when set, outgoing requests are signed
            with an Anore-Signature header (the server verifies it if present).
        base_url: API base, defaults to https://api.anore.cc/v1.
        timeout: per-request timeout in seconds.
        max_retries: retries on network errors / 5xx (exponential backoff).
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

    def create_payment(self, amount, description, order_id=None, shop_id=None):
        """Create a payment / invoice (POST /payments).

        Args:
            amount: amount in rubles, must be > 0.
            description: shown to the customer.
            order_id: your own order reference.
            shop_id: required only for account-level keys.

        Returns:
            Payment — use ``.payment_url`` to redirect the customer.
        """
        if not amount or amount <= 0:
            raise ValueError("create_payment: amount must be > 0")
        if not description:
            raise ValueError("create_payment: description is required")
        body = {"amount": amount, "description": description}
        if order_id is not None:
            body["orderId"] = order_id
        if shop_id is not None:
            body["shopId"] = shop_id
        data, _ = self._http.request("POST", "/payments", body=body)
        return Payment(data)

    def get_payment(self, payment_id):
        """Fetch payment status (GET /payments/{id}).

        Returns:
            Payment — ``.status`` is 'new' | 'paid' | 'expired'.
        """
        if not payment_id:
            raise ValueError("get_payment: payment_id is required")
        import urllib.parse
        path = "/payments/" + urllib.parse.quote(str(payment_id))
        data, _ = self._http.request("GET", path)
        return Payment(data)
