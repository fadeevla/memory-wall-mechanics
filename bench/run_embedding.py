#!/usr/bin/env python3
"""Benchmark batched CPU embedding bags across NumPy, Numba, Python, and PyTorch."""

import argparse
import json
import os
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from duplicate_find.benchmark.reporter import sample_statistics
from duplicate_find.benchmark.runner import collect_environment
from duplicate_find.ml import (
    embedding_bags_numba,
    embedding_bags_numpy,
    embedding_bags_python,
    embedding_bags_torch,
    warmup_embedding_numba,
)


def _as_numpy(value: object) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return value
    return value.detach().cpu().numpy()  # type: ignore[union-attr]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument("--dimension", type=int, default=128)
    parser.add_argument("--bags", type=int, default=128)
    parser.add_argument("--bag-size", type=int, default=64)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--order-seed", type=int, default=12345)
    parser.add_argument("--data-seeds", type=int, nargs="+", default=[12345, 12346, 12347])
    parser.add_argument(
        "--locality",
        choices=["random", "sorted-within-bag"],
        default="random",
    )
    parser.add_argument("--skip-python", action="store_true")
    parser.add_argument("--skip-torch", action="store_true")
    parser.add_argument("--torch-threads", type=int, default=1)
    parser.add_argument(
        "--cache-flush-mib",
        type=int,
        default=0,
        help=(
            "Read this many MiB before every timed call as a best-effort cache "
            "eviction step; 0 leaves cache state uncontrolled."
        ),
    )
    parser.add_argument("--json", help="Write grouped samples and environment metadata.")
    args = parser.parse_args()
    if min(args.rows, args.dimension, args.bags, args.bag_size, args.repeats) < 1:
        parser.error("all numeric arguments must be positive")
    if not args.data_seeds:
        parser.error("data-seeds must not be empty")
    if args.cache_flush_mib < 0:
        parser.error("cache-flush-mib must be non-negative")

    cache_flush_buffer = (
        np.ones(args.cache_flush_mib * 1024**2, dtype=np.uint8)
        if args.cache_flush_mib
        else None
    )

    warmup_embedding_numba()
    torch = None
    torch_version = None
    if not args.skip_torch:
        try:
            import torch as imported_torch
        except ImportError:
            print("PyTorch is unavailable; install the optional 'ml' extra or use --skip-torch.")
        else:
            torch = imported_torch
            torch.set_num_threads(args.torch_threads)
            torch_version = torch.__version__

    samples: Dict[str, List[Dict[str, object]]] = {}
    max_errors: Dict[str, Dict[str, float]] = {}
    order_rng = random.Random(args.order_seed)
    execution_orders: Dict[str, List[List[str]]] = {}

    for data_seed in args.data_seeds:
        rng = np.random.default_rng(data_seed)
        table = rng.standard_normal((args.rows, args.dimension), dtype=np.float32)
        shaped_indices = rng.integers(
            0, args.rows, size=(args.bags, args.bag_size), dtype=np.int64
        )
        if args.locality == "sorted-within-bag":
            shaped_indices.sort(axis=1)
        indices = shaped_indices.reshape(-1)
        offsets = np.arange(args.bags + 1, dtype=np.int64) * args.bag_size

        calls: Dict[str, Callable[[], object]] = {
            "numpy_gather_reduce": lambda: embedding_bags_numpy(table, indices, offsets),
            "numba_fused": lambda: embedding_bags_numba(table, indices, offsets),
        }
        if not args.skip_python:
            calls["python_loops"] = lambda: embedding_bags_python(table, indices, offsets)
        if torch is not None:
            torch_table = torch.from_numpy(table)
            torch_indices = torch.from_numpy(indices)
            torch_offsets = torch.from_numpy(offsets)
            calls["torch_embedding_bag"] = lambda: embedding_bags_torch(
                torch_table, torch_indices, torch_offsets
            )
            # Exclude one-time PyTorch dispatcher and kernel initialization.
            calls["torch_embedding_bag"]()

        reference = np.add.reduceat(
            table[indices].astype(np.float64), offsets[:-1], axis=0
        )
        seed_samples: Dict[str, List[float]] = {name: [] for name in calls}
        seed_orders: List[List[str]] = []
        for _ in range(args.repeats):
            order = list(calls)
            order_rng.shuffle(order)
            seed_orders.append(order)
            for name in order:
                if cache_flush_buffer is not None:
                    # Best-effort LLC eviction. This is outside timing and does not
                    # guarantee a fully cold hierarchy on every CPU.
                    int(np.sum(cache_flush_buffer, dtype=np.uint64))
                started = time.perf_counter_ns()
                result = calls[name]()
                elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
                result_array = _as_numpy(result)
                difference = np.abs(result_array.astype(np.float64) - reference)
                absolute_error = float(np.max(difference))
                relative_error = float(
                    np.max(difference / np.maximum(np.abs(reference), 1e-12))
                )
                np.testing.assert_allclose(
                    result_array,
                    reference,
                    rtol=1e-3,
                    atol=1e-4 * args.bag_size,
                )
                seed_samples[name].append(elapsed_ms)
                errors = max_errors.setdefault(name, {"max_abs": 0.0, "max_rel": 0.0})
                errors["max_abs"] = max(errors["max_abs"], absolute_error)
                errors["max_rel"] = max(errors["max_rel"], relative_error)

        execution_orders[str(data_seed)] = seed_orders
        for name, values in seed_samples.items():
            samples.setdefault(name, []).append(
                {"data_seed": data_seed, "samples_ms": values}
            )

    measurements = {}
    for name, groups in samples.items():
        values = [float(value) for group in groups for value in group["samples_ms"]]
        seed_medians = [statistics.median(group["samples_ms"]) for group in groups]
        measurements[name] = {
            "sample_groups": groups,
            "statistics": sample_statistics(values, confidence_samples=seed_medians),
            "confidence_unit": "per-data-seed median",
            "numerical_error_vs_float64": max_errors[name],
        }
        stats = measurements[name]["statistics"]
        print(
            f"{name:<22} median={stats['median_ms']:10.3f} ms "
            f"seed-CI=[{stats['median_ci95_low_ms']:.3f}, "
            f"{stats['median_ci95_high_ms']:.3f}]"
        )

    if args.json:
        environment = collect_environment()
        environment["torch"] = torch_version
        payload = {
            "schema_version": 2,
            "configuration": vars(args),
            "environment": environment,
            "table_bytes": args.rows * args.dimension * np.dtype(np.float32).itemsize,
            "gathered_tensor_bytes": (
                args.bags * args.bag_size * args.dimension * np.dtype(np.float32).itemsize
            ),
            "execution_order": execution_orders,
            "cache_conditioning": {
                "method": (
                    "best-effort sequential flush-buffer read before each timed call"
                    if cache_flush_buffer is not None
                    else "none; float64 reference calculation precedes timed calls"
                ),
                "flush_buffer_mib": args.cache_flush_mib,
                "guarantees_cold_cache": False,
            },
            "measurements": measurements,
        }
        Path(args.json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
