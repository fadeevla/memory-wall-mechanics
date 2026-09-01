"""NumPy vectorized implementations for Find the Duplicate Number."""

from typing import Sequence
import numpy as np


def findDuplicate_bit_numpy(nums: Sequence[int]) -> int:
    """NumPy loop-over-bits implementation with C-speed inner summation.

    Time: O(N log M), Peak extra space: O(N). Each vectorized expression
    materializes temporary arrays, which is intentionally measured here.
    """
    if not isinstance(nums, np.ndarray):
        arr = np.array(nums, dtype=np.uint32)
    else:
        arr = nums

    n = len(arr) - 1
    duplicate = 0
    max_bit = n.bit_length()

    for bit in range(max_bit):
        mask = 1 << bit

        period = 1 << (bit + 1)
        half_period = 1 << bit
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        count_base = (full_cycles * half_period) + max(0, remainder - half_period)

        count_nums = np.sum((arr >> bit) & 1)

        if count_nums > count_base:
            duplicate |= mask

    return int(duplicate)


def findDuplicate_bit_numpy_full(nums: Sequence[int]) -> int:
    """Fully broadcasted 2D NumPy implementation.

    Creates an (N, max_bit) intermediate matrix in RAM via broadcasting.
    Time: O(N log M), Space: O(N log M) RAM explosion.
    """
    if not isinstance(nums, np.ndarray):
        arr = np.array(nums, dtype=np.int32)
    else:
        arr = nums

    n = len(arr) - 1
    max_bit = n.bit_length()

    bits = np.arange(max_bit, dtype=np.int32)

    # Analytical count_base for all bits simultaneously
    period = 1 << (bits + 1)
    half_period = 1 << bits
    full_cycles = (n + 1) // period
    remainder = (n + 1) % period
    count_base = (full_cycles * half_period) + np.maximum(0, remainder - half_period)

    # 2D broadcasted bit matrix
    bit_matrix = (arr[:, None] >> bits) & 1
    count_nums = np.sum(bit_matrix, axis=0)

    diff = count_nums > count_base
    duplicate = np.sum(diff * (1 << bits))

    return int(duplicate)
