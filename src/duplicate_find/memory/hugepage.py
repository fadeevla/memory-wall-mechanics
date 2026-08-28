import mmap
from typing import Tuple, Optional
import numpy as np

# Linux-specific MAP_HUGETLB flag (default fallback: 0x40000)
MAP_HUGETLB = getattr(mmap, "MAP_HUGETLB", 0x40000)
HUGE_PAGE_SIZE = 2 * 1024 * 1024  # 2MB default HugePage size on x86_64


def allocate_hugepage_array(
    num_elements: int, dtype=np.int32
) -> Tuple[np.ndarray, mmap.mmap]:
    """Allocates a NumPy array backed by Linux 2MB HugePages using mmap.

    Args:
        num_elements: Number of elements in the 1D array.
        dtype: NumPy data type.

    Returns:
        A tuple of (mutable_np_array, raw_mmap_buffer).
        The caller must close raw_mmap_buffer when done to free physical resources.
    """
    element_size = np.dtype(dtype).itemsize
    required_bytes = num_elements * element_size

    # Align allocation to 2MB HugePage boundary
    if required_bytes % HUGE_PAGE_SIZE != 0:
        padding = HUGE_PAGE_SIZE - (required_bytes % HUGE_PAGE_SIZE)
        allocation_size = required_bytes + padding
    else:
        allocation_size = required_bytes

    flags = mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS | MAP_HUGETLB

    try:
        raw_buffer = mmap.mmap(-1, allocation_size, flags=flags)
    except OSError as e:
        raise RuntimeError(
            "HugePage allocation failed. Did you reserve pages in the kernel?\n"
            "Run: sudo sysctl -w vm.nr_hugepages=1024"
        ) from e

    mutable_array = np.ndarray(
        buffer=raw_buffer, dtype=dtype, shape=(num_elements,), offset=0
    )

    return mutable_array, raw_buffer
