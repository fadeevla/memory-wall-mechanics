"""Baseline algorithm implementations for Find the Duplicate Number.

All functions accept a list or array `nums` of size n + 1 containing
values from 1 to n with at least one duplicate.
"""

from typing import List, Sequence


def findDuplicate_sort(nums: List[int]) -> int:
    """Sort-based duplicate finding.

    Time: O(N log N), Space: O(1) in-place (mutates input).
    """
    nums.sort()
    for i in range(len(nums) - 1):
        if nums[i] == nums[i + 1]:
            return nums[i]
    return -1


def findDuplicate_set(nums: Sequence[int]) -> int:
    """Hash-set duplicate finding.

    Time: O(N), Space: O(N) (PyObject overhead and heap allocation).
    """
    seen = set()
    for num in nums:
        if num in seen:
            return num
        seen.add(num)
    return -1


def findDuplicate_bs(nums: Sequence[int]) -> int:
    """Binary search over the answer range [1, n].

    Time: O(N log N), Space: O(1).
    """
    n = len(nums) - 1
    left, right = 1, n
    while left < right:
        mid = left + (right - left) // 2
        count = sum(1 for num in nums if num <= mid)
        if count > mid:
            right = mid
        else:
            left = mid + 1
    return left


def findDuplicate_floyd(nums: Sequence[int]) -> int:
    """Floyd's Tortoise and Hare cycle detection algorithm.

    Time: O(N), Space: O(1).
    Theoretical ideal, but in practice suffers heavily from Pointer Chasing
    and TLB cache misses on large random arrays.
    """
    slow = nums[0]
    fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break

    slow2 = nums[0]
    while slow != slow2:
        slow = nums[slow]
        slow2 = nums[slow2]

    return slow


def findDuplicate_sign(nums: List[int]) -> int:
    """Array mutation (sign-marking) duplicate finding.

    Time: O(N), Space: O(1).
    Mutates input temporarily; causes PyObject allocations in CPython.
    """
    pos = 0
    duplicate = -1
    while True:
        if nums[pos] < 0:
            duplicate = pos
            break
        nums[pos] = -nums[pos]
        pos = -nums[pos]

    # Restore array to original state
    pos2 = 0
    while nums[pos2] < 0:
        nums[pos2] = -nums[pos2]
        pos2 = nums[pos2]

    return duplicate


def findDuplicate_bit(nums: Sequence[int]) -> int:
    """Sequential bit-counting algorithm in pure Python.

    Time: O(N log M), Space: O(1).
    """
    n = len(nums) - 1
    duplicate = 0
    max_bit = n.bit_length()

    for bit in range(max_bit):
        mask = 1 << bit
        count_nums = 0

        period = 1 << (bit + 1)
        half_period = 1 << bit
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        count_base = (full_cycles * half_period) + max(0, remainder - half_period)

        for num in nums:
            if num & mask:
                count_nums += 1

        if count_nums > count_base:
            duplicate |= mask

    return duplicate


def findDuplicate_bit_optimal(nums: Sequence[int]) -> int:
    """Single-pass bit-counting algorithm in pure Python.

    Time: O(N log M), Space: O(log M) counters in memory.
    """
    n = len(nums) - 1
    max_bit = n.bit_length()
    count_nums = [0] * max_bit

    for num in nums:
        temp = num
        for bit in range(max_bit):
            count_nums[bit] += temp & 1
            temp >>= 1
            if temp == 0:
                break

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
