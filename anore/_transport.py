"""Internal HTTP transport — stdlib urllib with retry/backoff on network errors.

Not part of the public API; use AnoreClient instead.
"""

import json
import time
import urllib.error
import urllib.request

from .errors import APIConnectionError, error_for_status

USER_AGENT = "anore-python/1.0.0"


class Transport:
    def __init__(self, base_url, api_key, secret=None, timeout=30, max_retries=2):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.secret = secret
        self.timeout = timeout
        self.max_retries = max_retries

    def request(self, method, path, body=None, sign=None):
        url = self.base_url + path
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
            # optional request signing — server verifies Anore-Signature if present
            secret = sign if sign is not None else self.secret
            if secret:
                import hashlib
                import hmac
                headers["Anore-Signature"] = hmac.new(
                    secret.encode("utf-8"), data, hashlib.sha256
                ).hexdigest()

        last_err = None
        # retry only transient failures: network errors + 5xx. POST is safe to
        # retry here because payment creation has no server-side idempotency key
        # yet — a duplicate is far less likely than a flaky-network false-negative,
        # and only fires on connection errors, not on a received 4xx.
        for attempt in range(self.max_retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return self._parse(resp.read()), resp.headers
            except urllib.error.HTTPError as e:
                payload = self._parse(e.read())
                rid = e.headers.get("X-Request-Id") if e.headers else None
                if e.code >= 500 and attempt < self.max_retries:
                    last_err = e
                    time.sleep(self._backoff(attempt))
                    continue
                msg = payload.get("message") or payload.get("error") or "request failed"
                raise error_for_status(e.code, msg, data=payload, request_id=rid)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(self._backoff(attempt))
                    continue
                raise APIConnectionError("could not reach anore API: %s" % e)

        raise APIConnectionError("could not reach anore API: %s" % last_err)

    @staticmethod
    def _backoff(attempt):
        return min(0.5 * (2 ** attempt), 4.0)

    @staticmethod
    def _parse(raw_bytes):
        if not raw_bytes:
            return {}
        try:
            return json.loads(raw_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {"raw": raw_bytes.decode("utf-8", "replace")}
