from __future__ import annotations

import threading
import time
from typing import Any, Callable, Hashable, TypeVar

T = TypeVar("T")


class TTLCache:
    def __init__(
        self,
        ttl_seconds: float,
        max_size: int = 512,
        miss_ttl_seconds: float | None = None,
    ) -> None:
        self._ttl = float(ttl_seconds)
        self._miss_ttl = float(
            miss_ttl_seconds if miss_ttl_seconds is not None else ttl_seconds
        )
        self._max = int(max_size)
        self._lock = threading.Lock()
        self._store: dict[Hashable, tuple[float, Any]] = {}

    def _ttl_for(self, value: Any) -> float:
        return self._miss_ttl if value is None else self._ttl

    def _evict_if_full(self) -> None:
        if len(self._store) < self._max:
            return
        victims = sorted(self._store.items(), key=lambda kv: kv[1][0])
        for k, _ in victims[: max(1, self._max // 4)]:
            self._store.pop(k, None)

    def get_or_compute(self, key: Hashable, compute: Callable[[], T]) -> T:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is not None and entry[0] > now:
                return entry[1]
        value = compute()
        with self._lock:
            self._evict_if_full()
            self._store[key] = (time.monotonic() + self._ttl_for(value), value)
        return value

    def invalidate(self, key: Hashable) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


__all__ = ["TTLCache"]
