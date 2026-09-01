"""Generate a compact report about CPython objects, NumPy storage, memory, and the GIL."""

import argparse
import concurrent.futures
import dis
import gc
import json
import os
import random
import statistics
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numba
import numpy as np
from numba import njit, prange

from .reporter import sample_statistics
from .runner import collect_environment


def sum_low_bits_python(values: Sequence[int]) -> int:
    """Small CPython loop used for bytecode and GIL demonstrations."""
    total = 0
    for value in values:
        total += value & 1
    return total


@njit
def sum_low_bits_numba_serial(values: np.ndarray) -> int:
    """Compiled serial counterpart to ``sum_low_bits_python``."""
    total = 0
    for index in range(len(values)):
        total += values[index] & 1
    return total


@njit(parallel=True)
def sum_low_bits_numba_parallel(values: np.ndarray) -> int:
    """Compiled parallel reduction using native Numba worker threads."""
    total = 0
    for index in prange(len(values)):
        total += values[index] & 1
    return total


def _rss_kib(pid: int) -> Optional[int]:
    try:
        status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError):
        return None
    for line in status.splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return None


def collect_representation_metadata(length: int) -> Dict[str, object]:
    """Collect exact shallow/deep object sizes and ndarray layout metadata."""
    python_values = list(range(length))
    array = np.arange(length, dtype=np.int32)
    strided = array[::2]
    return {
        "length": length,
        "python_int_zero_bytes": sys.getsizeof(0),
        "python_int_large_bytes": sys.getsizeof(10**30),
        "list_shallow_bytes": sys.getsizeof(python_values),
        "list_deep_bytes": sys.getsizeof(python_values)
        + sum(sys.getsizeof(value) for value in python_values),
        "ndarray": {
            "dtype": str(array.dtype),
            "itemsize": array.itemsize,
            "shape": array.shape,
            "strides": array.strides,
            "nbytes": array.nbytes,
            "sys_getsizeof_bytes": sys.getsizeof(array),
            "c_contiguous": bool(array.flags.c_contiguous),
        },
        "strided_view": {
            "shape": strided.shape,
            "strides": strided.strides,
            "nbytes": strided.nbytes,
            "sys_getsizeof_bytes": sys.getsizeof(strided),
            "c_contiguous": bool(strided.flags.c_contiguous),
            "shares_memory": bool(np.shares_memory(array, strided)),
        },
    }


def _memory_worker(representation: str, length: int, trace_allocations: bool) -> None:
    """Construct one representation in a fresh process and print one memory view."""
    gc.collect()
    rss_before = _rss_kib(os.getpid())
    if trace_allocations:
        tracemalloc.start()
    if representation == "python.list[int]":
        value = list(range(length))
    elif representation == "numpy.int32":
        value = np.arange(length, dtype=np.int32)
    else:
        raise ValueError(f"unknown representation: {representation}")
    traced_current, traced_peak = (
        tracemalloc.get_traced_memory() if trace_allocations else (None, None)
    )
    rss_after = _rss_kib(os.getpid())
    payload = {
        "representation": representation,
        "length": length,
        "trace_allocations": trace_allocations,
        "sys_getsizeof_bytes": sys.getsizeof(value),
        "tracemalloc_current_bytes": traced_current,
        "tracemalloc_peak_bytes": traced_peak,
        "rss_before_kib": rss_before,
        "rss_after_kib": rss_after,
        "rss_increment_kib": (
            rss_after - rss_before
            if rss_before is not None and rss_after is not None
            else None
        ),
    }
    print(json.dumps(payload), flush=True)


def measure_representation_memory(representation: str, length: int) -> Dict[str, object]:
    """Measure tracing and RSS separately so tracing metadata cannot pollute RSS."""
    def run_worker(trace_allocations: bool) -> Dict[str, object]:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "duplicate_find.benchmark.runtime_explainer",
                "--memory-worker",
                representation,
                str(length),
                "trace" if trace_allocations else "rss",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    rss_result = run_worker(False)
    traced_result = run_worker(True)
    return {
        "representation": representation,
        "length": length,
        "sys_getsizeof_bytes": rss_result["sys_getsizeof_bytes"],
        "tracemalloc_current_bytes": traced_result["tracemalloc_current_bytes"],
        "tracemalloc_peak_bytes": traced_result["tracemalloc_peak_bytes"],
        "rss_before_kib": rss_result["rss_before_kib"],
        "rss_after_kib": rss_result["rss_after_kib"],
        "rss_increment_kib": rss_result["rss_increment_kib"],
        "measurement_design": (
            "tracemalloc and RSS were collected in separate fresh workers to keep "
            "tracemalloc bookkeeping out of the RSS delta"
        ),
    }


def _elapsed_ms(function: Callable[[], int]) -> Tuple[float, int]:
    started = time.perf_counter_ns()
    result = function()
    return (time.perf_counter_ns() - started) / 1_000_000, result


def measure_concurrency(
    python_length: int,
    native_length: int,
    repeats: int,
    numba_threads: int,
) -> Dict[str, object]:
    """Compare Python threads with an internal Numba parallel reduction."""
    first = list(range(python_length))
    second = list(range(python_length, python_length * 2))
    expected_python_total = python_length
    native_values = np.arange(native_length, dtype=np.int32)
    expected_native = native_length // 2
    sum_low_bits_numba_serial(np.array([0, 1], dtype=np.int32))
    sum_low_bits_numba_parallel(np.array([0, 1], dtype=np.int32))
    numba.set_num_threads(numba_threads)

    samples: Dict[str, List[float]] = {
        "python_sequential_two_tasks": [],
        "python_threads_two_tasks": [],
        "numba_serial_one_task": [],
        "numba_parallel_one_task": [],
    }
    order_rng = random.Random(12345)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        def python_sequential() -> int:
            return sum_low_bits_python(first) + sum_low_bits_python(second)

        def python_threaded() -> int:
            future_a = executor.submit(sum_low_bits_python, first)
            future_b = executor.submit(sum_low_bits_python, second)
            return future_a.result() + future_b.result()

        calls: Dict[str, Tuple[Callable[[], int], int]] = {
            "python_sequential_two_tasks": (python_sequential, expected_python_total),
            "python_threads_two_tasks": (python_threaded, expected_python_total),
            "numba_serial_one_task": (
                lambda: sum_low_bits_numba_serial(native_values),
                expected_native,
            ),
            "numba_parallel_one_task": (
                lambda: sum_low_bits_numba_parallel(native_values),
                expected_native,
            ),
        }
        execution_order = []
        for _ in range(repeats):
            order = list(calls)
            order_rng.shuffle(order)
            execution_order.append(order)
            for name in order:
                elapsed_ms, result = _elapsed_ms(calls[name][0])
                if result != calls[name][1]:
                    raise AssertionError(f"{name} returned {result}; expected {calls[name][1]}")
                samples[name].append(elapsed_ms)

    medians = {name: statistics.median(values) for name, values in samples.items()}
    return {
        "python_length_per_task": python_length,
        "native_length": native_length,
        "numba_threads": numba_threads,
        "execution_order": execution_order,
        "measurements": {
            name: {"samples_ms": values, "statistics": sample_statistics(values)}
            for name, values in samples.items()
        },
        "python_thread_speedup": (
            medians["python_sequential_two_tasks"] / medians["python_threads_two_tasks"]
        ),
        "numba_parallel_speedup": (
            medians["numba_serial_one_task"] / medians["numba_parallel_one_task"]
        ),
        "comparison_boundary": (
            "Python speedup compares two equal tasks sequentially versus in two Python "
            "threads. Numba speedup compares equivalent serial and prange native reductions; "
            "absolute Python and Numba latencies are not compared because representations and "
            "task counts differ."
        ),
    }


def render_markdown(payload: Dict[str, object]) -> str:
    """Render collected evidence as a concise explanatory report."""
    objects = payload["representation_metadata"]
    array = objects["ndarray"]
    view = objects["strided_view"]
    memory = {item["representation"]: item for item in payload["memory_measurements"]}
    concurrency = payload["concurrency"]
    timings = concurrency["measurements"]
    environment = payload["environment"]
    topology_summary = "; ".join(
        f"CPU {entry['logical_cpu']} -> core {entry['core_id']}, package {entry['package_id']}"
        for entry in environment["affinity_topology"]
    )
    memory_length = memory["python.list[int]"]["length"]
    list_trace_mib = memory["python.list[int]"]["tracemalloc_peak_bytes"] / 1024**2
    list_rss_mib = memory["python.list[int]"]["rss_increment_kib"] / 1024
    array_trace_mib = memory["numpy.int32"]["tracemalloc_peak_bytes"] / 1024**2
    array_rss_mib = memory["numpy.int32"]["rss_increment_kib"] / 1024

    def median(name: str) -> float:
        return timings[name]["statistics"]["median_ms"]

    return f"""# What the Python runtime costs in this benchmark

This report is generated by `bench/explain_python_runtime.py`. It connects the main
benchmark results to observable CPython bytecode, object sizes, NumPy layout,
allocation measurements, and CPU-threading behavior. Values below describe this
recorded environment; rerun the command on another interpreter or host rather than
assuming the bytecode or sizes are universal.

## Recorded environment

- Python {environment['python']} ({environment['implementation']})
- NumPy {environment['numpy']}; Numba {environment['numba']}
- CPU: {environment['processor']}
- Affinity: {environment['cpu_affinity']}
- Affinity topology: {topology_summary or 'not reported'}
- Configured Numba threads: {concurrency['numba_threads']}

## 1. CPython executes a loop as bytecode

The demonstration function is deliberately small:

```python
def sum_low_bits_python(values):
    total = 0
    for value in values:
        total += value & 1
    return total
```

Its disassembly in the recorded interpreter is:

```text
{payload['python_loop_disassembly'].rstrip()}
```

`FOR_ITER` advances the Python iterator. Each iteration loads Python objects and
dispatches operations for `&` and `+=`; this is not a raw loop over four-byte machine
integers. Opcode names and specialization change between Python releases, which is
why the report records the exact interpreter version.

## 2. A list stores references to Python integer objects

For {objects['length']:,} values:

| Observation | Bytes |
| --- | ---: |
| `sys.getsizeof(0)` | {objects['python_int_zero_bytes']:,} |
| `sys.getsizeof(10**30)` | {objects['python_int_large_bytes']:,} |
| List container only | {objects['list_shallow_bytes']:,} |
| List plus every referenced integer | {objects['list_deep_bytes']:,} |
| Owning int32 ndarray data | {array['nbytes']:,} |
| `sys.getsizeof` owning ndarray | {array['sys_getsizeof_bytes']:,} |

`sys.getsizeof(list)` is shallow: it counts the list's reference array, not the
integer objects reached through those references. Integer size also depends on
magnitude because CPython integers are variable-width objects. This is why the
algorithmic phrase “an array of integers” describes very different memory layouts
for a list and a packed ndarray.

## 3. ndarray dtype, shape, and strides describe packed access

The owning array has dtype `{array['dtype']}`, item size {array['itemsize']} bytes,
shape `{tuple(array['shape'])}`, and strides `{tuple(array['strides'])}`. Its
one-dimensional stride equals its item size, so adjacent logical elements are
adjacent in memory.

The `array[::2]` view has shape `{tuple(view['shape'])}`, strides `{tuple(view['strides'])}`, and
`C_CONTIGUOUS={view['c_contiguous']}`. It shares memory with the original array but
its `sys.getsizeof` is only {view['sys_getsizeof_bytes']} bytes because the view owns
metadata, not the {view['nbytes']:,} logical bytes it exposes. Packed dtype alone does
not guarantee contiguous traversal; strides are part of the performance contract.

## 4. `tracemalloc` and RSS answer different questions

Each representation was constructed in two fresh interpreters: one with
`tracemalloc` enabled, and one uninstrumented worker for RSS. Separating them prevents
the tracer's own bookkeeping from inflating the RSS delta. RSS is the operating
system's resident set for the whole process; `tracemalloc` reports allocations
visible through Python's traced allocation domains.

| Representation ({memory_length:,} values) | `tracemalloc` peak | RSS increase |
| --- | ---: | ---: |
| `list[int]` | {list_trace_mib:.2f} MiB | {list_rss_mib:.2f} MiB |
| `numpy.int32` | {array_trace_mib:.2f} MiB | {array_rss_mib:.2f} MiB |

Neither instrument is a universal “memory used” number. RSS includes imported native
runtimes and allocator behavior; it can retain pages after objects are freed.
`tracemalloc` does not automatically explain every native library allocation. Their
agreement or disagreement is evidence that must be interpreted with the allocation
path and process baseline.

## 5. The GIL constrains Python bytecode, not Numba's internal workers

The process was restricted to affinity `{environment['cpu_affinity']}`. Two equal
CPython tasks took a median of {median('python_sequential_two_tasks'):.3f} ms
sequentially and {median('python_threads_two_tasks'):.3f} ms through two persistent
Python threads: a speedup of {concurrency['python_thread_speedup']:.2f}x. The threads
cannot execute this CPU-bound bytecode loop simultaneously because one thread holds
the GIL while interpreting Python operations.

The equivalent native reduction took {median('numba_serial_one_task'):.3f} ms with
the serial Numba loop and {median('numba_parallel_one_task'):.3f} ms with
`prange` using {concurrency['numba_threads']} Numba workers: a speedup of
{concurrency['numba_parallel_speedup']:.2f}x. Numba's workers execute compiled native
code inside the parallel region rather than competing to interpret the loop's Python
bytecode. Scaling is still bounded by scheduling overhead, memory bandwidth, cache
topology, and workload size.

These are two within-model comparisons, not an absolute Python-versus-Numba latency
comparison: the Python measurement runs two list-backed tasks, while the Numba
measurement compares one ndarray-backed reduction in serial and parallel forms.

## Reproduce

```bash
NUMBA_NUM_THREADS=2 taskset -c 2,4 .venv/bin/python \\
  bench/explain_python_runtime.py \\
  --object-length 10000 --memory-length 500000 \\
  --python-length 1000000 --native-length 10000000 \\
  --repeats 7 --numba-threads 2 \\
  --json results/my-host-python-runtime.json \\
  --markdown docs/python-runtime-report.md
```

The JSON retains the complete timing samples, randomized execution order, object and
layout metadata, disassembly, configuration, and host environment.

For the matching CPython 3.14 standard versus free-threaded comparison, see
[`python314-free-threading.md`](python314-free-threading.md).
"""


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--memory-worker":
        _, _, representation, length, mode = sys.argv
        _memory_worker(representation, int(length), trace_allocations=(mode == "trace"))
        return

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--object-length", type=int, default=10_000)
    parser.add_argument("--memory-length", type=int, default=500_000)
    parser.add_argument("--python-length", type=int, default=1_000_000)
    parser.add_argument("--native-length", type=int, default=10_000_000)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--numba-threads", type=int, default=2)
    parser.add_argument("--json", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()
    if min(
        args.object_length,
        args.memory_length,
        args.python_length,
        args.native_length,
        args.repeats,
        args.numba_threads,
    ) < 1:
        parser.error("all numeric arguments must be positive")
    if not Path("/proc/self/status").exists():
        parser.error("RSS collection currently requires Linux procfs")

    payload: Dict[str, object] = {
        "schema_version": 1,
        "configuration": vars(args),
        "environment": collect_environment(),
        "python_loop_disassembly": dis.Bytecode(sum_low_bits_python).dis(),
        "representation_metadata": collect_representation_metadata(args.object_length),
        "memory_measurements": [
            measure_representation_memory("python.list[int]", args.memory_length),
            measure_representation_memory("numpy.int32", args.memory_length),
        ],
        "concurrency": measure_concurrency(
            args.python_length,
            args.native_length,
            args.repeats,
            args.numba_threads,
        ),
    }
    json_path = Path(args.json)
    markdown_path = Path(args.markdown)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"Wrote raw evidence to {args.json}")
    print(f"Wrote explanatory report to {args.markdown}")


if __name__ == "__main__":
    main()
