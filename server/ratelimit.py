"""
IP sliding-window rate limiter — in-memory (default) with Redis fallback for production.
"""
import time
import threading
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List

from fastapi import Request, HTTPException

logger = logging.getLogger("app.ratelimit")


class BaseRateLimiter(ABC):
    @abstractmethod
    async def __call__(self, request: Request):
        ...


class MemoryRateLimiter(BaseRateLimiter):
    """In-memory sliding window — suitable for single-process deployments."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max = max_requests
        self.window = window_seconds
        self._hits: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _clean(self, key: str, now: float):
        cutoff = now - self.window
        hits = self._hits[key]
        idx = 0
        for i, t in enumerate(hits):
            if t > cutoff:
                idx = i
                break
        else:
            idx = len(hits)
        self._hits[key] = hits[idx:]
        return len(self._hits[key])

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        now = time.time()

        with self._lock:
            count = self._clean(key, now)
            if count >= self.max:
                raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
            self._hits[key].append(now)

        if hash(key) % 1000 == 0:
            self._gc(now)

    def _gc(self, now: float):
        cutoff = now - self.window
        with self._lock:
            stale = [k for k, v in self._hits.items() if not v or v[-1] <= cutoff]
            for k in stale:
                del self._hits[k]


class RedisRateLimiter(BaseRateLimiter):
    """Redis sorted-set sliding window — suitable for multi-process deployments."""

    LUA_SCRIPT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local max_req = tonumber(ARGV[3])
    local cutoff = now - window
    redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
    local count = redis.call('ZCARD', key)
    if count >= max_req then
        return 0
    end
    redis.call('ZADD', key, now, now .. ':' .. ARGV[4])
    redis.call('EXPIRE', key, window)
    return 1
    """

    def __init__(self, redis_client, max_requests: int = 60, window_seconds: int = 60):
        self.max = max_requests
        self.window = window_seconds
        self._redis = redis_client
        self._script = None  # lazily registered

    async def __call__(self, request: Request):
        if self._script is None:
            self._script = self._redis.register_script(self.LUA_SCRIPT)

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}:{request.url.path}"
        now = time.time()
        nonce = str(time.time_ns())

        allowed = self._script(
            keys=[key],
            args=[now, self.window, self.max, nonce],
        )
        if not allowed:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")


# ---- Redis client lazy init ----
_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        from config import settings
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        import redis
        r = redis.Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        r.ping()
        _redis_client = r
        logger.info("Redis connected — using RedisRateLimiter")
    except Exception:
        _redis_client = False
        logger.info("Redis unavailable — using MemoryRateLimiter")
    return _redis_client


def _make_limiter(max_requests: int, window_seconds: int) -> BaseRateLimiter:
    redis_conn = _get_redis()
    if redis_conn:
        return RedisRateLimiter(redis_conn, max_requests=max_requests, window_seconds=window_seconds)
    return MemoryRateLimiter(max_requests=max_requests, window_seconds=window_seconds)


# Preset limiters (auto-detect Redis)
general_limiter = _make_limiter(max_requests=120, window_seconds=60)
strict_limiter = _make_limiter(max_requests=10, window_seconds=60)
