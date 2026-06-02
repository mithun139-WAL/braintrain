import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("response_cache")

class ResponseCache:
    def __init__(self, max_size: int = 20, default_ttl_seconds: float = 300.0):
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieves cached item if it exists and has not expired."""
        item = self.cache.get(key)
        if not item:
            return None

        # Expiry check
        if time.time() > item["expires_at"]:
            logger.info("response_cache | expired cache key: %s", key)
            self.invalidate(key)
            return None

        logger.debug("response_cache | hit key: %s", key)
        return item["value"]

    def set(self, key: str, value: Any, ttl_seconds: float = None) -> None:
        """Caches an item with a given TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        
        # Enforce max size limit by eviction
        if len(self.cache) >= self.max_size:
            # Evict oldest or expired items
            expired_keys = [k for k, v in self.cache.items() if time.time() > v["expires_at"]]
            if expired_keys:
                for k in expired_keys:
                    self.invalidate(k)
            else:
                # Evict first key arbitrarily to keep size bounded
                oldest_key = next(iter(self.cache))
                self.invalidate(oldest_key)

        expires_at = time.time() + ttl
        self.cache[key] = {
            "value": value,
            "expires_at": expires_at,
        }
        logger.debug("response_cache | cached key: %s (ttl: %.1fs)", key, ttl)

    def invalidate(self, key: str) -> None:
        """Removes an item from the cache."""
        self.cache.pop(key, None)
        logger.debug("response_cache | invalidated key: %s", key)

    def clear(self) -> None:
        """Clears all cached items."""
        self.cache.clear()
        logger.info("response_cache | cache cleared")
