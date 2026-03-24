from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request, status

from app.config.settings import get_settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        window = self._events[key]
        while window and now - window[0] > window_seconds:
            window.popleft()
        if len(window) >= limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded.")
        window.append(now)


rate_limiter = InMemoryRateLimiter()


async def rate_limit_device(request: Request) -> None:
    settings = get_settings()
    client = request.client.host if request.client else "unknown"
    rate_limiter.check(client, settings.device_rate_limit_per_minute, 60)
