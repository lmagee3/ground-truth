"""Auth Middleware — Ground Truth API.

Provides:
  - API key authentication via ``X-API-Key`` request header
  - In-memory token-bucket rate limiting (per client IP)

Configuration (all via environment variables / .env):
  GT_API_KEY               — secret key consumers must send.
                             If unset or empty, auth is DISABLED (for local dev).
  GT_RATE_LIMIT_PER_MINUTE — max requests per IP per minute (default: 60).
                             Set to 0 to disable rate limiting.

Public routes (bypass auth + rate limiting):
  GET /
  GET /v1/health

Responses:
  401 Unauthorized      — ``X-API-Key`` header missing (when auth is enabled)
  403 Forbidden         — ``X-API-Key`` present but incorrect
  429 Too Many Requests — rate limit exceeded
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PUBLIC_PATHS: frozenset[str] = frozenset({"/", "/v1/health"})

# ---------------------------------------------------------------------------
# Token-bucket rate limiter (in-memory, per IP)
# ---------------------------------------------------------------------------


class _TokenBucket:
    """Simple sliding-window token bucket for one client IP."""

    __slots__ = ("_limit", "_window", "_timestamps")

    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self._limit = limit
        self._window = window_seconds
        self._timestamps: list[float] = []

    def allow(self) -> bool:
        """Return True if the request is within the rate limit, False otherwise."""
        now = time.monotonic()
        cutoff = now - self._window
        # Drop timestamps outside the sliding window
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        if len(self._timestamps) >= self._limit:
            return False
        self._timestamps.append(now)
        return True


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class AuthMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for API key auth + rate limiting."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._api_key: str = os.getenv("GT_API_KEY", "").strip()
        raw_limit = os.getenv("GT_RATE_LIMIT_PER_MINUTE", "60").strip()
        try:
            self._rate_limit: int = int(raw_limit)
        except ValueError:
            self._rate_limit = 60

        self._auth_enabled: bool = bool(self._api_key)
        self._rate_enabled: bool = self._rate_limit > 0

        # Per-IP token buckets
        self._buckets: dict[str, _TokenBucket] = defaultdict(
            lambda: _TokenBucket(self._rate_limit)
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Public routes — skip all checks
        if path in _PUBLIC_PATHS:
            return await call_next(request)

        # --- Rate limiting ---
        if self._rate_enabled:
            client_ip = self._get_client_ip(request)
            if not self._buckets[client_ip].allow():
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded. Max {self._rate_limit} requests per minute.",
                        "error": "rate_limit_exceeded",
                    },
                    headers={"Retry-After": "60"},
                )

        # --- API key authentication ---
        if self._auth_enabled:
            provided_key = request.headers.get("X-API-Key", "").strip()
            if not provided_key:
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Missing X-API-Key header.",
                        "error": "missing_api_key",
                    },
                )
            if provided_key != self._api_key:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Invalid API key.",
                        "error": "invalid_api_key",
                    },
                )

        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract the real client IP, respecting common reverse-proxy headers."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        if request.client:
            return request.client.host
        return "unknown"
