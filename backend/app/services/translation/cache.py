"""
Thread-safe in-memory cache for translated strings with TTL and LRU eviction.
Reduces latency and avoids duplicate external Google Cloud API calls.
"""

import time
import hashlib
from typing import Optional, Dict, Tuple
from collections import OrderedDict


class TranslationCache:
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 86400):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[str, float]] = OrderedDict()

    @staticmethod
    def _make_key(text: str, source_lang: str, target_lang: str) -> str:
        raw_key = f"{source_lang}:{target_lang}:{text}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        if not text:
            return None
        key = self._make_key(text, source_lang, target_lang)
        if key not in self._cache:
            return None

        translated, timestamp = self._cache[key]
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            return None

        # Move to end for LRU order
        self._cache.move_to_end(key)
        return translated

    def set(self, text: str, source_lang: str, target_lang: str, translated: str) -> None:
        if not text or not translated:
            return
        key = self._make_key(text, source_lang, target_lang)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (translated, time.time())

        # Enforce max size (LRU eviction)
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()

    def size(self) -> int:
        return len(self._cache)


# Global singleton cache instance
translation_cache = TranslationCache()
