import os
import unittest
from pathlib import Path

from naren import diskcache_fn
from naren._diskcache_fn import _arg_hash


class TestDiskcacheFn(unittest.TestCase):
    def test_diskcache_fn(self):
        def uncached_add(a, b):
            return a + b

        # Test the diskcache_fn function
        @diskcache_fn(cache_dir="/tmp/fn_cache")
        def add(a, b):
            return uncached_add(a, b)

        input = (1, 2)
        res = add(*input)

        key = _arg_hash(input, {})
        cache_file = Path("/tmp/fn_cache") / f"add_{key}.pkl"
        self.assertTrue(cache_file.exists(), f"Cache file {cache_file} not found")

        cached_res = add(*input)
        self.assertEqual(
            res, cached_res, "Cached result does not match original result"
        )
        uncached_res = uncached_add(*input)
        self.assertEqual(
            cached_res, uncached_res, "Cached result does not match uncached result"
        )

        # Clean up
        os.remove(cache_file)
