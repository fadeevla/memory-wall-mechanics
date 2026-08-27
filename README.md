## Usage
```bash
sudo ./bench/01_setup_runtime.sh
# Optionally ./bench/02_setup_grub_isolation.sh
bench/run.sh
```

## Abstract

Empirical profiling and benchmarking on large arrays ($N=10^8$) demonstrate that high-load system performance is fundamentally constrained by memory hierarchies and bandwidth limits rather than abstract Big-O mathematical complexity. Mathematically optimal $O(N)$ algorithms relying on random memory access degrade catastrophically due to L3 cache exhaustion and Translation Lookaside Buffer (TLB) misses. Conversely, sequentially accessing data using an $O(N \log N)$ bit-manipulation approach outperforms them by keeping hardware prefetchers and vector registers fully fed.

  

## 1. Theoretical Baselines & CPython Interpreter Bottlenecks

Performance in high-load systems is constrained by memory hierarchies rather than pure mathematical complexity. Initial baseline implementations expose severe interpreter overheads:
  

- **Hash Table (`set`):** Exhibits $O(N)$ time and space complexity. It is fast on small arrays, but suffers from dynamic allocation of `PyObject` structures and re-hashing overhead under collisions.
    
- **Sorting (`sort`):** Provides a data-independent, stable execution time through sequential memory access, though it mutates the input array and incurs sorting costs.


## 2. The $O(1)$ Space Illusion: Pointer Chasing & TLB Exhaustion

Graph cycle-detection algorithms represent theoretical ideals that break down under silicon realities:

- **Floyd’s Cycle-Finding Algorithm (`floyd`):** Operates in $O(N)$ time and $O(1)$ space without auxiliary allocations.
    
- **The Pointer Chasing Bottleneck:** Random memory lookups (`nums[nums[slow]]`) destroy hardware branch prediction and prefetcher efficiency.
    
- **TLB and Cache Collapse:** On massive datasets ($N=10^8$), random jumps overwhelm the Translation Lookaside Buffer (TLB), triggering cascading Page Walks and up to $95.6\%$ dTLB load misses.
    

```python
def findDuplicate_floyd(nums):
    slow = nums[0]
    fast = nums[nums[0]]
    while slow != fast:
        slow = nums[slow]
        fast = nums[nums[fast]]
    return slow
```

## 3. Cache-Locality, SIMD, and Branchless Execution

To bypass the memory wall, algorithms must prioritize strict sequential access patterns and hardware empathy:

- **Sequential Bit Manipulation:** Scanning arrays bit-by-bit ensures contiguous memory reads, allowing CPU hardware prefetchers to operate at maximum efficiency.
    
- **Branchless Design vs. Branch Divergence:** Avoiding dynamic short-circuit loops prevents branch divergence, enabling compilers to apply SIMD (AVX2) vectorization.
    
- **The Memory Blow-Up Trap:** Full NumPy vectorization via broadcasting materializes large $O(N \log N)$ matrices in RAM, mirroring the memory explosion of standard Transformer Attention mechanisms and requiring Kernel Fusion (comparable to FlashAttention).
        

```python
@njit
def findDuplicate_bit_optimal_numba(arr: np.ndarray) -> int:
	N = len(arr)
    count_nums = np.zeros(max_bit, dtype=np.int32)
    max_bit = math.ceil(mah.log2(N)) - 1 # max_bit=27 for N=10**8
    for i in range(N):
        temp = arr[i]
        for bit in range(max_bit):
            count_nums[bit] += temp & 1
            temp >>= 1
    return duplicate
```

## 4. Bare-Metal Scaling & Constructive Cache Sharing

Executing multi-threaded JIT kernels reveals the physical limits of motherboard data buses and CPU core topologies:

- **Defeating SMT (Hyper-Threading):** Logical threads contend for shared execution units and memory controllers in memory-bound tasks; scaling requires pinning processes to physical cores.
    
- **OS Jitter Isolation:** Reserving control plane cores for the operating system prevents background interrupts from desynchronizing working threads.
    
- **Constructive Cache Sharing:** Synchronized multi-threaded execution allows parallel workers to pull cached lines directly from the shared L3 cache rather than external RAM, pushing effective throughput beyond physical motherboard limits.
    

```python
@njit(parallel=True)
def findDuplicate_bit_numba_prange(nums):
    n = len(nums)
    duplicate = 0
    for bit in prange(32):
        mask = 1 << bit
        base_count = 0
        nums_count = 0
        for i in range(n):
            if i & mask:
                base_count += 1
            if nums[i] & mask:
                nums_count += 1
        if nums_count > base_count:
            duplicate |= mask
    return duplicate
```
### **Hardware Validation: ASUS FA507NV & Constructive Cache Sharing**

- **Hardware Specifications:** Benchmarked on an ASUS TUF Gaming A15 (model FA507NV-LP110W) featuring an **AMD Ryzen 5 7535HS** processor (16 MB L3 cache) and dual-channel **DDR5-4800** SO-DIMM RAM.
    
- **The Theoretical RAM Limit:** The physical memory bus bandwidth for dual-channel DDR5-4800 has a strict theoretical ceiling of **76.8 GB/s**.
    
- **The Effective Throughput Phenomenon:** Under isolated multi-threaded execution (`NUMBA_NUM_THREADS=5` on 5 physical cores), the benchmark recorded an effective throughput of **92.6 GB/s** (surpassing the hardware RAM limit by ~20%).
    
- **Mechanics of Cache Overlap:** Because threads advance through the contiguous array in strict lockstep, the memory controller fetches a 64-byte cache line into the L3 cache for the leading thread. Subsequent threads intercept those same bytes directly from the L3 ring bus rather than hitting external RAM, creating an effective throughput multiplier identical to the mechanics behind **Multi-Query Attention (MQA)** and **Grouped-Query Attention (GQA)** in modern LLMs.

## **5. Architectural Anomalies & Anti-Patterns: Array Mutation (`sign`)**

The array mutation approach achieves $O(1)$ space complexity by marking visited nodes using sign bits. However, in CPython, it turns into an anti-pattern:

- **The PyObject Allocation Trap:** Python numbers are immutable. Negating values (`-nums[index]`) forces heap allocations for new `PyObject` instances on every iteration.
    
- **GC Thrashing:** Mass allocation overloads generations of the Garbage Collector, causing frequent Stop-the-World pauses.
    
- **Execution Variance:** Early exit paths cause high P99 latency dispersion based on data distribution.
### Benchmark Performance Overview ($N=10^8$ Threads/Cores Context)

| **Algorithm / Configuration**      | $N=10^1$  | $N=10^5$ | $N=10^6$  | $N=10^7$   | $N=10^8$        |
| ---------------------------------- | --------- | -------- | --------- | ---------- | --------------- |
| **findDuplicate_bit_numba_prange** | 419.89 ms | 3.16 ms  | 0.89 ms   | 10.54 ms   | **116.62 ms**   |
| **findDuplicate_bit_numba**        | 97.81 ms  | 0.12 ms  | 1.53 ms   | 34.87 ms   | **448.42 ms**   |
| **findDuplicate_set**              | 0.00 ms   | 4.66 ms  | 104.44 ms | 2335.17 ms | **31414.68 ms** |
| **findDuplicate_floyd**            | 0.00 ms   | 3.79 ms  | 105.97 ms | 5707.12 ms | **64150.53 ms** |
```python
def findDuplicate_sign(nums):
    for i in range(len(nums)):
        index = abs(nums[i]) - 1
        if nums[index] < 0:
            return abs(nums[i])
        nums[index] = -nums[index]
```
## **6. Comprehensive Performance Overview ($N=10^8$)**

|**Algorithm**|**Time / Space Complexity**|**Execution Time (N=108)**|**Memory Locality**|**Primary Architectural Bottleneck**|
|---|---|---|---|---|
|**sign**|$O(N) / O(1)$|$\approx 35,700$ ms|Random Access|`PyObject` heap allocations & GC thrashing|
|**set**|$O(N) / O(N)$|$\approx 31,400$ ms|Hashing|Dynamic memory fragmentation|
|**floyd**|$O(N) / O(1)$|$\approx 64,150$ ms|Pointer Chasing|TLB & Cache Misses|
|**sort**|$O(N \log N) / O(1)$|$\approx 46,950$ ms|Sequential|Element permutation overhead|
|**bit_numba**|$O(N \log N) / O(1)$|$\approx 400$ ms|Sequential|Single-core RAM bandwidth limit|
|**bit_numba_prange**|$O(N \log N) / O(1)$|**116.62 ms**|Sequential (Cache Overlap)|Physical memory controller limit (Memory Wall)|

## **7. From Bare-Metal CPU Profiling to GPU Triton Kernels**

The low-level hardware phenomena observed in these CPU benchmarks directly translate to designing high-performance Triton and CUDA kernels for LLM infrastructure:

- **Hardware Event Profiling:** Utilizing tools like `perf stat` to track TLB and cache misses identifies memory-bound execution states, guiding memory layout optimizations.
    
- **Kernel Fusion:** Avoiding intermediate memory allocations by aggregating computations within L1/L2 caches mirrors the architectural principles behind FlashAttention.
    
- **Warp Divergence:** Data-dependent branching within GPU execution warps mirrors CPU branch divergence, degrading Tensor Core utilization.
    
- **Constructive Cache Sharing:** Synchronized parallel fetches mapped through L3 cache overlap form the hardware basis for attention optimizations like Multi-Query Attention (MQA) and Grouped-Query Attention (GQA).
    
- **Memory-Bandwidth Bounds:** Auto-regressive generation is strictly limited by memory bandwidth; just as CPUs saturate system buses during sequential passes, GPUs require High Bandwidth Memory (HBM) and quantization methods (e.g., INT4/AWQ) to compress memory traffic.
