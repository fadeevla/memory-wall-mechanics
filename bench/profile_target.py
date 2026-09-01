#!/usr/bin/env python3
"""Attach perf only after imports, allocation, shuffling, and JIT warmup."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Set

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from duplicate_find.algorithms import ALGORITHM_SPECS, warmup_numba_kernels
from duplicate_find.benchmark.runner import collect_environment


DEFAULT_EVENTS = (
    "cycles,instructions,cache-references,cache-misses,"
    "L1-dcache-loads,L1-dcache-load-misses,dTLB-loads,dTLB-load-misses"
)


def parse_cpu_set(value: str) -> Set[int]:
    """Parse taskset-style comma-separated CPUs and inclusive ranges."""
    cpus: Set[int] = set()
    for group in value.split(","):
        bounds = group.strip().split("-", maxsplit=1)
        if len(bounds) == 1:
            cpus.add(int(bounds[0]))
        else:
            cpus.update(range(int(bounds[0]), int(bounds[1]) + 1))
    if not cpus:
        raise ValueError("CPU set cannot be empty")
    return cpus


def run_worker(algorithm: str, n: int, repeats: int, seed: int) -> None:
    """Prepare and warm a target, then wait for the parent profiler to release it."""
    rng = np.random.default_rng(seed)
    packed = np.arange(1, n + 2, dtype=np.int32)
    packed[-1] = n
    rng.shuffle(packed)
    spec = ALGORITHM_SPECS[algorithm]
    if spec.compiled:
        warmup_numba_kernels()
    data = spec.prepare_input(packed)
    function = spec.function
    metadata = {
        "schema_version": 1,
        "configuration": {
            "algorithm": algorithm,
            "n": n,
            "repeats": repeats,
            "seed": seed,
            "algorithm_family": spec.algorithm_family,
            "execution_model": spec.execution_model,
            "input_representation": spec.input_representation,
            "packed_equivalent_bytes": packed.nbytes,
        },
        "environment": collect_environment(),
    }
    print(json.dumps({"state": "ready", "metadata": metadata}), flush=True)
    if sys.stdin.readline().strip() != "run":
        raise SystemExit(3)

    started = time.perf_counter_ns()
    for _ in range(repeats):
        answer = function(data)
        if answer != n:
            raise AssertionError(f"incorrect result: {answer}; expected {n}")
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    print(json.dumps({"state": "complete", "elapsed_ms": elapsed_ms}), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("algorithm", choices=list(ALGORITHM_SPECS))
    parser.add_argument("n", type=int)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument(
        "--cpus", help="CPU list such as 2 or 2,4,6; defaults to current affinity."
    )
    parser.add_argument("--events", default=DEFAULT_EVENTS)
    parser.add_argument("--output", help="Write perf's machine-readable CSV to this path.")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.n < 1 or args.repeats < 1:
        parser.error("n and repeats must be positive")
    if shutil.which("perf") is None:
        parser.error("Linux perf is not installed or not on PATH")
    if args.cpus:
        if not hasattr(os, "sched_setaffinity"):
            parser.error("CPU affinity is not supported on this platform")
        os.sched_setaffinity(0, parse_cpu_set(args.cpus))

    if args.worker:
        run_worker(args.algorithm, args.n, args.repeats, args.seed)
        return

    worker_command = [
        sys.executable,
        str(Path(__file__).resolve()),
        args.algorithm,
        str(args.n),
        "--repeats",
        str(args.repeats),
        "--seed",
        str(args.seed),
        "--worker",
    ]
    worker = subprocess.Popen(
        worker_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert worker.stdin is not None
    assert worker.stdout is not None
    ready_line = worker.stdout.readline()
    if not ready_line:
        stderr = worker.stderr.read() if worker.stderr is not None else ""
        raise RuntimeError(f"profile worker failed before readiness: {stderr}")
    ready = json.loads(ready_line)
    profile_metadata = ready["metadata"]
    profile_metadata["configuration"]["events"] = args.events.split(",")

    perf_command = [
        "perf",
        "stat",
        "--no-big-num",
        "-x",
        ",",
        "-e",
        args.events,
        "-p",
        str(worker.pid),
    ]
    if args.output:
        perf_command.extend(["--output", args.output])
    perf = subprocess.Popen(perf_command)
    # perf signals readiness only indirectly. A short timeout catches immediate
    # permission/event failures while the worker remains blocked on stdin.
    try:
        perf.wait(timeout=0.2)
    except subprocess.TimeoutExpired:
        pass
    else:
        worker.stdin.close()
        worker.wait()
        raise SystemExit(perf.returncode)
    worker.stdin.write("run\n")
    worker.stdin.flush()
    worker.stdin.close()
    remaining = worker.stdout.read().strip().splitlines()
    stderr = worker.stderr.read() if worker.stderr is not None else ""
    worker_status = worker.wait()
    perf_status = perf.wait()
    if worker_status != 0:
        raise RuntimeError(f"profile worker exited {worker_status}: {stderr}")
    if perf_status != 0:
        raise SystemExit(perf_status)
    complete = json.loads(remaining[-1])
    print(
        f"target={args.algorithm} n={args.n} repeats={args.repeats} "
        f"elapsed_ms={complete['elapsed_ms']:.3f}"
    )
    if args.output:
        metadata_path = Path(f"{args.output}.metadata.json")
        metadata_path.write_text(json.dumps(profile_metadata, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(profile_metadata, indent=2))


if __name__ == "__main__":
    main()
