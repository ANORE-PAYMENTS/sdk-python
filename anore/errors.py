"""Exception hierarchy for the anore SDK.

    AnoreError                  — base for everything the SDK raises
    ├─ APIError                 — the API returned a non-2xx response
    │  ├─ ValidationError       — 400
    │  ├─ AuthenticationError   — 401
    │  ├─ ForbiddenError        — 403
    │  ├─ NotFoundError         — 404
    │  └─ ServerError           — 5xx
    ├─ APIConnectionError       — network failure / timeout (after retries)
    └─ SignatureError           — webhook signature verification failed
"""

class AnoreError(Exception):
    """Base class for all SDK errors."""

class APIError(AnoreError):
    """The API responded with a non-2xx status."""

    def __init__(self, message, status=0, data=None, request_id=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.data = data or {}
        self.request_id = request_id

    def __str__(self):
        rid = " (request_id=%s)" % self.request_id if self.request_id else ""
        return "anore: HTTP %s — %s%s" % (self.status, self.message, rid)

class ValidationError(APIError):
    """400 — invalid request (amount/description/shopId/JSON)."""

class AuthenticationError(APIError):
    """401 — missing or invalid API key / signature."""

class ForbiddenError(APIError):
    """403 — shop blocked, or access denied."""

class NotFoundError(APIError):
    """404 — shop or payment not found."""

class ServerError(APIError):
    """5xx — something went wrong on anore's side."""

class APIConnectionError(AnoreError):
    """Could not reach the API (network error / timeout), even after retries."""

class SignatureError(AnoreError):
    """Webhook signature did not match the expected value."""

def error_for_status(status, message, data=None, request_id=None):
    """Map an HTTP status to the most specific APIError subclass."""
    cls = {
        400: ValidationError,
        401: AuthenticationError,
        403: ForbiddenError,
        404: NotFoundError,
    }.get(status)
    if cls is None:
        cls = ServerError if status >= 500 else APIError
    return cls(message, status=status, data=data, request_id=request_id)
