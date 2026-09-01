"""Baseline algorithm implementations for Find the Duplicate Number (LeetCode 287).

Constraint Analysis:
- Problem Constraint 1: Must NOT modify the input array.
- Problem Constraint 2: Must use only O(1) constant extra space.

Implementations below are categorized into:
1. Fully Compliant:
   - `findDuplicate_floyd` (O(N) time, O(1) space, read-only)
   - `findDuplicate_bs` (O(N log N) time, O(1) space, read-only)
   - `findDuplicate_bit` (O(N log M) time, O(1) space, read-only)
   - `findDuplicate_bit_optimal` is read-only but uses O(log M) counters.
2. Constraint-Violating Baselines (included for comparative hardware benchmarking):
   - `findDuplicate_set`: Violates space constraint with O(N) heap allocations.
   - `findDuplicate_sort`: Violates read-only constraint if in-place; violates space
     constraint if a defensive copy is used.
   - `findDuplicate_sign`: Violates read-only constraint during traversal (thread-unsafe).
"""

from typing import List, Sequence


def findDuplicate_sort(nums: Sequence[int]) -> int:
    """Sort-based duplicate finding.

    To adhere to the read-only constraint without mutating caller data, this creates
    a sorted copy, incurring O(N) auxiliary space.

    Time: O(N log N), Space: O(N) due to defensive copy.
    """
    sorted_nums = sorted(nums)
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i] == sorted_nums[i + 1]:
            return sorted_nums[i]
    return -1


def findDuplicate_set(nums: Sequence[int]) -> int:
    """Hash-set duplicate detection.

    Violates the O(1) space constraint by storing up to N elements.
    The set table adds substantial allocation and hashing overhead. Existing
    integer objects are referenced rather than copied when ``nums`` is a list.

    Time: O(N), Space: O(N).
    """
    seen = set()
    for num in nums:
        if num in seen:
            return num
        seen.add(num)
    return -1


def findDuplicate_bs(nums: Sequence[int]) -> int:
    """Binary search over the candidate answer range [1, n].

    Fully compliant: read-only and O(1) extra space.

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

    Fully compliant: O(N) time, O(1) space, and read-only.
    Its data-dependent pointer chasing can limit prefetching and cache locality;
    hardware counters are needed to attribute a slowdown to specific causes.

    Time: O(N), Space: O(1).
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

    Temporarily negates visited indices to track cycle entry.
    Restores the array to its original state before returning.
    Violates strict immutability during execution and is thread-unsafe.

    Time: O(N), Space: O(1). Negation creates integer objects in CPython, but
    integers are not tracked by the cyclic garbage collector.
    """
    pos = 0
    duplicate = -1
    try:
        while True:
            if nums[pos] < 0:
                duplicate = pos
                break
            nums[pos] = -nums[pos]
            pos = -nums[pos]
    finally:
        # Guarantee restoration of modified elements
        pos2 = 0
        while nums[pos2] < 0:
            nums[pos2] = -nums[pos2]
            pos2 = nums[pos2]

    return duplicate


def findDuplicate_bit(nums: Sequence[int]) -> int:
    """Sequential bit-counting algorithm.

    Fully compliant: read-only and O(1) space.
    Computes expected bit distribution analytically in O(1) and scans
    the array sequentially for each bit position.

    Time: O(N log M), Space: O(1).
    """
    n = len(nums) - 1
    duplicate = 0
    max_bit = n.bit_length()

    for bit in range(max_bit):
        mask = 1 << bit
        count_nums = 0

        # O(1) analytical base calculation
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
    """Single-pass bit-counting algorithm.

    Fully compliant: read-only, single memory pass.
    Maintains max_bit counters and updates them via incremental bit shifts.

    Time: O(N log M), Space: O(log M) counters.
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
