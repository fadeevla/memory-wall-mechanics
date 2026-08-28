"""HugePages memory allocator helper (backward compatibility redirect)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from duplicate_find.memory.hugepage import allocate_hugepage_array, MAP_HUGETLB, HUGE_PAGE_SIZE

if __name__ == "__main__":
    import numpy as np

    N = 10**8
    try:
        huge_arr, memory_buffer = allocate_hugepage_array(N, dtype=np.int32)
        huge_arr[0] = 42
        huge_arr[-1] = 999
        print(f"✅ Successfully allocated {len(huge_arr)} elements in HugePages.")
        print(f"First: {huge_arr[0]}, Last: {huge_arr[-1]}")
    finally:
        if "memory_buffer" in locals():
            memory_buffer.close()
            print("Memory unmapped and returned to OS.")
