"""Typed response models for the anore API.

Lightweight dataclass-style wrappers over the JSON the API returns. Each keeps the
raw dict in `.raw` so forward-compatible fields are never lost.
"""

class _Model:
    __slots__ = ("raw",)

    def __init__(self, raw):
        self.raw = raw or {}

    def __getitem__(self, key):
        return self.raw[key]

    def get(self, key, default=None):
        return self.raw.get(key, default)


class Payment(_Model):
    """A payment / invoice (response of create_payment and get_payment)."""

    __slots__ = ()

    @property
    def success(self):
        return bool(self.raw.get("success"))

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
    def base_amount(self):
        return self.raw.get("baseAmount")

    @property
    def currency(self):
        return self.raw.get("currency")

    @property
    def currency_rate(self):
        return self.raw.get("currencyRate")

    @property
    def rub_amount(self):
        return self.raw.get("rubAmount")

    @property
    def description(self):
        return self.raw.get("description")

    @property
    def status(self):
        """'new' | 'paid' | 'expired'."""
        return self.raw.get("status")

    @property
    def paid(self):
        return bool(self.raw.get("paid"))

    @property
    def test(self):
        return bool(self.raw.get("test"))

    @property
    def payment_url(self):
        return self.raw.get("paymentUrl")

    @property
    def sbp_url(self):
        return self.raw.get("sbpUrl")

    @property
    def method(self):
        return self.raw.get("method")

    @property
    def created_at(self):
        return self.raw.get("createdAt")

    @property
    def paid_at(self):
        return self.raw.get("paidAt")

    @property
    def expires_in(self):
        return self.raw.get("expiresIn")

    def __repr__(self):
        return "Payment(id=%r, status=%r, amount=%r)" % (self.id, self.status, self.amount)


class PaymentList(_Model):
    """A paginated list returned by ``list_payments``."""

    __slots__ = ()

    @property
    def payments(self):
        return [Payment(item) for item in self.raw.get("payments", [])]

    @property
    def success(self):
        return bool(self.raw.get("success"))

    @property
    def shop_id(self):
        return self.raw.get("shopId")

    @property
    def total(self):
        return self.raw.get("total", 0)

    @property
    def limit(self):
        return self.raw.get("limit", 0)

    @property
    def offset(self):
        return self.raw.get("offset", 0)

    def __iter__(self):
        return iter(self.payments)

    def __len__(self):
        return len(self.raw.get("payments", []))


class Balance(_Model):
    """A shop payout balance."""

    __slots__ = ()

    @property
    def currency(self):
        return self.raw.get("currency")

    @property
    def available(self):
        return self.raw.get("available")

    @property
    def shop_local_balance(self):
        return self.raw.get("shopLocalBalance")

    @property
    def shop_local_available(self):
        return self.raw.get("shopLocalAvailable")

    @property
    def account_available(self):
        return self.raw.get("accountAvailable")

    @property
    def hold(self):
        return self.raw.get("hold")

    @property
    def frozen(self):
        return self.raw.get("frozen")

    @property
    def matured(self):
        return self.raw.get("matured")

    @property
    def paid_amount(self):
        return self.raw.get("paidAmount")

    @property
    def withdrawn(self):
        return self.raw.get("withdrawn")

    @property
    def reserved(self):
        return self.raw.get("reserved")

    @property
    def legacy_payouts_unassigned(self):
        return bool(self.raw.get("legacyPayoutsUnassigned"))

    @property
    def fee(self):
        return self.raw.get("fee", {})

    @property
    def min_amount(self):
        return self.raw.get("minAmount")

    @property
    def min_amount_by_method(self):
        return self.raw.get("minAmountByMethod", {})

    @property
    def max_amount(self):
        return self.raw.get("maxAmount")

    @property
    def max_amount_by_method(self):
        return self.raw.get("maxAmountByMethod", {})

    @property
    def usdt_rate_rub(self):
        return self.raw.get("usdtRateRub")

    @property
    def rapira_market_usdt_rub(self):
        return self.raw.get("rapiraMarketUsdtRub")

    @property
    def rapira_markup_percent(self):
        return self.raw.get("rapiraMarkupPercent")

    @property
    def rate_basis(self):
        return self.raw.get("rateBasis")

    @property
    def rapira_fixing(self):
        return self.raw.get("rapiraFixing")

    @property
    def cbr_rate_rub(self):
        return self.raw.get("cbrRateRub")

    @property
    def sbp_banks(self):
        return self.raw.get("sbpBanks", [])


class PayoutFees(_Model):
    """Effective payout fee settings."""

    __slots__ = ()

    @property
    def shop_id(self):
        return self.raw.get("shopId")

    @property
    def currency(self):
        return self.raw.get("currency")

    @property
    def threshold_rub(self):
        return self.raw.get("thresholdRub")

    @property
    def min_amount_rub(self):
        return self.raw.get("minAmountRub")

    @property
    def min_amount_rub_by_method(self):
        return self.raw.get("minAmountRubByMethod", {})

    @property
    def max_amount_rub(self):
        return self.raw.get("maxAmountRub")

    @property
    def max_amount_rub_by_method(self):
        return self.raw.get("maxAmountRubByMethod", {})

    @property
    def methods(self):
        return self.raw.get("methods", [])


class PayoutRates(_Model):
    """Current payout conversion rates."""

    __slots__ = ()

    @property
    def shop_id(self):
        return self.raw.get("shopId")

    @property
    def rate_policy(self):
        return self.raw.get("ratePolicy")

    @property
    def rate_basis(self):
        return self.raw.get("rateBasis")

    @property
    def sbp_rate_policy(self):
        return self.raw.get("sbpRatePolicy")

    @property
    def rapira_usdt_rub(self):
        return self.raw.get("rapiraUsdtRub")

    @property
    def rapira_market_usdt_rub(self):
        return self.raw.get("rapiraMarketUsdtRub")

    @property
    def rapira_markup_percent(self):
        return self.raw.get("rapiraMarkupPercent")

    @property
    def cbr_usd_rub(self):
        return self.raw.get("cbrUsdRub")

    @property
    def rub_to_usdt(self):
        return self.raw.get("rubToUsdt")

    @property
    def usdt_to_rub(self):
        return self.raw.get("usdtToRub")

    @property
    def rub_to_rub_settlement(self):
        return self.raw.get("rubToRubSettlement")

    @property
    def rapira_fixing(self):
        return self.raw.get("rapiraFixing")

    @property
    def fees(self):
        return self.raw.get("fees", [])


class Payout(_Model):
    """A payout request."""

    __slots__ = ()

    @property
    def id(self):
        return self.raw.get("id")

    @property
    def shop_id(self):
        return self.raw.get("shopId")

    @property
    def legacy(self):
        return bool(self.raw.get("legacy"))

    @property
    def status(self):
        return self.raw.get("status")

    @property
    def amount(self):
        return self.raw.get("amount")

    @property
    def method(self):
        return self.raw.get("methodCode", self.raw.get("method"))

    @property
    def address(self):
        return self.raw.get("address")

    @property
    def bank(self):
        return self.raw.get("bank")

    @property
    def fee(self):
        return self.raw.get("fee")

    @property
    def net_rub(self):
        return self.raw.get("netRub")

    @property
    def amount_usdt(self):
        return self.raw.get("amountUsdt")

    @property
    def rapira_rate(self):
        return self.raw.get("rapiraRate")

    @property
    def cbr_rate(self):
        return self.raw.get("cbrRate")

    @property
    def settlement_rub(self):
        return self.raw.get("settlementRub")

    @property
    def quote_type(self):
        return self.raw.get("quoteType")

    @property
    def rate_policy(self):
        return self.raw.get("ratePolicy")

    @property
    def rate_basis(self):
        return self.raw.get("rateBasis")

    @property
    def quote_applied_at(self):
        return self.raw.get("quoteAppliedAt")

    @property
    def manual_correction(self):
        return bool(self.raw.get("manualCorrection"))

    @property
    def status_revision(self):
        return self.raw.get("statusRevision")

    @property
    def external_id(self):
        return self.raw.get("externalId")

    @property
    def created_at(self):
        return self.raw.get("createdAt")

    @property
    def processed_at(self):
        return self.raw.get("processedAt")

    @property
    def tx_hash(self):
        return self.raw.get("txHash")


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
    def rub_amount(self):
        return self.raw.get("rubAmount")

    @property
    def currency(self):
        return self.raw.get("currency")

    @property
    def currency_rate(self):
        return self.raw.get("currencyRate")

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
        return self.event in ("payment.succeeded", "payout.succeeded")

    @property
    def is_payout(self):
        return bool(self.event and self.event.startswith("payout."))

    @property
    def external_id(self):
        return self.raw.get("externalId")

    @property
    def shop_id(self):
        return self.raw.get("shopId")

    @property
    def method(self):
        return self.raw.get("method")

    @property
    def fee(self):
        return self.raw.get("fee")

    @property
    def net_rub(self):
        return self.raw.get("netRub")

    @property
    def amount_usdt(self):
        return self.raw.get("amountUsdt")

    @property
    def settlement_rub(self):
        return self.raw.get("settlementRub")

    @property
    def processed_at(self):
        return self.raw.get("processedAt")

    @property
    def tx_hash(self):
        return self.raw.get("txHash")

    def __repr__(self):
        return "WebhookEvent(event=%r, id=%r, status=%r)" % (self.event, self.id, self.status)

    @property
    def manual_correction(self):
        return bool(self.raw.get("manualCorrection"))

    @property
    def status_revision(self):
        return self.raw.get("statusRevision")
