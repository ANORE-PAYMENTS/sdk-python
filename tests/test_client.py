import hashlib
import hmac
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anore import (  # noqa: E402
    AnoreClient,
    APIConnectionError,
    Balance,
    DEFAULT_BASE_URL,
    Payout,
    PayoutFees,
    PayoutRates,
    ServerError,
    SignatureError,
    ValidationError,
    parse_webhook,
    verify_webhook,
)


class Fixture:
    def __init__(self, handler):
        self.calls = []
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _handle(self):
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                call = {"method": self.command, "path": self.path, "headers": self.headers, "raw": raw}
                fixture.calls.append(call)
                result = handler(call, len(fixture.calls))
                if result is None:
                    self.close_connection = True
                    self.connection.close()
                    return
                status, data = result
                body = json.dumps(data).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("X-Request-Id", "fixture-request")
                self.end_headers()
                self.wfile.write(body)

            do_GET = _handle
            do_POST = _handle

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = "http://127.0.0.1:%d" % self.server.server_address[1]

    def client(self, **kwargs):
        options = {"api_key": "fixture-key", "secret": "fixture-secret", "base_url": self.origin, "max_retries": 1}
        options.update(kwargs)
        return AnoreClient(**options)

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class ClientTest(unittest.TestCase):
    def fixture(self, handler):
        fixture = Fixture(handler)
        self.addCleanup(fixture.close)
        return fixture

    def test_create_payment_sends_current_fields_signed_over_exact_bytes(self):
        fx = self.fixture(lambda call, n: (200, {"success": True, "id": "invoice", "paymentUrl": "https://pay.anore.cc/invoice"}))
        payment = fx.client().create_payment(
            amount=12.34, description="Оплата заказа", order_id="42", shop_id=7, currency="usd",
            methods=["card", "crypto-old"], getback_url="https://merchant.example/back",
            success_url="https://merchant.example/ok", fail_url="https://merchant.example/fail",
            callback_url="https://merchant.example/hook", email="customer@example.test")
        call = fx.calls[0]
        self.assertEqual(payment.id, "invoice")
        self.assertEqual(call["path"], "/api/v1/payments")
        self.assertEqual(call["headers"]["Authorization"], "Bearer fixture-key")
        self.assertEqual(json.loads(call["raw"]), {
            "amount": 12.34, "description": "Оплата заказа", "orderId": "42", "shopId": 7, "currency": "usd",
            "methods": ["card", "crypto-old"], "getbackurl": "https://merchant.example/back",
            "successurl": "https://merchant.example/ok", "failurl": "https://merchant.example/fail",
            "callbackUrl": "https://merchant.example/hook", "email": "customer@example.test"})
        expected = hmac.new(b"fixture-secret", call["raw"], hashlib.sha256).hexdigest()
        self.assertEqual(call["headers"]["X-ZPay-Signature"], expected)

    def test_base_urls_do_not_duplicate_paths(self):
        self.assertEqual(DEFAULT_BASE_URL, "https://api.anore.cc/api/v1")
        fx = self.fixture(lambda call, n: (200, {"id": "test", "paid": True, "status": "paid"}))
        for suffix in ["", "/", "/api", "/api/v1/", "/v1/", "/proxy/api/"]:
            AnoreClient(api_key="key", base_url=fx.origin + suffix).get_payment("a/b?c")
        self.assertEqual([c["path"] for c in fx.calls], [
            "/api/v1/payments/a%2Fb%3Fc", "/api/v1/payments/a%2Fb%3Fc", "/api/v1/payments/a%2Fb%3Fc",
            "/api/v1/payments/a%2Fb%3Fc", "/v1/payments/a%2Fb%3Fc", "/proxy/api/payments/a%2Fb%3Fc"])

    def test_list_payments_encodes_filters(self):
        fx = self.fixture(lambda call, n: (200, {"success": True, "shopId": 7, "limit": 20, "offset": 40, "total": 80,
                                                 "payments": [{"id": "first", "status": "paid", "paid": True, "currencyRate": 88}]}))
        page = fx.client().list_payments(shop_id=7, status="paid", date_from="2026-10-01", date_to="2026-10-03", limit=20, offset=40)
        self.assertEqual(fx.calls[0]["path"], "/api/v1/payments?limit=20&offset=40&shopId=7&status=paid&from=2026-10-01&to=2026-10-03")
        self.assertEqual(page.total, 80)
        self.assertEqual(list(page)[0].currency_rate, 88)

    def test_balance_fees_rates_and_payout_status_are_shop_scoped(self):
        fx = self.fixture(lambda call, n: (200, {"id": "WD-42", "currency": "RUB", "methodCode": "sbp", "method": "СБП"}))
        client = fx.client()
        self.assertIsInstance(client.get_balance(shop_id=7), Balance)
        self.assertIsInstance(client.get_payout_fees(shop_id=7), PayoutFees)
        self.assertIsInstance(client.get_payout_rates(shop_id=7), PayoutRates)
        payout = client.get_payout("WD-42")
        self.assertIsInstance(payout, Payout)
        self.assertEqual(payout.method, "sbp")
        self.assertEqual([c["path"] for c in fx.calls], [
            "/api/v1/balance?shopId=7", "/api/v1/payouts/fees?shopId=7", "/api/v1/payouts/rates?shopId=7", "/api/v1/payouts/WD-42"])

    def test_create_payout_sends_all_fields(self):
        fx = self.fixture(lambda call, n: (200, {"id": "WD-42", "method": "usdt_erc20", "ratePolicy": "approval", "quoteType": "estimate"}))
        payout = fx.client().create_payout(amount=5000, method="usdt_erc20", address="0x123", shop_id=7, bank="example", external_id="merchant-42")
        self.assertEqual(payout.rate_policy, "approval")
        self.assertEqual(json.loads(fx.calls[0]["raw"]), {
            "amount": 5000, "method": "usdt_erc20", "address": "0x123", "shopId": 7, "bank": "example", "externalId": "merchant-42"})

    def test_get_retries_server_errors(self):
        fx = self.fixture(lambda call, n: (503, {"message": "busy"}) if n == 1 else (200, {"id": "ok"}))
        self.assertEqual(fx.client().get_payment("ok").id, "ok")
        self.assertEqual(len(fx.calls), 2)

    def test_post_never_retries(self):
        for respond in (lambda call, n: (503, {"message": "busy"}), lambda call, n: None):
            fx = self.fixture(respond)
            client = fx.client()
            expected = ServerError if respond(None, 0) else APIConnectionError
            with self.assertRaises(expected):
                client.create_payment(amount=1, description="test")
            with self.assertRaises(expected):
                client.create_payout(amount=5000, method="card", address="card")
            self.assertEqual(len(fx.calls), 2)

    def test_api_error_carries_message_and_request_id(self):
        fx = self.fixture(lambda call, n: (400, {"message": "amount must be > 0"}))
        with self.assertRaises(ValidationError) as ctx:
            fx.client().get_payment("x")
        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(ctx.exception.request_id, "fixture-request")
        self.assertIn("amount must be > 0", str(ctx.exception))

    def test_invalid_input_fails_before_networking(self):
        client = AnoreClient(api_key="key", base_url="http://127.0.0.1:9")
        for amount in (0, -1, float("nan"), float("inf"), True, "10"):
            with self.assertRaises(ValueError):
                client.create_payment(amount=amount, description="x")
        with self.assertRaises(ValueError):
            AnoreClient(api_key="key", max_retries=-1)
        with self.assertRaises(ValueError):
            AnoreClient(api_key="key", base_url="https://user:pass@api.anore.cc")


class WebhookTest(unittest.TestCase):
    def sign(self, raw, secret="whsec"):
        return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()

    def test_payment_webhook(self):
        raw = json.dumps({"event": "payment.succeeded", "id": "uuid", "orderId": "42", "amount": 10, "rubAmount": 900,
                          "currency": "usd", "currencyRate": 90, "status": "paid"}, ensure_ascii=False).encode()
        event = parse_webhook(raw, self.sign(raw), "whsec")
        self.assertTrue(event.is_succeeded)
        self.assertFalse(event.is_payout)
        self.assertEqual(event.rub_amount, 900)

    def test_payout_webhook(self):
        raw = json.dumps({"event": "payout.succeeded", "id": "WD-1", "externalId": "m-1", "shopId": 7, "status": "paid",
                          "method": "usdt_ton", "amountUsdt": 50.5, "txHash": "abc", "manualCorrection": False,
                          "statusRevision": 0}).encode()
        event = parse_webhook(raw.decode(), self.sign(raw).upper(), "whsec")
        self.assertTrue(event.is_payout)
        self.assertTrue(event.is_succeeded)
        self.assertEqual(event.external_id, "m-1")
        self.assertEqual(event.tx_hash, "abc")

    def test_bad_signatures(self):
        raw = b'{"event":"payment.succeeded"}'
        self.assertFalse(verify_webhook(raw, self.sign(raw, "other"), "whsec"))
        self.assertFalse(verify_webhook(raw, "", "whsec"))
        self.assertFalse(verify_webhook(raw, self.sign(raw), ""))
        self.assertFalse(verify_webhook(b"", self.sign(b""), "whsec"))
        with self.assertRaises(SignatureError):
            parse_webhook(raw, "00" * 32, "whsec")


if __name__ == "__main__":
    unittest.main()
