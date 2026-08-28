"""Benchmark runner executing algorithms across dataset scales."""

import argparse
import math
import random
import sys
import time
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from ..algorithms import ALGORITHMS, warmup_numba_kernels
from ..memory.hugepage import allocate_hugepage_array
from .reporter import format_table_cli, export_csv, export_markdown


def run_benchmark(
    algorithms: Optional[List[str]] = None,
    sizes: Optional[List[int]] = None,
    repeats: int = 1,
    use_hugepages: bool = True,
    warmup: bool = True,
    verbose: bool = True,
) -> Dict[str, List[Tuple[int, float]]]:
    """Runs benchmarks across specified array sizes and algorithms.

    Args:
        algorithms: List of algorithm names to run (defaults to all).
        sizes: List of array sizes N (defaults to [10, 10**5, 10**6, 10**7, 10**8]).
        repeats: Number of timing repetitions per test case (returns minimum latency).
        use_hugepages: Whether to back NumPy arrays with 2MB HugePages.
        warmup: Whether to pre-compile JIT kernels before measuring.
        verbose: Whether to print progress.

    Returns:
        Dictionary mapping algorithm name to list of (N, execution_time_ms) tuples.
    """
    if sizes is None:
        sizes = [10, 10**5, 10**6, 10**7, 10**8]

    selected_algos = {}
    if algorithms is None:
        selected_algos = ALGORITHMS
    else:
        for name in algorithms:
            if name in ALGORITHMS:
                selected_algos[name] = ALGORITHMS[name]
            else:
                print(f"[Warning] Unknown algorithm: {name}. Skipping.", file=sys.stderr)

    if warmup:
        if verbose:
            print("🔥 Warming up Numba JIT kernels...")
        warmup_numba_kernels()

    results: Dict[str, List[Tuple[int, float]]] = {
        name: [] for name in selected_algos.keys()
    }

    hugepages_active = use_hugepages

    for N in sizes:
        if verbose:
            print(f"⏳ Generating test dataset for N = {N:,}...")

        test_arr = list(range(1, N + 1)) + [N]
        random.shuffle(test_arr)
        expected_dup = N

        for func_name, func in selected_algos.items():
            run_times = []

            for r in range(repeats):
                raw_buffer = None
                # Prepare data representation
                if "numba" in func_name or "numpy" in func_name:
                    if hugepages_active:
                        try:
                            data, raw_buffer = allocate_hugepage_array(
                                len(test_arr), dtype=np.int32
                            )
                            data[:] = test_arr
                        except RuntimeError as e:
                            if verbose and r == 0:
                                print(f"[!] HugePages unavailable ({e}). Falling back to 4KB pages.")
                            hugepages_active = False
                            data = np.array(test_arr, dtype=np.int32)
                    else:
                        data = np.array(test_arr, dtype=np.int32)
                else:
                    data = test_arr.copy()

                # Measure pure algorithm execution time
                start_time = time.perf_counter()
                try:
                    res = func(data)
                    elapsed = (time.perf_counter() - start_time) * 1000.0
                    if res != expected_dup:
                        if verbose:
                            print(f"❌ {func_name} returned wrong answer: {res} (expected {expected_dup})")
                        elapsed = -1.0
                except Exception as e:
                    if verbose:
                        print(f"❌ {func_name} raised exception: {e}")
                    elapsed = -1.0
                finally:
                    if raw_buffer is not None:
                        raw_buffer.close()

                if elapsed >= 0:
                    run_times.append(elapsed)

            best_elapsed = min(run_times) if run_times else -1.0
            results[func_name].append((N, best_elapsed))

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark memory wall and CPU cache locality on Find Duplicate Number."
    )
    parser.add_argument(
        "--algorithms",
        "-a",
        nargs="+",
        choices=list(ALGORITHMS.keys()),
        default=None,
        help="Specific algorithms to run (default: all)",
    )
    parser.add_argument(
        "--sizes",
        "-s",
        type=int,
        nargs="+",
        default=[10, 10**5, 10**6, 10**7, 10**8],
        help="Dataset sizes N to benchmark",
    )
    parser.add_argument(
        "--repeats",
        "-r",
        type=int,
        default=1,
        help="Number of repeats per test case (default: 1)",
    )
    parser.add_argument(
        "--no-hugepages",
        action="store_true",
        help="Disable 2MB HugePages and use standard 4KB OS pages",
    )
    parser.add_argument(
        "--no-warmup",
        action="store_true",
        help="Disable JIT compilation warmup",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="File path to save results in CSV format",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output results as a Markdown table",
    )

    args = parser.parse_args()

    results = run_benchmark(
        algorithms=args.algorithms,
        sizes=args.sizes,
        repeats=args.repeats,
        use_hugepages=not args.no_hugepages,
        warmup=not args.no_warmup,
        verbose=True,
    )

    print("\n" + format_table_cli(results, args.sizes))

    if args.markdown:
        print("\n### Markdown Table Output:\n")
        print(export_markdown(results, args.sizes))

    if args.csv:
        export_csv(results, args.sizes, args.csv)
        print(f"\n📊 Results saved to {args.csv}")


if __name__ == "__main__":
    main()
