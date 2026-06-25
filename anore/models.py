"""Typed response models for the anore API.

Lightweight dataclass-style wrappers over the JSON the API returns. Each keeps the
raw dict in `.raw` so forward-compatible fields are never lost.
"""


class _Model:
    __slots__ = ("raw",)

    def __init__(self, raw):
        self.raw = raw or {}

    def __getitem__(self, key):
        # dict-style access for fields not promoted to attributes
        return self.raw[key]

    def get(self, key, default=None):
        return self.raw.get(key, default)


class Payment(_Model):
    """A payment / invoice (response of create_payment and get_payment)."""

    __slots__ = ()

    @property
    def id(self):
        return self.raw.get("id")

    @property
    def order_id(self):
        return self.raw.get("orderId")

    @property
    def amount(self):
        return self.raw.get("amount")

    @property
    def currency(self):
        return self.raw.get("currency")

    @property
    def status(self):
        """'new' | 'paid' | 'expired'."""
        return self.raw.get("status")

    @property
    def paid(self):
        return bool(self.raw.get("paid"))

    @property
    def payment_url(self):
        return self.raw.get("paymentUrl")

    @property
    def expires_in(self):
        return self.raw.get("expiresIn")

    def __repr__(self):
        return "Payment(id=%r, status=%r, amount=%r)" % (self.id, self.status, self.amount)


class WebhookEvent(_Model):
    """A parsed (and verified) webhook payload."""

    __slots__ = ()

    @property
    def event(self):
        """e.g. 'payment.succeeded'."""
        return self.raw.get("event")

    @property
    def id(self):
        return self.raw.get("id")

    @property
    def order_id(self):
        return self.raw.get("orderId")

    @property
    def amount(self):
        return self.raw.get("amount")

    @property
    def currency(self):
        return self.raw.get("currency")

    @property
    def status(self):
        return self.raw.get("status")

    @property
    def description(self):
        return self.raw.get("description")

    @property
    def shop(self):
        return self.raw.get("shop")

    @property
    def created_at(self):
        return self.raw.get("createdAt")

    @property
    def is_succeeded(self):
        return self.event == "payment.succeeded"

    def __repr__(self):
        return "WebhookEvent(event=%r, id=%r, status=%r)" % (self.event, self.id, self.status)
