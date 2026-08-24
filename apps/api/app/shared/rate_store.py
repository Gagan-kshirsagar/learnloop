import asyncio
import time
from typing import Protocol
from uuid import uuid4

from app.shared.config import get_settings


class RateStore(Protocol):
    async def check_and_consume(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        amount: int = 1,
    ) -> tuple[bool, int, int]:
        """Check if request is within limit and atomically consume units.

        Returns:
            tuple[bool, int, int]: (allowed, current_count, retry_after_seconds)
        """
        ...

    async def increment_with_expiry(
        self,
        key: str,
        window_seconds: int,
        amount: int = 1,
    ) -> int:
        """Increment key by amount and ensure TTL is set. Returns new count."""
        ...

    async def get_count(self, key: str, window_seconds: int = 86400) -> int:
        """Get current count of units in the active window."""
        ...

    async def reset(self, key: str | None = None) -> None:
        """Reset key or all stored rate keys."""
        ...


class InMemoryRateStore:
    """Thread-safe, sliding-window in-memory rate store for local dev, CI, and testing."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._store: dict[str, list[float]] = {}

    def _prune(self, key: str, now: float, window_seconds: int) -> list[float]:
        cutoff = now - window_seconds
        valid = [t for t in self._store.get(key, []) if t > cutoff]
        self._store[key] = valid
        return valid

    async def check_and_consume(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        amount: int = 1,
    ) -> tuple[bool, int, int]:
        async with self._lock:
            now = time.time()
            timestamps = self._prune(key, now, window_seconds)
            current_count = len(timestamps)

            if current_count + amount <= limit:
                for _ in range(amount):
                    timestamps.append(now)
                self._store[key] = timestamps
                return True, len(timestamps), 0

            oldest = timestamps[0] if timestamps else now
            retry_after = max(1, int(oldest + window_seconds - now))
            return False, current_count, retry_after

    async def increment_with_expiry(
        self,
        key: str,
        window_seconds: int,
        amount: int = 1,
    ) -> int:
        async with self._lock:
            now = time.time()
            timestamps = self._prune(key, now, window_seconds)
            for _ in range(amount):
                timestamps.append(now)
            self._store[key] = timestamps
            return len(timestamps)

    async def get_count(self, key: str, window_seconds: int = 86400) -> int:
        async with self._lock:
            now = time.time()
            timestamps = self._prune(key, now, window_seconds)
            return len(timestamps)

    async def reset(self, key: str | None = None) -> None:
        async with self._lock:
            if key is None:
                self._store.clear()
            else:
                self._store.pop(key, None)


class RedisRateStore:
    """Redis/Upstash sliding-window rate store using atomic sorted sets."""

    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as aioredis

        self._client = aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )

    async def check_and_consume(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        amount: int = 1,
    ) -> tuple[bool, int, int]:
        now = time.time()
        cutoff = now - window_seconds

        pipeline = self._client.pipeline(transaction=True)
        pipeline.zremrangebyscore(key, 0, cutoff)
        pipeline.zcard(key)
        results = await pipeline.execute()
        current_count = int(results[1])

        if current_count + amount <= limit:
            consume_pipe = self._client.pipeline(transaction=True)
            for _ in range(amount):
                member = f"{now}:{uuid4().hex}"
                consume_pipe.zadd(key, {member: now})
            consume_pipe.expire(key, window_seconds + 60)
            await consume_pipe.execute()
            return True, current_count + amount, 0

        # Fetch oldest element timestamp to compute retry-after
        oldest_items = await self._client.zrange(key, 0, 0, withscores=True)
        if oldest_items:
            oldest_ts = float(oldest_items[0][1])
            retry_after = max(1, int(oldest_ts + window_seconds - now))
        else:
            retry_after = max(1, window_seconds)

        return False, current_count, retry_after

    async def increment_with_expiry(
        self,
        key: str,
        window_seconds: int,
        amount: int = 1,
    ) -> int:
        now = time.time()
        cutoff = now - window_seconds

        pipeline = self._client.pipeline(transaction=True)
        pipeline.zremrangebyscore(key, 0, cutoff)
        for _ in range(amount):
            member = f"{now}:{uuid4().hex}"
            pipeline.zadd(key, {member: now})
        pipeline.expire(key, window_seconds + 60)
        pipeline.zcard(key)
        results = await pipeline.execute()
        return int(results[-1])

    async def get_count(self, key: str, window_seconds: int = 86400) -> int:
        now = time.time()
        cutoff = now - window_seconds
        pipeline = self._client.pipeline(transaction=True)
        pipeline.zremrangebyscore(key, 0, cutoff)
        pipeline.zcard(key)
        results = await pipeline.execute()
        return int(results[1])

    async def reset(self, key: str | None = None) -> None:
        if key is None:
            keys = await self._client.keys("learnloop:rate:*")
            if keys:
                await self._client.delete(*keys)
        else:
            await self._client.delete(key)


_in_memory_store: InMemoryRateStore | None = None
_redis_store: RedisRateStore | None = None


def get_rate_store() -> RateStore:
    global _in_memory_store, _redis_store
    settings = get_settings()

    if settings.rate_store_type == "redis" and settings.redis_url:
        if _redis_store is None:
            _redis_store = RedisRateStore(settings.redis_url)
        return _redis_store

    if _in_memory_store is None:
        _in_memory_store = InMemoryRateStore()
    return _in_memory_store
