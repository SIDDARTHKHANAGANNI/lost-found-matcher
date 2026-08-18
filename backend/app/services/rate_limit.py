import time
from collections import defaultdict
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import HTTPException, Request
from app.config import settings

# per-IP limiter (general use across all routes)
limiter = Limiter(key_func=get_remote_address)

# per-account tracking for auth routes — in-memory store
# (swap for Redis in production if scaling beyond a single instance)
_failed_attempts: dict[str, list[float]] = defaultdict(list)
_lockout_until: dict[str, float] = {}


def _prune_old_attempts(email: str, window_seconds: int = 60):
    now = time.time()
    _failed_attempts[email] = [
        t for t in _failed_attempts[email] if now - t < window_seconds
    ]


def check_account_backoff(email: str):
    """Raise 429 if this account is currently in backoff, using exponential delay
    instead of a hard lockout — each additional failure in the window doubles the wait."""
    now = time.time()
    lockout = _lockout_until.get(email)
    if lockout and now < lockout:
        retry_after = round(lockout - now, 1)
        raise HTTPException(
            status_code=429,
            detail=f"Too many attempts for this account. Try again in {retry_after}s.",
        )


def record_failed_attempt(email: str):
    _prune_old_attempts(email)
    _failed_attempts[email].append(time.time())

    attempt_count = len(_failed_attempts[email])
    if attempt_count >= 3:
        # exponential backoff: base * 2^(attempts - 3), capped at 15 min
        backoff = min(
            settings.rate_limit_backoff_base_seconds * (2 ** (attempt_count - 3)),
            900,
        )
        _lockout_until[email] = time.time() + backoff


def clear_failed_attempts(email: str):
    _failed_attempts.pop(email, None)
    _lockout_until.pop(email, None)