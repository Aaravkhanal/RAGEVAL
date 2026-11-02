"""Process-local HTTP runtime: CORS, hosts, evaluator cache, rate limit, headers."""

from __future__ import annotations

import os
import hashlib
import hmac
import threading
import time
import uuid
from typing import Dict, List, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from rageval.core.config import EvaluatorConfig
from rageval.evaluator.evaluator import RAGEvalEvaluator

DEFAULT_CORS = "http://127.0.0.1:8000,http://localhost:8000"
RATE_LIMITED_PREFIXES = ("/evaluate/", "/score")
PROTECTED_PREFIXES = ("/datasets", "/experiments", "/experiment-configs", "/evaluate", "/score", "/metrics")
MAX_REQUEST_BYTES = 65536
_evaluators: Dict[str, RAGEvalEvaluator] = {}
_eval_lock = threading.Lock()
_hits: Dict[str, List[float]] = {}
_hits_lock = threading.Lock()


def cors_allow_origins(raw: Optional[str] = None) -> Tuple[List[str], bool]:
    """Return (origins, allow_credentials). Wildcard disables credentials."""
    text = DEFAULT_CORS if raw is None else raw
    if raw is None:
        text = os.environ.get("RAGEVAL_CORS_ORIGINS", DEFAULT_CORS)
    origins = [part.strip() for part in text.split(",") if part.strip()]
    if not origins:
        origins = [part.strip() for part in DEFAULT_CORS.split(",")]
    if origins == ["*"]:
        return ["*"], False
    return origins, True


def allowed_hosts(raw: Optional[str] = None) -> List[str]:
    text = os.environ.get("RAGEVAL_ALLOWED_HOSTS", "*") if raw is None else raw
    hosts = [part.strip() for part in text.split(",") if part.strip()]
    return hosts or ["*"]


def rate_limit_per_minute() -> int:
    raw = os.environ.get("RAGEVAL_RATE_LIMIT_PER_MINUTE", "60").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 60


def require_public_auth() -> bool:
    return os.environ.get("RAGEVAL_REQUIRE_AUTH", "0").lower() in {"1", "true", "yes"}


def read_rate_limit_per_minute() -> int:
    try:
        return max(1, int(os.environ.get("RAGEVAL_READ_RATE_LIMIT_PER_MINUTE", "120")))
    except ValueError:
        return 120


class APIAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS" or not require_public_auth():
            return await call_next(request)
        path = request.url.path
        if not any(path == prefix or path.startswith(prefix + "/") for prefix in PROTECTED_PREFIXES):
            return await call_next(request)
        expected = os.environ.get("RAGEVAL_PUBLIC_TOKEN", "")
        if not expected:
            return JSONResponse(status_code=503, content={"detail": "Public API authentication is not configured"})
        supplied = request.headers.get("x-rageval-api-token", "")
        admin = os.environ.get("RAGEVAL_ADMIN_TOKEN", "")
        if not supplied or not (hmac.compare_digest(supplied, expected) or (admin and hmac.compare_digest(supplied, admin))):
            client = request.client.host if request.client else "unknown"
            if not allow_request(f"{client}:auth", 20):
                return JSONResponse(status_code=429, content={"detail": "Too many authentication attempts"}, headers={"Retry-After": "60"})
            return JSONResponse(status_code=401, content={"detail": "Invalid API token"})
        return await call_next(request)


def reset_runtime_for_tests() -> None:
    """Drop cached evaluators and rate-limit buckets. Tests only."""
    with _eval_lock:
        _evaluators.clear()
    with _hits_lock:
        _hits.clear()


def get_evaluator(method: str = "heuristic") -> RAGEvalEvaluator:
    key = (method or "heuristic").lower()
    if key not in {"heuristic", "nli"}:
        raise ValueError(f"method must be 'heuristic' or 'nli', got {method!r}")
    with _eval_lock:
        ev = _evaluators.get(key)
        if ev is None:
            ev = RAGEvalEvaluator(EvaluatorConfig(method=key, allow_heuristic_fallback=False))
            _evaluators[key] = ev
        return ev


def allow_request(client_key: str, limit: int, window_s: float = 60.0) -> bool:
    if limit <= 0:
        return True
    now = time.monotonic()
    with _hits_lock:
        bucket = _hits.setdefault(client_key, [])
        cutoff = now - window_s
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


class ProductionHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path
        limited = any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in RATE_LIMITED_PREFIXES)
        job_start = request.method == "POST" and path == "/experiments"
        protected_read = request.method == "GET" and any(path == prefix or path.startswith(prefix + "/") for prefix in PROTECTED_PREFIXES)
        if not limited and not job_start and not protected_read:
            return await call_next(request)
        if request.method == "POST":
            body = await request.body()
            if len(body) > MAX_REQUEST_BYTES:
                return JSONResponse(status_code=413, content={"detail": "Request body exceeds 64 KiB"})
        limit = rate_limit_per_minute()
        if job_start:
            limit = min(limit, 6) if limit else 6
        elif protected_read:
            limit = read_rate_limit_per_minute()
        client = request.client.host if request.client else "unknown"
        principal = request.headers.get("x-rageval-api-token", "") or request.headers.get("x-rageval-admin-token", "")
        principal_id = hashlib.sha256(principal.encode()).hexdigest()[:16] if principal else client
        category = "jobs" if job_start else "reads" if protected_read else "evaluation"
        if not allow_request(f"{principal_id}:{category}", limit):
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded ({limit}/minute for {category})."},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
