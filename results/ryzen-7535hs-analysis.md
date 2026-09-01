# Ryzen 5 7535HS experiment: interpretation and limits

## Configuration

- CPU: AMD Ryzen 5 7535HS, process pinned to logical CPU 2
- Timing environment: Python 3.10.12, NumPy 2.2.6, Numba 0.67.0
- Numba: one thread, OpenMP threading layer
- Inputs: `N` from 1,000 to 1,000,000; fifteen seeds from 101 through 1515
- Sampling: three repetitions per seed; randomized execution order; ordinary pages
- Cache policy: 64 MiB best-effort flush-buffer read before every timed call
- Summary: median of seed medians; 95% percentile-bootstrap interval over those medians

The run did not isolate the core at boot, lock CPU frequency, or establish a quiet
thermal state. The intervals therefore include input-permutation effects and some
ordinary host noise, but they should not be interpreted as laboratory-grade bounds.
Reading a buffer larger than this CPU's L3 reduces dependence on immediately prior
input construction, but it neither flushes every hierarchy level nor proves that
each measurement begins from identical physical memory state.

## Controlled bit-counting result

| Execution and representation | N=1,000 median ms | N=1,000,000 median ms | Seed-median 95% CI at N=1,000,000 |
| --- | ---: | ---: | ---: |
| CPython over `list[int]` | 0.395 | 755.083 | [749.670, 761.002] |
| Same CPython function over `numpy.int32` | 0.822 | 1638.935 | [1620.786, 1644.632] |
| NumPy operations over `numpy.int32` | 0.100 | 10.887 | [10.535, 11.077] |
| Numba loop over `numpy.int32` | 0.009 | 1.567 | [1.551, 1.620] |

The list-versus-ndarray pair uses the same Python function. Iterating ndarray
scalars was about 2.2x slower at one million elements, despite the packed storage,
because the operation remains a CPython scalar loop and crosses the ndarray scalar
interface repeatedly. Packed representation becomes useful when NumPy or compiled
Numba code operates on it without returning to Python per element.

At one million elements, NumPy was about 69x faster than the list loop and Numba was
about 482x faster. Numba was about 6.9x faster than this NumPy formulation. That gap
is consistent with NumPy constructing temporary arrays for each bit while Numba
performs a compiled reduction, but timing alone cannot partition the exact cost.

## Isolated RSS

At `N=1,000,000`, external 1 ms polling observed 7,920 KiB incremental peak RSS for
the NumPy implementation. The Python list, Python ndarray, and Numba runs showed at
most one page of resolvable growth after their prepared input baseline. The NumPy
observation is consistent with two approximately four-megabyte elementwise
temporaries. Polling can miss shorter-lived peaks, so zero or four KiB means “below
the measurement resolution,” not proof of zero allocation.

Prepared-process baselines were 137,152 KiB for the Python list, roughly 101,900 KiB
for the NumPy variants, and 173,176 KiB after Numba compilation. These totals include
the interpreter and imported runtime; their value is mainly comparative. The list
baseline exposes boxed-object storage, while the Numba baseline includes the JIT
compiler/runtime footprint that ordinary latency timing deliberately excludes.

## Compiler evidence

The captured Numba LLVM IR contains a `vector.body` with four-lane `i32` wide loads,
conversion to four-lane `i64`, vector shifts, masks, additions, and a horizontal
reduction. This is direct evidence that LLVM vectorized the hot inner counting loop
for the recorded signature and host target. It does not imply that every Numba
version, dtype, CPU target, or parallel variant produces the same code.

## Batched embedding bags

The embedding runs used a 100,000 x 128 float32 table, 256 bags, 128 lookups per bag,
fifteen paired data seeds, and the same 64 MiB best-effort cache-eviction policy. The
table is about 48.8 MiB and NumPy's gathered intermediate is 16 MiB.

| Implementation | Random median ms | Random seed-median 95% CI | Sorted median ms | Paired median change |
| --- | ---: | ---: | ---: | ---: |
| CPython loops | 999.795 | [993.104, 1001.136] | 1022.976 | +2.32% |
| NumPy gather/reduce | 12.175 | [11.873, 12.409] | 13.028 | +6.23% |
| Numba fused | 1.905 | [1.873, 1.950] | 1.919 | +2.04% |
| PyTorch `embedding_bag` | 1.313 | [1.278, 1.339] | 1.310 | +1.00% |

PyTorch was about 9.3x faster than NumPy and 1.5x faster than the simple fused Numba
kernel in the random run. Numba avoided the gathered tensor and was about 6.4x
faster than NumPy. Sorting indices within each bag did not improve this configuration.
The paired sorted/random ratio detected slowdowns for NumPy ([1.048, 1.084]) and
Python loops ([1.022, 1.035]); Numba and PyTorch intervals included one. The full
per-seed effects are retained in the paired locality JSON and Markdown artifacts.

The embedding environment used the host's NumPy 1.26.4 and PyTorch 2.5.1 build,
whereas the controlled duplicate experiment used the isolated environment's NumPy
2.2.6. Results are compared only within each experiment, never across those package
environments.

Reduction order differs among NumPy, Numba, Python, and PyTorch. The result JSON
therefore records maximum error against a float64 reference; correctness is checked
with a scale-aware tolerance rather than bitwise equality.

## Claims this experiment does not support

- It does not measure physical DRAM bandwidth.
- It does not attribute a timing difference solely to cache or TLB behavior.
- It does not establish performance on other CPUs, Python versions, or thread counts.
- Fifteen data seeds improve input coverage but do not provide a portable population
  confidence interval across machines or runtime conditions.
- The embedding workload is an inference microbenchmark, not an end-to-end model.
