"""Compare identical CPU-bound threads on standard and free-threaded CPython."""

import argparse
import concurrent.futures
import gc
import hashlib
import json
import os
import platform
import random
import shutil
import statistics
import subprocess
import sys
import sysconfig
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple


def sum_low_bits(values: Sequence[int]) -> int:
    """CPU-bound Python bytecode loop shared by both interpreter builds."""
    total = 0
    for value in values:
        total += value & 1
    return total


def _time_call(function: Callable[[], int], expected: int) -> float:
    gc_was_enabled = gc.isenabled()
    try:
        if gc_was_enabled:
            gc.disable()
        started = time.perf_counter_ns()
        result = function()
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    finally:
        if gc_was_enabled:
            gc.enable()
    if result != expected:
        raise AssertionError(f"workload returned {result}; expected {expected}")
    return elapsed_ms


def _statistics(samples: List[float]) -> Dict[str, float]:
    return {
        "count": len(samples),
        "min_ms": min(samples),
        "median_ms": statistics.median(samples),
        "mean_ms": statistics.fmean(samples),
        "stdev_ms": statistics.stdev(samples) if len(samples) > 1 else 0.0,
    }


def run_worker(length: int, repeats: int) -> Dict[str, object]:
    """Measure one interpreter build; called in a dedicated subprocess."""
    first = list(range(length))
    second = list(range(length, length * 2))
    expected_one = length // 2
    expected_two = length
    samples: Dict[str, List[float]] = {
        "one_task": [],
        "two_tasks_sequential": [],
        "two_tasks_threads": [],
    }
    order_rng = random.Random(12345)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Create both worker threads before measuring task submission.
        warmup_barrier = threading.Barrier(3)

        def wait_for_warmup() -> None:
            warmup_barrier.wait()

        warmups = [executor.submit(wait_for_warmup) for _ in range(2)]
        warmup_barrier.wait()
        for future in warmups:
            future.result()

        def one_task() -> int:
            return sum_low_bits(first)

        def sequential() -> int:
            return sum_low_bits(first) + sum_low_bits(second)

        def threaded() -> int:
            future_a = executor.submit(sum_low_bits, first)
            future_b = executor.submit(sum_low_bits, second)
            return future_a.result() + future_b.result()

        calls: Dict[str, Tuple[Callable[[], int], int]] = {
            "one_task": (one_task, expected_one),
            "two_tasks_sequential": (sequential, expected_two),
            "two_tasks_threads": (threaded, expected_two),
        }
        execution_order = []
        for _ in range(repeats):
            order = list(calls)
            order_rng.shuffle(order)
            execution_order.append(order)
            for name in order:
                samples[name].append(_time_call(calls[name][0], calls[name][1]))

    medians = {name: statistics.median(values) for name, values in samples.items()}
    gil_enabled = (
        sys._is_gil_enabled()  # type: ignore[attr-defined]
        if hasattr(sys, "_is_gil_enabled")
        else True
    )
    affinity = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None
    affinity_topology = []
    for cpu in affinity or []:
        topology_root = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        try:
            affinity_topology.append(
                {
                    "logical_cpu": cpu,
                    "core_id": int((topology_root / "core_id").read_text().strip()),
                    "package_id": int(
                        (topology_root / "physical_package_id").read_text().strip()
                    ),
                }
            )
        except (FileNotFoundError, PermissionError, ValueError):
            continue
    executable_path = Path(sys.executable).resolve()
    try:
        executable_sha256 = hashlib.sha256(executable_path.read_bytes()).hexdigest()
    except (FileNotFoundError, PermissionError, OSError):
        executable_sha256 = None
    return {
        "python_version": platform.python_version(),
        "python_build": sys.version,
        "python_build_tuple": platform.python_build(),
        "python_compiler": platform.python_compiler(),
        "python_abiflags": getattr(sys, "abiflags", ""),
        "python_config_args": sysconfig.get_config_var("CONFIG_ARGS"),
        "executable": sys.executable,
        "executable_sha256": executable_sha256,
        "implementation": platform.python_implementation(),
        "gil_enabled_at_runtime": gil_enabled,
        "py_gil_disabled_build": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        "python_int_zero_bytes": sys.getsizeof(0),
        "cpu_affinity": affinity,
        "affinity_topology": affinity_topology,
        "length_per_task": length,
        "repeats": repeats,
        "execution_order": execution_order,
        "measurements": {
            name: {"samples_ms": values, "statistics": _statistics(values)}
            for name, values in samples.items()
        },
        "thread_speedup_for_two_tasks": (
            medians["two_tasks_sequential"] / medians["two_tasks_threads"]
        ),
        "single_task_median_ms": medians["one_task"],
    }


def run_interpreter(executable: str, length: int, repeats: int) -> Dict[str, object]:
    """Run this module as a worker under a selected Python executable."""
    resolved = shutil.which(executable)
    if resolved is None:
        raise FileNotFoundError(f"interpreter not found: {executable}")
    completed = subprocess.run(
        [
            resolved,
            str(Path(__file__).resolve()),
            "--worker",
            "--length",
            str(length),
            "--repeats",
            str(repeats),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def render_markdown(payload: Dict[str, object]) -> str:
    """Render paired interpreter evidence as a concise report."""
    results = payload["interpreters"]
    rows = []
    for result in results:
        measurements = result["measurements"]
        build = "free-threaded" if result["py_gil_disabled_build"] else "standard"
        rows.append(
            "| {version} {build} | {gil} | {one:.3f} | {sequential:.3f} | "
            "{threads:.3f} | {speedup:.2f}x |".format(
                version=result["python_version"],
                build=build,
                gil="enabled" if result["gil_enabled_at_runtime"] else "disabled",
                one=measurements["one_task"]["statistics"]["median_ms"],
                sequential=measurements["two_tasks_sequential"]["statistics"]["median_ms"],
                threads=measurements["two_tasks_threads"]["statistics"]["median_ms"],
                speedup=result["thread_speedup_for_two_tasks"],
            )
        )
    standard = next(result for result in results if not result["py_gil_disabled_build"])
    free = next(result for result in results if result["py_gil_disabled_build"])
    single_overhead = (
        free["single_task_median_ms"] / standard["single_task_median_ms"] - 1.0
    ) * 100.0
    single_thread_comparison = (
        f"{single_overhead:.1f}% slower"
        if single_overhead >= 0
        else f"{abs(single_overhead):.1f}% faster"
    )
    return """# CPython 3.14 free-threading experiment

This experiment runs identical CPU-bound Python bytecode under matching standard and
free-threaded CPython 3.14 builds. It uses only the standard library, so importing a
third-party extension cannot silently re-enable the GIL. Both subprocesses inherit
the same two-core CPU affinity and use persistent worker threads.

## Results

| Interpreter | Runtime GIL | One task ms | Two sequential ms | Two threads ms | Thread speedup |
| --- | --- | ---: | ---: | ---: | ---: |
{rows}

The standard build shows no CPU-throughput benefit from Python threads because the
threads take turns executing bytecode under the GIL. The free-threaded build permits
the same bytecode loop to run simultaneously on both cores. Its two-task thread
speedup is therefore a real throughput comparison, not a Numba or native-extension
comparison.

Free-threading is not free: synchronization and thread-safe reference counting can
change single-thread latency. In this run, one task on the free-threaded build was
{single_thread_comparison} than the matching standard build. This is one workload
on one Python build and CPU, not a general estimate of free-threading overhead.
The raw JSON records `sys.getsizeof(0)` as {standard_int_bytes} bytes in the standard
build and {free_int_bytes} bytes in the free-threaded build, along with compiler and
configure arguments, ABI flags, and executable hashes for both interpreters.

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
taskset -c 2,4 .venv/bin/python bench/compare_free_threading.py \\
  --interpreters python3.14 python3.14t --length 2000000 --repeats 9 \\
  --json results/my-host-python314-free-threading.json \\
  --markdown docs/python314-free-threading.md
```
""".format(
        rows="\n".join(rows),
        single_thread_comparison=single_thread_comparison,
        standard_int_bytes=standard["python_int_zero_bytes"],
        free_int_bytes=free["python_int_zero_bytes"],
    )


def main() -> None:
    if "--worker" in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument("--worker", action="store_true")
        parser.add_argument("--length", type=int, required=True)
        parser.add_argument("--repeats", type=int, required=True)
        args = parser.parse_args()
        print(json.dumps(run_worker(args.length, args.repeats)), flush=True)
        return

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interpreters", nargs=2, default=["python3.14", "python3.14t"]
    )
    parser.add_argument("--length", type=int, default=2_000_000)
    parser.add_argument("--repeats", type=int, default=9)
    parser.add_argument("--json", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()
    if min(args.length, args.repeats) < 1:
        parser.error("length and repeats must be positive")

    payload: Dict[str, object] = {
        "schema_version": 1,
        "configuration": vars(args),
        "interpreters": [
            run_interpreter(executable, args.length, args.repeats)
            for executable in args.interpreters
        ],
    }
    build_modes = {result["py_gil_disabled_build"] for result in payload["interpreters"]}
    if build_modes != {False, True}:
        raise RuntimeError("comparison requires one standard and one free-threaded build")

    json_path = Path(args.json)
    markdown_path = Path(args.markdown)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"Wrote raw evidence to {json_path}")
    print(f"Wrote comparison report to {markdown_path}")


if __name__ == "__main__":
    main()
