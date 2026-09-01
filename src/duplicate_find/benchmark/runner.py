"""Reproducible benchmark runner for duplicate-finding algorithms."""

import argparse
import gc
import os
import platform
import random
import resource
import statistics
import sys
import time
from pathlib import Path
from typing import Dict, List, MutableMapping, Optional, Tuple

import numba
import numpy as np
import llvmlite

from ..algorithms import ALGORITHM_SPECS, warmup_numba_kernels
from ..memory.hugepage import allocate_hugepage_array
from .reporter import export_csv, export_json, export_markdown, format_table_cli

SummaryResults = Dict[str, List[Tuple[int, float]]]
SampleGroup = Dict[str, object]
RawResults = Dict[str, List[SampleGroup]]


def collect_environment() -> Dict[str, object]:
    """Return metadata needed to interpret or reproduce benchmark results."""
    affinity = None
    if hasattr(os, "sched_getaffinity"):
        affinity = sorted(os.sched_getaffinity(0))

    try:
        threading_layer = numba.threading_layer()
    except ValueError:
        threading_layer = "not initialized"

    cpu_model = platform.processor() or "unknown"
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    except (FileNotFoundError, PermissionError):
        pass

    memory_total_kib = None
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                memory_total_kib = int(line.split()[1])
                break
    except (FileNotFoundError, PermissionError):
        pass

    cache_hierarchy = []
    cache_root = Path("/sys/devices/system/cpu/cpu0/cache")
    if cache_root.exists():
        for index in sorted(cache_root.glob("index*")):
            try:
                cache_hierarchy.append(
                    {
                        "level": (index / "level").read_text().strip(),
                        "type": (index / "type").read_text().strip(),
                        "size": (index / "size").read_text().strip(),
                    }
                )
            except (FileNotFoundError, PermissionError):
                continue

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

    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": cpu_model,
        "logical_cpu_count": os.cpu_count(),
        "memory_total_kib": memory_total_kib,
        "cache_hierarchy_cpu0": cache_hierarchy,
        "numpy": np.__version__,
        "numba": numba.__version__,
        "llvmlite": llvmlite.__version__,
        "numba_threads": numba.get_num_threads(),
        "numba_threading_layer": threading_layer,
        "cpu_affinity": affinity,
        "affinity_topology": affinity_topology,
    }


def _summary(samples: List[float], statistic: str) -> float:
    if not samples:
        return -1.0
    if statistic == "min":
        return min(samples)
    if statistic == "mean":
        return statistics.fmean(samples)
    return statistics.median(samples)


def run_benchmark(
    algorithms: Optional[List[str]] = None,
    sizes: Optional[List[int]] = None,
    repeats: int = 5,
    use_hugepages: bool = True,
    warmup: bool = True,
    verbose: bool = True,
    seed: int = 12345,
    data_seeds: Optional[List[int]] = None,
    statistic: str = "median",
    randomize_order: bool = True,
    max_temp_bytes: Optional[int] = 1024**3,
    cache_flush_mib: int = 0,
    raw_results: Optional[MutableMapping[str, List[SampleGroup]]] = None,
    run_metadata: Optional[MutableMapping[str, object]] = None,
) -> SummaryResults:
    """Benchmark algorithms over independent datasets and aggregate their samples.

    ``seed`` remains the deterministic algorithm-order seed. ``data_seeds`` controls
    independent input permutations; by default the data seed is also ``seed``.
    Construction, representation conversion, and JIT compilation are untimed.
    """
    if sizes is None:
        sizes = [10, 10**5, 10**6]
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    if cache_flush_mib < 0:
        raise ValueError("cache_flush_mib must be non-negative")
    if statistic not in {"min", "median", "mean"}:
        raise ValueError("statistic must be min, median, or mean")
    selected_data_seeds = list(data_seeds) if data_seeds is not None else [seed]
    if not selected_data_seeds:
        raise ValueError("data_seeds must contain at least one seed")

    names = list(ALGORITHM_SPECS) if algorithms is None else list(algorithms)
    unknown = [name for name in names if name not in ALGORITHM_SPECS]
    if unknown:
        raise ValueError(f"unknown algorithms: {', '.join(unknown)}")

    if warmup and any(ALGORITHM_SPECS[name].compiled for name in names):
        if verbose:
            print("Warming up Numba kernels...")
        warmup_numba_kernels()

    results: SummaryResults = {name: [] for name in names}
    samples_by_algorithm: RawResults = {name: [] for name in names}
    hugepages_active = use_hugepages
    hugepages_used = False
    order_rng = random.Random(seed)
    execution_orders: Dict[str, List[List[str]]] = {}
    cache_flush_buffer = (
        np.ones(cache_flush_mib * 1024**2, dtype=np.uint8)
        if cache_flush_mib
        else None
    )

    for n in sizes:
        if n < 1:
            raise ValueError("sizes must contain positive integers")
        all_samples: Dict[str, List[float]] = {name: [] for name in names}
        seed_summaries: Dict[str, List[float]] = {name: [] for name in names}

        for data_seed in selected_data_seeds:
            if verbose:
                print(f"Generating dataset N={n:,}, seed={data_seed}...")
            canonical = np.arange(1, n + 2, dtype=np.int32)
            canonical[-1] = n
            np.random.default_rng(data_seed).shuffle(canonical)

            skipped = {
                name
                for name in names
                if (
                    ALGORITHM_SPECS[name].temporary_bytes is not None
                    and max_temp_bytes is not None
                    and ALGORITHM_SPECS[name].temporary_bytes(n) > max_temp_bytes
                )
            }
            if skipped and verbose:
                for name in sorted(skipped):
                    estimate_mib = ALGORITHM_SPECS[name].temporary_bytes(n) / 1024**2
                    print(f"Skipping {name}: estimated temporary is {estimate_mib:,.0f} MiB.")

            samples_for_seed: Dict[str, List[float]] = {name: [] for name in names}
            order_key = f"n={n},seed={data_seed}"
            size_orders: List[List[str]] = []
            for _ in range(repeats):
                execution_order = [name for name in names if name not in skipped]
                if randomize_order:
                    order_rng.shuffle(execution_order)
                size_orders.append(execution_order)

                for name in execution_order:
                    spec = ALGORITHM_SPECS[name]
                    raw_buffer = None
                    if spec.input_representation == "numpy.int32" and hugepages_active:
                        try:
                            data, raw_buffer = allocate_hugepage_array(
                                len(canonical), dtype=np.int32
                            )
                            data[:] = canonical
                            hugepages_used = True
                        except RuntimeError as error:
                            if verbose:
                                print(f"HugePages unavailable ({error}); using normal pages.")
                            hugepages_active = False
                            data = spec.prepare_input(canonical)
                    else:
                        data = spec.prepare_input(canonical)

                    gc_was_enabled = gc.isenabled()
                    try:
                        if gc_was_enabled:
                            gc.disable()
                        if cache_flush_buffer is not None:
                            # Best-effort LLC eviction, outside the measured region. It
                            # does not guarantee a fully cold hierarchy on every CPU.
                            int(np.sum(cache_flush_buffer, dtype=np.uint64))
                        started = time.perf_counter_ns()
                        answer = spec.function(data)
                        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
                    finally:
                        if gc_was_enabled:
                            gc.enable()
                        if raw_buffer is not None:
                            raw_buffer.close()

                    if answer != n:
                        raise AssertionError(f"{name} returned {answer}; expected {n}")
                    samples_for_seed[name].append(elapsed_ms)
                    all_samples[name].append(elapsed_ms)

            execution_orders[order_key] = size_orders
            for name in names:
                if samples_for_seed[name]:
                    seed_summaries[name].append(
                        _summary(samples_for_seed[name], statistic)
                    )
                samples_by_algorithm[name].append(
                    {"n": n, "data_seed": data_seed, "samples_ms": samples_for_seed[name]}
                )

        for name in names:
            results[name].append((n, _summary(seed_summaries[name], statistic)))

    if raw_results is not None:
        raw_results.update(samples_by_algorithm)
    if run_metadata is not None:
        run_metadata.update(
            {
                "data_seeds": selected_data_seeds,
                "hugepages_used": hugepages_used,
                "execution_order": execution_orders,
                "gc_disabled_during_timing": True,
                "cache_conditioning": {
                    "method": (
                        "best-effort sequential flush-buffer read before each timed call"
                        if cache_flush_buffer is not None
                        else "none; input preparation occurs immediately before timing"
                    ),
                    "flush_buffer_mib": cache_flush_mib,
                    "guarantees_cold_cache": False,
                },
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark interpreter, representation, and memory-access tradeoffs."
    )
    parser.add_argument("--algorithms", "-a", nargs="+", choices=list(ALGORITHM_SPECS))
    parser.add_argument("--sizes", "-s", type=int, nargs="+", default=[10, 10**5, 10**6])
    parser.add_argument("--repeats", "-r", type=int, default=5)
    parser.add_argument("--seed", type=int, default=12345, help="Execution-order seed.")
    parser.add_argument(
        "--data-seeds",
        type=int,
        nargs="+",
        help="Independent dataset seeds; defaults to the execution-order seed.",
    )
    parser.add_argument("--statistic", choices=["median", "min", "mean"], default="median")
    parser.add_argument("--no-hugepages", action="store_true")
    parser.add_argument("--no-warmup", action="store_true")
    parser.add_argument("--keep-order", action="store_true")
    parser.add_argument(
        "--cache-flush-mib",
        type=int,
        default=0,
        help=(
            "Read this many MiB before every timed call as a best-effort cache "
            "eviction step; 0 leaves cache state uncontrolled."
        ),
    )
    parser.add_argument(
        "--max-temp-mib",
        type=int,
        default=1024,
        help="Skip implementations above this temporary estimate; 0 disables the guard.",
    )
    parser.add_argument("--csv", help="Write summarized timings to CSV.")
    parser.add_argument("--json", help="Write grouped samples, statistics, and metadata.")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    raw_results: RawResults = {}
    run_metadata: Dict[str, object] = {}
    max_temp_bytes = None if args.max_temp_mib == 0 else args.max_temp_mib * 1024**2
    results = run_benchmark(
        algorithms=args.algorithms,
        sizes=args.sizes,
        repeats=args.repeats,
        use_hugepages=not args.no_hugepages,
        warmup=not args.no_warmup,
        seed=args.seed,
        data_seeds=args.data_seeds,
        statistic=args.statistic,
        randomize_order=not args.keep_order,
        max_temp_bytes=max_temp_bytes,
        cache_flush_mib=args.cache_flush_mib,
        raw_results=raw_results,
        run_metadata=run_metadata,
    )

    environment = collect_environment()
    environment["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("\n" + format_table_cli(results, args.sizes, value_label=f"{args.statistic} ms"))
    print(
        f"Python {environment['python']}; NumPy {environment['numpy']}; "
        f"Numba {environment['numba']}; affinity={environment['cpu_affinity']}"
    )

    if args.markdown:
        print("\n" + export_markdown(results, args.sizes, value_label=f"{args.statistic} ms"))
    if args.csv:
        export_csv(results, args.sizes, args.csv)
    if args.json:
        export_json(
            results,
            raw_results,
            args.json,
            environment=environment,
            configuration={
                "order_seed": args.seed,
                "repeats_per_seed": args.repeats,
                "statistic": args.statistic,
                "sizes": args.sizes,
                "algorithms": args.algorithms or list(ALGORITHM_SPECS),
                "hugepages_requested": not args.no_hugepages,
                "randomized_order": not args.keep_order,
                **run_metadata,
            },
        )


if __name__ == "__main__":
    main()
