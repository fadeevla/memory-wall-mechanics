"""Measure each implementation's RSS in a fresh, externally monitored process."""

import argparse
import gc
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from ..algorithms import ALGORITHM_SPECS, warmup_numba_kernels
from .runner import collect_environment


def _rss_kib(pid: int) -> Optional[int]:
    """Read resident memory from Linux procfs."""
    try:
        status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError):
        return None
    for line in status.splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return None


def _worker(algorithm: str, n: int, seed: int, repeats: int) -> None:
    spec = ALGORITHM_SPECS[algorithm]
    if spec.compiled:
        warmup_numba_kernels()
    canonical = np.arange(1, n + 2, dtype=np.int32)
    canonical[-1] = n
    np.random.default_rng(seed).shuffle(canonical)
    data = spec.prepare_input(canonical)
    del canonical
    gc.collect()
    baseline = _rss_kib(os.getpid())
    print(json.dumps({"state": "ready", "baseline_rss_kib": baseline}), flush=True)
    if sys.stdin.readline().strip() != "run":
        raise SystemExit(3)

    started = time.perf_counter_ns()
    answer = -1
    for _ in range(repeats):
        answer = spec.function(data)
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    if answer != n:
        raise AssertionError(f"{algorithm} returned {answer}; expected {n}")
    print(json.dumps({"state": "complete", "elapsed_ms": elapsed_ms}), flush=True)


def measure_one(algorithm: str, n: int, seed: int, repeats: int = 3) -> Dict[str, object]:
    """Run and monitor one implementation in a clean subprocess."""
    command = [
        sys.executable,
        "-m",
        "duplicate_find.benchmark.memory_runner",
        "--worker",
        algorithm,
        str(n),
        str(seed),
        str(repeats),
    ]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    assert process.stdin is not None
    ready_line = process.stdout.readline()
    if not ready_line:
        stderr = process.stderr.read() if process.stderr is not None else ""
        raise RuntimeError(f"memory worker failed before readiness: {stderr}")
    ready = json.loads(ready_line)
    baseline = ready["baseline_rss_kib"]
    peak = baseline
    process.stdin.write("run\n")
    process.stdin.flush()

    while process.poll() is None:
        rss = _rss_kib(process.pid)
        if rss is not None:
            peak = rss if peak is None else max(peak, rss)
        time.sleep(0.001)

    remaining = process.stdout.read().strip().splitlines()
    stderr = process.stderr.read() if process.stderr is not None else ""
    if process.returncode != 0:
        raise RuntimeError(f"memory worker exited {process.returncode}: {stderr}")
    complete = json.loads(remaining[-1])
    spec = ALGORITHM_SPECS[algorithm]
    return {
        "algorithm": algorithm,
        "algorithm_family": spec.algorithm_family,
        "execution_model": spec.execution_model,
        "input_representation": spec.input_representation,
        "n": n,
        "data_seed": seed,
        "repeats": repeats,
        "input_logical_bytes": (n + 1) * 4,
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "peak_increment_kib": (
            max(0, peak - baseline) if peak is not None and baseline is not None else None
        ),
        "elapsed_ms": complete["elapsed_ms"],
        "sampling_interval_ms": 1.0,
    }


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        _, _, algorithm, n, seed, repeats = sys.argv
        _worker(algorithm, int(n), int(seed), int(repeats))
        return

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algorithms", nargs="+", choices=list(ALGORITHM_SPECS), required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--json", required=True)
    args = parser.parse_args()
    if min(args.size, args.repeats) < 1:
        parser.error("size and repeats must be positive")
    if not Path("/proc/self/status").exists():
        parser.error("isolated RSS measurement currently requires Linux procfs")

    measurements: List[Dict[str, object]] = []
    for algorithm in args.algorithms:
        measurement = measure_one(algorithm, args.size, args.seed, args.repeats)
        measurements.append(measurement)
        print(
            f"{algorithm:<36} peak_increment={measurement['peak_increment_kib']} KiB"
        )
    payload = {
        "schema_version": 1,
        "method": "fresh subprocess per implementation; parent polls Linux VmRSS",
        "environment": collect_environment(),
        "configuration": vars(args),
        "measurements": measurements,
    }
    Path(args.json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
