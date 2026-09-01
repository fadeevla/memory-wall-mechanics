# Technical analysis: Python and ML systems performance

This document connects the repository's measurements to Python runtime behavior,
compiled execution, memory hierarchy effects, free-threading, and ML embedding
systems. Each section separates the supported conclusion from mechanisms that remain
hypotheses. Measurements refer to the published Ryzen 5 7535HS artifacts and should
not be treated as portable constants.

## 1. CPython scalar iteration: ndarray versus list

An ndarray improves storage density, but it does not make CPython
execute a scalar loop as native array code. Iterating a Python list retrieves
references to existing `PyLong` objects. Iterating an `int32` ndarray crosses the
NumPy scalar boundary for every element and exposes a NumPy scalar object to Python.
The bitwise operation and comparison are still dynamically dispatched Python-level
operations. In this case, that per-element boundary cost outweighed the ndarray's
better memory density.

The controlled registry assigns the exact same `findDuplicate_bit` function object
to the list and ndarray variants. At `N=1,000,000`, the list took 755.1 ms and the
ndarray took 1638.9 ms, about 2.2 times slower. This isolates representation while
holding the Python bytecode and algorithm constant.

This does not mean lists are generally faster than ndarrays. It means ndarray
performance comes from operating on buffers in native loops—through ufuncs,
compiled kernels, or vectorized library operations—not from indexing or iterating
NumPy scalar objects in CPython.

## 2. Numba versus NumPy with the same packed input

The NumPy implementation runs the inner work in native code, but each
bit performs several whole-array operations: shift, mask, and reduction. Expressions
such as `(arr >> bit) & 1` materialize temporary arrays and make multiple passes over
memory. The process repeats for every significant bit.

Numba compiles the surrounding loop and reduction as one native kernel. It loads
elements directly from the packed buffer, performs shifts and additions in compiled
code, and does not allocate an O(N) temporary for every bit. The captured LLVM IR
contains a vector loop with wide `int32` loads, vector shifts, additions, and a
horizontal reduction.

At `N=1,000,000`, NumPy took 10.89 ms and Numba took 1.57 ms. The isolated RSS run
observed about 7.7 MiB of incremental peak memory for NumPy and no resolvable
increment for Numba. Those observations support the temporary-allocation
explanation. They do not prove that allocation is the only contributor; loop fusion,
ufunc dispatch, the number of memory passes, and generated instructions also matter.

## 3. Measurement interference from `tracemalloc`

The observer consumed memory. `tracemalloc` maintains bookkeeping for
traced allocations. When it was enabled while constructing 500,000 Python integers,
that bookkeeping increased the process RSS even though the bookkeeping itself was
not part of the representation being measured. The first simultaneous
run reported an implausible RSS increase of about 65 MiB for an object graph whose
traced allocation was about 17 MiB.

The corrected experiment uses two fresh workers per representation. One enables
`tracemalloc` and reports its traced peak. The other does not enable tracing and
reports the RSS delta. The corrected list result was 17.16 MiB traced and 19.13 MiB
RSS; the `int32` ndarray was about 1.91 MiB by both measures.

The two measurements still answer different questions. `tracemalloc` observes
allocations registered with Python's tracing domains. RSS measures resident pages
for the entire process and is affected by allocator arenas, native libraries, page
rounding, and retained memory. Agreement is useful evidence, not proof that either
number is a universal definition of “memory used.”

## 4. Free-threaded single-task overhead

Removing the global lock requires replacing some of its implicit
protection with more granular mechanisms. Likely costs include thread-safe or biased
reference counting, per-object locking for mutable containers, different allocator
paths, synchronization around interpreter state, and coordination for garbage
collection. Free-threaded builds can also have different object layouts and
specialization behavior.

On this host, `sys.getsizeof(0)` is 28 bytes in standard Python 3.14 and 44 bytes in
the free-threaded build, so the builds demonstrably differ in more than whether one
global mutex is held. In the controlled loop, the free-threaded build was 48.2%
slower for one task, but two threads completed two tasks with a 1.94x speedup. The
standard build achieved 0.91x with threads.

The 48.2% should be treated as a build-and-workload result, not “the cost of removing
the GIL.” Further isolation requires recording configure and compiler flags,
compare allocation and refcount-heavy kernels separately, control thread-local
bytecode settings, and repeat across multiple Python patch releases.

## 5. Third-party extensions and runtime GIL state

Starting `python3.14t` does not guarantee that the GIL remains disabled. Importing a
C-API extension that has not explicitly declared
free-threading support can enable the GIL at runtime and emit a warning. A
multi-phase extension declares support with a `Py_mod_gil` slot set to
`Py_MOD_GIL_NOT_USED`. A single-phase extension uses
`PyUnstable_Module_SetGIL(..., Py_MOD_GIL_NOT_USED)` in a free-threaded build.

Both build capability and runtime state should be checked:

```python
import sys
import sysconfig

supports_free_threading = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
gil_is_currently_enabled = sys._is_gil_enabled()
```

The GIL can also be explicitly controlled with `PYTHON_GIL` or `-X gil`. This is why
the repository's 3.14 comparison is standard-library-only and records
`sys._is_gil_enabled()` inside each measured subprocess rather than assuming that a
`t` executable suffix proves the runtime state.

Even an extension that keeps the GIL disabled is not automatically thread-safe. It
must protect mutable internal state, avoid unsafe borrowed-reference patterns, use
appropriate container critical sections, and follow the free-threaded memory
allocation rules.

## 6. Why sorted embedding indices did not improve performance

Sorting can improve locality only if the resulting access distances
and reuse are useful to the hierarchy. Each embedding row here contains 128
`float32` values, or 512 bytes. The table is about 48.8 MiB, larger than the 16 MiB
L3 cache, and each bag contains only 128 uniformly random indices. Sorting those
indices still leaves large, irregular gaps across the table.

The order changed, but the experiment fetched essentially the same set of cache
lines with little repeated-row reuse. Sorting was performed outside the timed
region, so its own cost did not cause the result. NumPy was also dominated by
materializing and reducing a 16 MiB gathered tensor, while the fused Numba and
PyTorch kernels avoided that intermediate.

The paired analysis compares sorted and random medians for each of fifteen identical
data seeds. It found no sorting benefit. NumPy was 6.23% slower with a paired ratio
interval of [1.048, 1.084], and Python loops were 2.32% slower with [1.022, 1.035].
The intervals for Numba and PyTorch included a ratio of one, so their direction was
unresolved. A different result remains plausible with Zipfian indices, repeated
rows, smaller row dimensions, larger bags, or grouping that creates actual
cache-line reuse. Those are new hypotheses, not conclusions from this uniform run.

## 7. Extending the embedding experiment to NUMA systems

CPU placement and memory placement should become independent
experimental variables. First-touch allocation matters: a thread that initializes
the table can determine which NUMA node owns its pages. Pinning computation without
pinning allocation can accidentally benchmark remote memory.

The experiment should include at least these configurations:

1. One worker on node 0 with the table allocated on node 0.
2. One worker on node 0 with the table allocated on node 1.
3. Interleaved table pages across nodes.
4. Concurrent workers using one shared table.
5. A table replica per socket.
6. A row-sharded table with request routing and explicit cross-node lookups.

Placement can be controlled with `numactl --cpunodebind` and `--membind`, then
verified with `numastat` or `/proc/<pid>/numa_maps`. Socket, core, and thread topology
should also be recorded.
The metrics would include throughput, tail latency, local and remote demand fills,
memory-controller traffic per socket, and interconnect traffic. On this AMD host,
`perf list` exposes local and remote demand-fill events such as
`ls_dmnd_fills_from_sys.mem_io_local` and `.mem_io_remote`; event names must be
rediscovered on the target server.

For a real serving study, the comparison should include one large shared process and a
process per NUMA node. Replication consumes more memory but can remove remote table
reads and cross-socket synchronization.

## 8. `perf` measurement design for dependent access versus sequential scanning

No hardware-counter artifact is published for this host because PMU access was
denied at `perf_event_paranoid=4`. The following is therefore a measurement design,
not observed evidence. Analysis should begin with rates and latency proxies, not raw event totals,
because the algorithms retire different numbers of instructions and perform
different amounts of logical work.

The baseline group is:

- `cycles` and `instructions`, giving IPC;
- L1 data-cache loads and misses;
- last-level-cache accesses and misses;
- L1 and L2 DTLB misses, including page-walk-producing misses;
- branch instructions and branch misses;
- demand fills classified by cache versus local or remote memory;
- hardware-prefetch fills;
- a load-latency sampler such as AMD IBS when available.

For Floyd-style dependent access, the expected signature is lower IPC, more
long-latency demand loads,
more LLC misses per useful lookup once the working set exceeds cache, and potentially
more DTLB misses or page walks. Hardware prefetch should be less effective because
the next address depends on the previous load result.

For sequential bit scanning, the expected signature is predictable wide loads and
effective hardware
prefetch, fewer misses per load, and higher IPC. It can still generate more logical
traffic because it scans the array once per bit, so physical memory-controller
events are needed before claiming DRAM bandwidth.

Separate event groups are preferable when the PMU cannot schedule all counters
simultaneously; multiplexed counters can add uncertainty. The process should be
pinned, JIT code and data warmed according to an explicit cold/warm policy, and
events normalized per element or load. Generic `cache-misses` alone cannot distinguish
DRAM, cache-to-cache transfers, TLB walks, or prefetch behavior.

## 9. Training, sparse gradients, and quantized embeddings

Inference is primarily gather and reduction. Training adds a backward
scatter: every accessed row receives a gradient contribution. Repeated indices now
create write conflicts. The implementation may need atomic additions, sorting and
segmented reduction, per-thread accumulation buffers, or ownership partitioning.
The best strategy depends on duplicate frequency and embedding dimension.

Sparse gradients avoid materializing a dense table-sized gradient, but introduce
index/value structures, coalescing, and optimizer compatibility constraints. The
optimizer state can dominate memory: momentum or adaptive optimizers may store one
or two additional values per parameter, and sparse update support differs across
optimizers. Writes also introduce cache-line ownership and NUMA-coherence traffic
that the read-only experiment does not exercise.

Quantization reduces table bytes and can improve cache residency, TLB reach, and
effective bandwidth. It also adds scale and zero-point loads, unpacking, conversion,
and usually wider accumulation. The comparison should cover per-row and per-group
quantization,
`int8` and lower-bit formats, `int32` or `float32` accumulation, kernel fusion, and
accuracy against the float model. A quantized kernel can become compute-bound after
the memory bottleneck is reduced.

The expanded benchmark should include:

- inference versus forward-and-backward;
- uniform versus Zipfian and repeated indices;
- fixed versus variable bag lengths;
- weighted bags and padding indices;
- dense versus sparse gradients;
- optimizer state and update time;
- float, mixed-precision, and quantized tables;
- numerical error and model-level quality, not latency alone.

## 10. Portability across Python 3.12, 3.14, and free-threaded 3.14

Structural conclusions should be separated from measured constants.

The structural conclusions are likely to remain valid:

- a Python list stores references to Python objects while an ndarray stores typed
  elements in a strided buffer;
- `sys.getsizeof(list)` is shallow;
- ndarray scalar iteration crosses a Python/native object boundary;
- native vectorization and compilation can remove per-element interpreter dispatch;
- vectorized expressions can allocate large intermediates;
- dtype, strides, ownership, and access pattern affect performance;
- `tracemalloc` and RSS measure different domains;
- JIT compilation and data preparation must be excluded or reported explicitly.

The version-sensitive conclusions must be remeasured:

- exact bytecode and specialization behavior;
- Python object sizes and allocator behavior;
- absolute timings and crossover points;
- compiler vectorization and Numba support;
- NumPy and PyTorch extension compatibility;
- threading behavior and single-thread overhead.

Python 3.12 and standard 3.14 still serialize CPU-bound Python bytecode under the
process GIL, although interpreter improvements can change the absolute cost. A
free-threaded 3.14 build can execute pure Python threads in parallel when the GIL is
actually disabled, but its runtime mechanisms and object layout change the cost
model. Importing an unsupported C extension may re-enable the GIL, so both build
capability and runtime state should be recorded after imports.

Therefore the methodology should be carried across versions rather than copying the
numerical ratios. Correctness invariants and representation facts are portable;
performance numbers belong to a specific interpreter, dependency set, build, CPU,
and runtime configuration.

## References

- [Python 3.14: Python support for free threading](https://docs.python.org/3/howto/free-threading-python.html)
- [Python 3.14: C API extension support for free threading](https://docs.python.org/3.14/howto/free-threading-extensions.html)
- [Python 3.14: threading and GIL performance considerations](https://docs.python.org/3.14/library/threading.html)
- [Numba parallel loops and reductions](https://numba.readthedocs.io/en/stable/user/parallel.html)
