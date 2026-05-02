from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

from polymarket.api.cache import TTLCache


class TestTTLCacheHits:
    def test_caches_value_within_ttl(self) -> None:
        cache = TTLCache(ttl_seconds=10.0)
        compute = MagicMock(return_value="v")
        assert cache.get_or_compute("k", compute) == "v"
        assert cache.get_or_compute("k", compute) == "v"
        assert compute.call_count == 1

    def test_recomputes_after_ttl_expires(self) -> None:
        cache = TTLCache(ttl_seconds=0.05)
        compute = MagicMock(side_effect=["a", "b"])
        assert cache.get_or_compute("k", compute) == "a"
        time.sleep(0.08)
        assert cache.get_or_compute("k", compute) == "b"
        assert compute.call_count == 2

    def test_distinct_keys_compute_independently(self) -> None:
        cache = TTLCache(ttl_seconds=10.0)
        compute_a = MagicMock(return_value=1)
        compute_b = MagicMock(return_value=2)
        assert cache.get_or_compute("a", compute_a) == 1
        assert cache.get_or_compute("b", compute_b) == 2
        assert cache.get_or_compute("a", compute_a) == 1
        assert compute_a.call_count == 1
        assert compute_b.call_count == 1


class TestTTLCacheMissTtl:
    def test_none_uses_miss_ttl(self) -> None:
        cache = TTLCache(ttl_seconds=10.0, miss_ttl_seconds=0.05)
        compute = MagicMock(side_effect=[None, "found"])
        assert cache.get_or_compute("k", compute) is None
        assert cache.get_or_compute("k", compute) is None
        assert compute.call_count == 1
        time.sleep(0.08)
        assert cache.get_or_compute("k", compute) == "found"
        assert compute.call_count == 2

    def test_falls_back_to_ttl_when_miss_ttl_not_set(self) -> None:
        cache = TTLCache(ttl_seconds=10.0)
        compute = MagicMock(return_value=None)
        cache.get_or_compute("k", compute)
        cache.get_or_compute("k", compute)
        assert compute.call_count == 1


class TestTTLCacheInvalidation:
    def test_invalidate_removes_key(self) -> None:
        cache = TTLCache(ttl_seconds=10.0)
        compute = MagicMock(side_effect=["a", "b"])
        cache.get_or_compute("k", compute)
        cache.invalidate("k")
        assert cache.get_or_compute("k", compute) == "b"
        assert compute.call_count == 2

    def test_invalidate_unknown_key_is_safe(self) -> None:
        cache = TTLCache(ttl_seconds=10.0)
        cache.invalidate("missing")

    def test_clear_drops_all_entries(self) -> None:
        cache = TTLCache(ttl_seconds=10.0)
        compute_a = MagicMock(side_effect=["a1", "a2"])
        compute_b = MagicMock(side_effect=["b1", "b2"])
        cache.get_or_compute("a", compute_a)
        cache.get_or_compute("b", compute_b)
        cache.clear()
        assert cache.get_or_compute("a", compute_a) == "a2"
        assert cache.get_or_compute("b", compute_b) == "b2"


class TestTTLCacheEviction:
    def test_evicts_when_over_max_size(self) -> None:
        cache = TTLCache(ttl_seconds=10.0, max_size=4)
        for i in range(4):
            cache.get_or_compute(i, lambda i=i: i)
        cache.get_or_compute(99, lambda: 99)
        assert cache.get_or_compute(99, lambda: -1) == 99
        recomputed = 0
        for i in range(4):
            sentinel = MagicMock(return_value=i + 1000)
            cache.get_or_compute(i, sentinel)
            if sentinel.called:
                recomputed += 1
        assert recomputed >= 1


class TestTTLCacheThreadSafety:
    def test_concurrent_access_does_not_crash(self) -> None:
        cache = TTLCache(ttl_seconds=5.0)

        def worker(key: int) -> None:
            for _ in range(50):
                cache.get_or_compute(key % 8, lambda k=key: f"v{k}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert cache.get_or_compute(0, lambda: "fresh") is not None
