"""Internal HTTP transport — stdlib urllib with retry/backoff for GET requests.

Not part of the public API; use AnoreClient instead.
"""

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request

from .errors import APIConnectionError, APIError, error_for_status

USER_AGENT = "anore-python/1.2.0"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Transport:
    def __init__(self, base_url, api_key, secret=None, timeout=30, max_retries=2):
        base = urllib.parse.urlsplit(base_url)
        if base.scheme not in ("http", "https") or not base.netloc or base.username or base.password or base.query or base.fragment:
            raise ValueError("AnoreClient: base_url must be an HTTP(S) API URL without credentials, query or fragment")
        path = base.path.rstrip("/")
        if not path:
            path = "/api/v1"
        elif path == "/api":
            path += "/v1"
        self.base_url = urllib.parse.urlunsplit((base.scheme, base.netloc, path, "", ""))
        self.api_key = api_key
        self.secret = secret
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("AnoreClient: timeout must be > 0")
        if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("AnoreClient: max_retries must be a nonnegative integer")
        self.timeout = timeout
        self.max_retries = max_retries
        self._opener = urllib.request.build_opener(_NoRedirect())

    def request(self, method, path, body=None, sign=None):
        url = self.base_url + path
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

            secret = sign if sign is not None else self.secret
            if secret:
                import hashlib
                import hmac
                signature = hmac.new(
                    secret.encode("utf-8"), data, hashlib.sha256
                ).hexdigest()
                headers["X-ZPay-Signature"] = signature

        retries = self.max_retries if method == "GET" else 0

        for attempt in range(retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
                with self._opener.open(req, timeout=self.timeout) as resp:
                    return self._parse(resp.read(), resp.status, True), resp.headers
            except urllib.error.HTTPError as e:
                payload = self._parse(e.read(), e.code, False)
                rid = e.headers.get("X-Request-Id") if e.headers else None
                status = e.code
                e.close()
                if status >= 500 and attempt < retries:
                    time.sleep(self._backoff(attempt))
                    continue
                msg = payload.get("message") or payload.get("error")
                if not isinstance(msg, str):
                    msg = "request failed"
                raise error_for_status(status, msg, data=payload, request_id=rid)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if attempt < retries:
                    time.sleep(self._backoff(attempt))
                    continue
                raise APIConnectionError("could not reach anore API: %s" % e)

    @staticmethod
    def _backoff(attempt):
        return min(0.5 * (2 ** attempt), 4.0)

    @staticmethod
    def _parse(raw_bytes, status, success):
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(payload, dict):
                return payload
        except (ValueError, UnicodeDecodeError):
            pass
        if success:
            raise APIError("API returned an invalid JSON object", status=status)
        return {}
