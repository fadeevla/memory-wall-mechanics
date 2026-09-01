# CPython 3.14 free-threading experiment

This experiment runs identical CPU-bound Python bytecode under matching standard and
free-threaded CPython 3.14 builds. It uses only the standard library, so importing a
third-party extension cannot silently re-enable the GIL. Both subprocesses inherit
the same two-core CPU affinity and use persistent worker threads.

## Results

| Interpreter | Runtime GIL | One task ms | Two sequential ms | Two threads ms | Thread speedup |
| --- | --- | ---: | ---: | ---: | ---: |
| 3.14.6 standard | enabled | 39.932 | 78.878 | 86.726 | 0.91x |
| 3.14.6 free-threaded | disabled | 59.168 | 117.778 | 60.777 | 1.94x |

The standard build shows no CPU-throughput benefit from Python threads because the
threads take turns executing bytecode under the GIL. The free-threaded build permits
the same bytecode loop to run simultaneously on both cores. Its two-task thread
speedup is therefore a real throughput comparison, not a Numba or native-extension
comparison.

Free-threading is not free: synchronization and thread-safe reference counting can
change single-thread latency. In this run, one task on the free-threaded build was
48.2% slower than the matching standard build. This is one workload
on one Python build and CPU, not a general estimate of free-threading overhead.
The raw JSON records `sys.getsizeof(0)` as 28 bytes in the standard build and 44
bytes in the free-threaded build, along with compiler and configure arguments, ABI
flags, and executable hashes for both interpreters.

## Boundaries

- This is CPU-bound bytecode with coarse tasks; I/O-bound threads behave differently.
- The result says nothing about third-party extension safety or whether an extension
  chooses to re-enable the GIL.
- Two cores cannot establish scaling beyond two threads.
- CPU frequency and ordinary host noise were not eliminated; raw samples and
  execution order are retained in JSON.
- Free-threaded Python changes concurrency semantics, but data races and application
  synchronization remain the programmer's responsibility.

## Reproduce

```bash
taskset -c 2,4 .venv/bin/python bench/compare_free_threading.py \
  --interpreters python3.14 python3.14t --length 2000000 --repeats 9 \
  --json results/my-host-python314-free-threading.json \
  --markdown docs/python314-free-threading.md
```
