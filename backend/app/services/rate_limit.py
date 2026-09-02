from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, status


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        now = monotonic()
        cutoff = now - window_seconds
        with self._lock:
            attempts = self._attempts[key]
            while attempts and attempts[0] < cutoff:
                attempts.popleft()
            if len(attempts) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="请求过于频繁，请稍后再试",
                )
            attempts.append(now)


auth_rate_limiter = InMemoryRateLimiter()

