"""Correctness tests for all duplicate-finding algorithms."""

import os
import sys
import random
import numpy as np

try:
    import pytest
except ImportError:
    pytest = None

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from duplicate_find.algorithms import ALGORITHMS

TEST_CASES = [
    ([1, 3, 4, 2, 2], 2),
    ([3, 1, 3, 4, 2], 3),
    ([3, 3, 3, 3, 3], 3),
    ([1, 1], 1),
    ([1, 2, 2], 2),
    ([2, 2, 2, 2, 2], 2),
    ([2, 5, 9, 6, 9, 3, 8, 9, 7, 1], 9),
    ([1, 4, 4, 2, 4], 4),
]


def _parametrize(*args, **kwargs):
    if pytest is not None:
        return pytest.mark.parametrize(*args, **kwargs)
    return lambda f: f


@_parametrize("name,func", ALGORITHMS.items())
@_parametrize("arr,expected", TEST_CASES)
def test_algorithm_basic_cases(name, func, arr, expected):
    """Test standard cases on both Python lists and NumPy arrays."""
    if "numba" in name:
        input_data = np.array(arr, dtype=np.int32)
    elif "numpy" in name:
        input_data = np.array(arr, dtype=np.int32)
    else:
        input_data = list(arr)

    result = func(input_data)
    assert result == expected, f"{name} failed on {arr}: expected {expected}, got {result}"


@_parametrize("name,func", ALGORITHMS.items())
def test_algorithm_scaled_random(name, func):
    """Test on a larger randomized array with duplicate at known position."""
    N = 1000
    expected_duplicate = 42
    test_arr = list(range(1, N + 1)) + [expected_duplicate]
    random.seed(12345)
    random.shuffle(test_arr)

    if "numba" in name or "numpy" in name:
        input_data = np.array(test_arr, dtype=np.int32)
    else:
        input_data = list(test_arr)

    result = func(input_data)
    assert result == expected_duplicate, (
        f"{name} failed on randomized N={N}: expected {expected_duplicate}, got {result}"
    )


if __name__ == "__main__":
    # Standalone test runner without requiring pytest installed
    print("Running correctness tests across all algorithms...")
    failed = 0
    total = 0
    for name, func in ALGORITHMS.items():
        for arr, expected in TEST_CASES:
            total += 1
            if "numba" in name or "numpy" in name:
                data = np.array(arr, dtype=np.int32)
            else:
                data = list(arr)
            try:
                res = func(data)
                assert res == expected, f"expected {expected}, got {res}"
            except Exception as e:
                print(f"❌ {name} failed on {arr}: {e}")
                failed += 1

    print(f"\nCompleted {total} test checks: {total - failed} passed, {failed} failed.")
    sys.exit(1 if failed > 0 else 0)
