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

from duplicate_find.algorithms import ALGORITHMS, ALGORITHM_SPECS

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
    """Test standard cases and require caller-visible input preservation."""
    canonical = np.array(arr, dtype=np.int32)
    input_data = ALGORITHM_SPECS[name].prepare_input(canonical)

    original = input_data.copy()
    result = func(input_data)
    assert result == expected, f"{name} failed on {arr}: expected {expected}, got {result}"
    if isinstance(input_data, np.ndarray):
        np.testing.assert_array_equal(input_data, original)
    else:
        assert input_data == original, f"{name} mutated its input"


@_parametrize("name,func", ALGORITHMS.items())
def test_algorithm_scaled_random(name, func):
    """Test on a larger randomized array with duplicate at known position."""
    N = 1000
    expected_duplicate = 42
    test_arr = list(range(1, N + 1)) + [expected_duplicate]
    random.seed(12345)
    random.shuffle(test_arr)

    input_data = ALGORITHM_SPECS[name].prepare_input(np.array(test_arr, dtype=np.int32))

    result = func(input_data)
    assert result == expected_duplicate, (
        f"{name} failed on randomized N={N}: expected {expected_duplicate}, got {result}"
    )


@_parametrize("name,func", ALGORITHMS.items())
@_parametrize("seed", range(5))
def test_algorithm_generated_valid_inputs(name, func, seed):
    """Exercise duplicates with varying multiplicity and missing values."""
    rng = random.Random(seed)
    n = 25
    duplicate = rng.randint(1, n)
    multiplicity = rng.randint(2, 6)
    remaining = [value for value in range(1, n + 1) if value != duplicate]
    rng.shuffle(remaining)
    values = [duplicate] * multiplicity + remaining[: n + 1 - multiplicity]
    rng.shuffle(values)
    data = ALGORITHM_SPECS[name].prepare_input(np.array(values, dtype=np.int32))
    assert func(data) == duplicate


if __name__ == "__main__":
    # Standalone test runner without requiring pytest installed
    print("Running correctness tests across all algorithms...")
    failed = 0
    total = 0
    for name, func in ALGORITHMS.items():
        for arr, expected in TEST_CASES:
            total += 1
            data = ALGORITHM_SPECS[name].prepare_input(np.array(arr, dtype=np.int32))
            try:
                res = func(data)
                assert res == expected, f"expected {expected}, got {res}"
            except Exception as e:
                print(f"❌ {name} failed on {arr}: {e}")
                failed += 1

        # Also execute a deterministic generated case in the standalone runner.
        generated = list(range(1, 101)) + [42]
        random.Random(12345).shuffle(generated)
        data = ALGORITHM_SPECS[name].prepare_input(np.array(generated, dtype=np.int32))
        total += 1
        try:
            assert func(data) == 42
        except Exception as e:
            print(f"❌ {name} failed generated case: {e}")
            failed += 1

    print(f"\nCompleted {total} test checks: {total - failed} passed, {failed} failed.")
    sys.exit(1 if failed > 0 else 0)
