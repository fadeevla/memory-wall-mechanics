"""Numba JIT-compiled implementations for Find the Duplicate Number."""

import numpy as np
from numba import njit, prange


@njit
def findDuplicate_bit_numba(arr: np.ndarray) -> int:
    """Sequential bit-counting using single-threaded Numba machine code.

    Reads packed memory sequentially. Whether LLVM vectorizes the loop is a
    compiler and CPU question and should be checked from generated assembly.
    """
    n = len(arr) - 1
    duplicate = 0

    temp = n
    max_bit = 0
    while temp > 0:
        max_bit += 1
        temp >>= 1

    for bit in range(max_bit):
        mask = 1 << bit

        # O(1) analytical base count
        period = 1 << (bit + 1)
        half_period = 1 << bit
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        count_base = (full_cycles * half_period) + max(0, remainder - half_period)

        count_nums = 0
        for i in range(len(arr)):
            count_nums += (arr[i] >> bit) & 1

        if count_nums > count_base:
            duplicate |= mask

    return duplicate


@njit(parallel=True)
def findDuplicate_bit_numba_prange(arr: np.ndarray) -> int:
    """Parallel bit-counting using Numba's configured threading backend.

    Each worker scans the full array for a subset of bits. Cache reuse between
    workers is a hypothesis to validate with CPU-specific hardware counters.
    """
    n = len(arr) - 1

    temp = n
    max_bit = 0
    while temp > 0:
        max_bit += 1
        temp >>= 1

    duplicate = 0

    for bit in prange(max_bit):
        mask = 1 << bit

        # O(1) analytical base calculation
        period = 1 << (bit + 1)
        half_period = 1 << bit
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        base_count = (full_cycles * half_period) + max(0, remainder - half_period)

        nums_count = 0
        for i in range(len(arr)):
            if (arr[i] & mask) != 0:
                nums_count += 1

        if nums_count > base_count:
            # Numba recognizes += as a scalar reduction across prange workers.
            duplicate += mask

    return duplicate


@njit
def findDuplicate_bit_optimal_numba(arr: np.ndarray) -> int:
    """Single-pass bit-counting in Numba.

    Maintains bit counters in an L1-resident array and scans memory only once.
    """
    n = len(arr) - 1

    temp_n = n
    max_bit = 0
    while temp_n > 0:
        max_bit += 1
        temp_n >>= 1

    count_nums = np.zeros(max_bit, dtype=np.int32)

    # Single pass over memory
    for i in range(len(arr)):
        temp = arr[i]
        for bit in range(max_bit):
            count_nums[bit] += temp & 1
            temp >>= 1

    duplicate = 0
    for bit in range(max_bit):
        period = 1 << (bit + 1)
        half_period = 1 << bit
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        count_base = (full_cycles * half_period) + max(0, remainder - half_period)

        if count_nums[bit] > count_base:
            duplicate |= 1 << bit

    return duplicate


@njit
def findDuplicate_floyd_numba(arr: np.ndarray) -> int:
    """Floyd's algorithm compiled with Numba (No-Python mode).

    Eliminates CPython interpreter loop overhead so dependent memory access is
    more visible; counters are still required to attribute individual stalls.
    """
    slow = arr[0]
    fast = arr[0]

    while True:
        slow = arr[slow]
        fast = arr[arr[fast]]
        if slow == fast:
            break

    slow2 = arr[0]
    while slow != slow2:
        slow = arr[slow]
        slow2 = arr[slow2]

    return slow


def warmup_numba_kernels():
    """Compiles all Numba JIT kernels ahead of time on small arrays."""
    dummy = np.array([1, 1], dtype=np.int32)
    findDuplicate_bit_numba(dummy)
    findDuplicate_bit_numba_prange(dummy)
    findDuplicate_bit_optimal_numba(dummy)
    findDuplicate_floyd_numba(dummy)
