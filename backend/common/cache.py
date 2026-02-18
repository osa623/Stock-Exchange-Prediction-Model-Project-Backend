"""
In-memory TTL cache for report GET endpoints.

Falls back to dictionary-based cache. Replace with Redis in production
by swapping the backend while keeping the same interface.
"""

import time
import asyncio
import hashlib
import json
from typing import Any
from functools import wraps
from common.logging import get_logger

logger = get_logger(__name__)


class InMemoryCache:
    """Thread-safe in-memory cache with TTL eviction."""

    def __init__(self, default_ttl: int = 300, max_size: int = 2000):
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None):
        async with self._lock:
            # Evict oldest entries if over capacity
            if len(self._store) >= self._max_size:
                self._evict_expired()
                if len(self._store) >= self._max_size:
                    # Remove oldest 10%
                    to_remove = max(1, self._max_size // 10)
                    keys = list(self._store.keys())[:to_remove]
                    for k in keys:
                        del self._store[k]
            expires_at = time.time() + (ttl or self._default_ttl)
            self._store[key] = (value, expires_at)

    async def delete(self, key: str):
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self):
        async with self._lock:
            self._store.clear()

    def _evict_expired(self):
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]

    @property
    def stats(self) -> dict:
        return {
            "size": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (
                round(self._hits / (self._hits + self._misses), 3)
                if (self._hits + self._misses) > 0
                else 0
            ),
        }


def make_cache_key(prefix: str, **kwargs) -> str:
    """Build a deterministic cache key from prefix + sorted kwargs."""
    raw = prefix + ":" + json.dumps(kwargs, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


# ── Global cache instances ───────────────────────────────────────────────

# Public report list — short TTL (2 min)
report_list_cache = InMemoryCache(default_ttl=120, max_size=500)

# Individual report detail — longer TTL (5 min)
report_detail_cache = InMemoryCache(default_ttl=300, max_size=1000)

# Folder tree structure — long TTL (10 min, rarely changes)
folder_tree_cache = InMemoryCache(default_ttl=600, max_size=50)
