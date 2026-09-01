"""Formatting and serialization for benchmark results."""

import json
import random
import statistics
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..algorithms import ALGORITHM_SPECS

SummaryResults = Dict[str, List[Tuple[int, float]]]
RawResults = Mapping[str, List[Mapping[str, object]]]


def _size_label(n: int) -> str:
    return f"{n:,}"


def _percentile(samples: Sequence[float], percentile: float) -> float:
    if not samples:
        raise ValueError("cannot calculate a percentile of empty samples")
    ordered = sorted(samples)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def bootstrap_median_ci(
    samples: Sequence[float], confidence: float = 0.95, resamples: int = 2000
) -> Tuple[float, float]:
    """Return a deterministic percentile-bootstrap interval for the median."""
    if not samples:
        raise ValueError("cannot bootstrap empty samples")
    if len(samples) == 1:
        return samples[0], samples[0]
    rng = random.Random(0)
    count = len(samples)
    estimates = [
        statistics.median(samples[rng.randrange(count)] for _ in range(count))
        for _ in range(resamples)
    ]
    tail = (1.0 - confidence) / 2.0
    return _percentile(estimates, tail), _percentile(estimates, 1.0 - tail)


def sample_statistics(
    samples: Sequence[float], confidence_samples: Optional[Sequence[float]] = None
) -> Dict[str, object]:
    """Calculate statistics over independent units while retaining repeat counts.

    When ``confidence_samples`` is provided, those values are the independent
    experimental units (for example, one median per data seed). Point estimates and
    confidence intervals use that same population. ``samples`` remains the complete
    set of technical repeats and is summarized separately.
    """
    if not samples:
        return {}
    independent = list(confidence_samples) if confidence_samples is not None else list(samples)
    ci_low, ci_high = bootstrap_median_ci(independent)
    return {
        "count": len(independent),
        "min_ms": min(independent),
        "median_ms": statistics.median(independent),
        "mean_ms": statistics.fmean(independent),
        "p95_ms": _percentile(independent, 0.95),
        "stdev_ms": statistics.stdev(independent) if len(independent) > 1 else 0.0,
        "median_ci95_low_ms": ci_low,
        "median_ci95_high_ms": ci_high,
        "confidence_unit_count": len(independent),
        "technical_repeat_count": len(samples),
        "raw_sample_median_ms": statistics.median(samples),
    }


def format_table_cli(
    results: SummaryResults, sizes: List[int], value_label: str = "ms"
) -> str:
    """Format summary results as a plain, copyable terminal table."""
    first_width = 38
    cell_width = 18
    separator = "=" * (first_width + cell_width * len(sizes))
    lines = [separator]
    header = f"{'Algorithm':<36} |"
    for n in sizes:
        header += f" N={_size_label(n):<13} |"
    lines.extend([header, "-" * len(separator)])

    max_n = max(sizes)
    names = sorted(
        results,
        key=lambda name: next(
            (value for n, value in results[name] if n == max_n and value >= 0),
            float("inf"),
        ),
    )
    for name in names:
        row = f"{name:<36} |"
        values = dict(results[name])
        for n in sizes:
            value = values.get(n, -1.0)
            cell = "N/A" if value < 0 else f"{value:.3f} {value_label}"
            row += f" {cell:>15} |"
        lines.append(row)
    lines.append(separator)
    return "\n".join(lines)


def export_csv(results: SummaryResults, sizes: List[int], file_path: str) -> None:
    """Export summarized benchmark results to CSV."""
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(",".join(["algorithm", *[f"n_{n}" for n in sizes]]) + "\n")
        for algorithm, timings in results.items():
            timing_map = dict(timings)
            row = [algorithm, *[f"{timing_map.get(n, -1):.6f}" for n in sizes]]
            file.write(",".join(row) + "\n")


def export_markdown(
    results: SummaryResults, sizes: List[int], value_label: str = "ms"
) -> str:
    """Generate a Markdown summary table."""
    headers = ["Algorithm", *[f"N={_size_label(n)}" for n in sizes]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for name, timings in results.items():
        timing_map = dict(timings)
        cells = []
        for n in sizes:
            value = timing_map.get(n, -1.0)
            cells.append("N/A" if value < 0 else f"{value:.3f} {value_label}")
        lines.append("| " + " | ".join([f"`{name}`", *cells]) + " |")
    return "\n".join(lines)


def export_json(
    results: SummaryResults,
    raw_results: RawResults,
    file_path: str,
    environment: Mapping[str, object],
    configuration: Mapping[str, object],
) -> None:
    """Export grouped samples, seed-level confidence intervals, and metadata."""
    measurements = []
    for algorithm, entries in raw_results.items():
        spec = ALGORITHM_SPECS.get(algorithm)
        summaries = dict(results[algorithm])
        sizes = sorted({int(entry["n"]) for entry in entries})
        for n in sizes:
            groups = [entry for entry in entries if int(entry["n"]) == n]
            samples = [
                float(sample)
                for group in groups
                for sample in group["samples_ms"]  # type: ignore[union-attr]
            ]
            seed_medians = [
                statistics.median(group["samples_ms"])  # type: ignore[arg-type]
                for group in groups
                if group["samples_ms"]
            ]
            measurements.append(
                {
                    "algorithm": algorithm,
                    "algorithm_family": spec.algorithm_family if spec else "unknown",
                    "execution_model": spec.execution_model if spec else "unknown",
                    "n": n,
                    "input_representation": (
                        spec.input_representation if spec else "unknown"
                    ),
                    "packed_equivalent_bytes": (n + 1) * 4,
                    "summary_ms": summaries[n],
                    "sample_groups": groups,
                    "statistics": sample_statistics(samples, confidence_samples=seed_medians),
                    "confidence_unit": "per-data-seed median",
                }
            )

    payload = {
        "schema_version": 2,
        "configuration": dict(configuration),
        "environment": dict(environment),
        "measurements": measurements,
    }
    Path(file_path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
