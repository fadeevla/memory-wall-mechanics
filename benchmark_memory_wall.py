"""287. Find the Duplicate Number - Memory Wall & Hardware Benchmark.

Benchmarking memory hierarchies, TLB misses, and cache locality on modern CPUs.
"""

import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from duplicate_find.algorithms import (
    findDuplicate_sort,
    findDuplicate_set,
    findDuplicate_bs,
    findDuplicate_floyd,
    findDuplicate_sign,
    findDuplicate_bit,
    findDuplicate_bit_optimal,
    findDuplicate_bit_numpy,
    findDuplicate_bit_numpy_full,
    findDuplicate_bit_numba,
    findDuplicate_bit_numba_prange,
    findDuplicate_bit_optimal_numba,
    findDuplicate_floyd_numba,
    warmup_numba_kernels,
    ALGORITHMS,
)
from duplicate_find.memory.hugepage import allocate_hugepage_array
from duplicate_find.benchmark.runner import main, run_benchmark

if __name__ == "__main__":
    main()
