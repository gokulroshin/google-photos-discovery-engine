import time
import asyncio
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
import structlog

logger = structlog.get_logger(__name__)


class LoginRateLimiter:
    """
    In-memory sliding window rate limiter for login attempts per IP address.
    Limits to max_attempts (default 10) per window_seconds (default 900s = 15 mins).
    """

    def __init__(self, max_attempts: int = 10, window_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    def get_client_ip(self, request: Request) -> str:
        """Extracts client IP from X-Forwarded-For header or direct connection."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For can be a comma-separated list of IPs
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    async def check_rate_limit(self, request: Request, email: Optional[str] = None):
        """
        Checks if the client IP has exceeded the allowed login attempt threshold.
        Raises HTTP 429 Too Many Requests if exceeded.
        """
        ip = self.get_client_ip(request)
        now = time.time()
        cutoff = now - self.window_seconds

        async with self._lock:
            if ip not in self._attempts:
                self._attempts[ip] = []

            # Prune attempts older than the rolling window
            self._attempts[ip] = [t for t in self._attempts[ip] if t > cutoff]

            if len(self._attempts[ip]) >= self.max_attempts:
                logger.warning(
                    "login_rate_limit_exceeded",
                    client_ip=ip,
                    attempt_count=len(self._attempts[ip]),
                    target_email=email,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many login attempts from this IP. Please try again after {self.window_seconds // 60} minutes.",
                    headers={"Retry-After": str(self.window_seconds)},
                )

            # Record this attempt
            self._attempts[ip].append(now)

    async def log_failed_attempt(self, request: Request, email: str, reason: str = "invalid_credentials"):
        """Logs an audit record for failed authentication attempts."""
        ip = self.get_client_ip(request)
        logger.warning(
            "login_failed_audit",
            client_ip=ip,
            target_email=email,
            reason=reason,
            timestamp=time.time(),
        )

    def reset_for_ip(self, ip: str):
        """Resets rate limit records for a given IP (useful for testing)."""
        self._attempts.pop(ip, None)


# Global singleton rate limiter instance
login_rate_limiter = LoginRateLimiter(max_attempts=10, window_seconds=900)
