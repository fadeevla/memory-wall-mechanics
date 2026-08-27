import mmap
import numpy as np
import os

# 1. Define the Linux-specific MAP_HUGETLB flag.
# Python's mmap module exposes this on modern Linux builds, but we use a 
# fallback (0x40000) just in case the Python binary was compiled differently.
MAP_HUGETLB = getattr(mmap, 'MAP_HUGETLB', 0x40000)

def allocate_hugepage_array(num_elements: int, dtype=np.int32) -> np.ndarray:
    # 2. Calculate the required memory size.
    element_size = np.dtype(dtype).itemsize
    required_bytes = num_elements * element_size
    
    # 3. Align the allocation to the HugePage boundary.
    # Linux requires HugePage allocations to be strict multiples of the page size.
    # The default HugePage size on most x86_64 systems is 2 Megabytes.
    HUGE_PAGE_SIZE = 2 * 1024 * 1024
    
    if required_bytes % HUGE_PAGE_SIZE != 0:
        # Round up to the nearest 2MB boundary
        padding = HUGE_PAGE_SIZE - (required_bytes % HUGE_PAGE_SIZE)
        allocation_size = required_bytes + padding
    else:
        allocation_size = required_bytes

    print(f"Requesting {allocation_size / (1024*1024):.1f} MB of HugePage memory...")

    # 4. Execute the system call.
    # -1: Anonymous memory (no file descriptor)
    # MAP_PRIVATE: Local to this process
    # MAP_ANONYMOUS: Not backed by a file
    # MAP_HUGETLB: Demand HugePages from the Linux kernel
    flags = mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS | MAP_HUGETLB
    
    try:
        raw_buffer = mmap.mmap(-1, allocation_size, flags=flags)
    except OSError as e:
        raise RuntimeError(
            "HugePage allocation failed. Did you reserve pages in the kernel?\n"
            "Run: sudo sysctl -w vm.nr_hugepages=500"
        ) from e

    # 5. Map the raw C-buffer to a NumPy array without copying any data.
    # We slice the buffer `[:required_bytes]` to hide the padding we added for alignment.
    array = np.frombuffer(raw_buffer[:required_bytes], dtype=dtype)
    
    # Make the array writeable (frombuffer makes it read-only by default in some versions)
    # Since we own the anonymous mmap, writing is completely safe.
    mutable_array = np.ndarray(
        buffer=raw_buffer, 
        dtype=dtype, 
        shape=(num_elements,), 
        offset=0
    )
    
    return mutable_array, raw_buffer

if __name__ == '__main__':
    # Let's allocate our 10^8 elements (approx 400 MB)
    N = 10**8
    
    try:
        # 1. Allocate
        huge_arr, memory_buffer = allocate_hugepage_array(N, dtype=np.int32)
        
        # 2. Use it just like a normal NumPy array
        huge_arr[0] = 42
        huge_arr[-1] = 999
        
        print(f"✅ Successfully allocated {len(huge_arr)} elements in HugePages.")
        print(f"First: {huge_arr[0]}, Last: {huge_arr[-1]}")
        
    finally:
        # 3. Explicitly free the hardware resources when done
        if 'memory_buffer' in locals():
            memory_buffer.close()
            print("Memory unmapped and returned to OS.")