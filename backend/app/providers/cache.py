"""In-memory cache with per-key TTL and stale-while-revalidate support.

Assumes a single-process backend deployment (single Uvicorn worker).
Redis can replace the storage backend later without changing call sites.

Observability: exposes hit/miss counters for periodic logging.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheEntry:
    """A single cached value with creation timestamp."""

    __slots__ = ("value", "created_at")

    def __init__(self, value: Any, created_at: float) -> None:
        self.value = value
        self.created_at = created_at


class ProviderCache:
    """Thread-safe in-memory cache with per-key TTL.

    Features:
    - Per-key TTL with configurable default.
    - Stale data retrieval: get_stale() returns expired entries
      when the provider is down.
    - Hit/miss counters for observability.

    Not suitable for multi-worker deployments — see architecture
    proposal for Redis migration path.
    """

    def __init__(self, default_ttl: float = 60.0) -> None:
        self._store: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str, ttl: float | None = None) -> Any | None:
        """Return the cached value if fresh, otherwise None."""
        effective_ttl = ttl if ttl is not None else self._default_ttl
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if time.time() - entry.created_at >= effective_ttl:
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    def get_stale(self, key: str) -> Any | None:
        """Return the cached value regardless of TTL expiry.

        Used for stale-while-revalidate: serve stale data when the
        provider is unavailable rather than returning an error.
        """
        with self._lock:
            entry = self._store.get(key)
            return entry.value if entry is not None else None

    def set(self, key: str, value: Any) -> None:
        """Store a value with the current timestamp."""
        with self._lock:
            self._store[key] = CacheEntry(value=value, created_at=time.time())

    def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._store.clear()

    def stats(self) -> dict[str, int]:
        """Return hit/miss counters for observability."""
        with self._lock:
            total = self._hits + self._misses
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_pct": round(
                    (self._hits / total * 100) if total > 0 else 0.0, 1
                ),
                "size": len(self._store),
            }

    def reset_stats(self) -> None:
        """Reset hit/miss counters (call after logging stats)."""
        with self._lock:
            self._hits = 0
            self._misses = 0

    def log_stats(self, prefix: str = "cache") -> None:
        """Log current cache statistics at INFO level and reset."""
        s = self.stats()
        logger.info(
            "%s stats: hits=%d misses=%d hit_rate=%.1f%% size=%d",
            prefix,
            s["hits"],
            s["misses"],
            s["hit_rate_pct"],
            s["size"],
        )
        self.reset_stats()
