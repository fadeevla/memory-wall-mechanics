#!/usr/bin/env python3
"""Compare random and sorted embedding runs using paired data-seed effects."""

import argparse
import json
import statistics
from pathlib import Path
from typing import Dict, List, Mapping


def _seed_medians(measurement: Mapping[str, object]) -> Dict[int, float]:
    groups = measurement["sample_groups"]
    return {
        int(group["data_seed"]): statistics.median(group["samples_ms"])
        for group in groups
    }


def _percentile(values: List[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _bootstrap_median(values: List[float], resamples: int = 10_000) -> List[float]:
    import random

    rng = random.Random(0)
    count = len(values)
    estimates = [
        statistics.median(values[rng.randrange(count)] for _ in range(count))
        for _ in range(resamples)
    ]
    return [_percentile(estimates, 0.025), _percentile(estimates, 0.975)]


def compare_payloads(
    random_payload: Mapping[str, object], sorted_payload: Mapping[str, object]
) -> Dict[str, object]:
    """Return paired sorted/random effects for matching implementations and seeds."""
    random_config = random_payload["configuration"]
    sorted_config = sorted_payload["configuration"]
    ignored = {"locality", "json"}
    for key in set(random_config) | set(sorted_config):
        if key not in ignored and random_config.get(key) != sorted_config.get(key):
            raise ValueError(f"configuration mismatch for {key}")

    random_measurements = random_payload["measurements"]
    sorted_measurements = sorted_payload["measurements"]
    if set(random_measurements) != set(sorted_measurements):
        raise ValueError("implementation sets do not match")

    effects = {}
    for implementation in sorted(random_measurements):
        baseline = _seed_medians(random_measurements[implementation])
        comparison = _seed_medians(sorted_measurements[implementation])
        if set(baseline) != set(comparison):
            raise ValueError(f"data seeds do not match for {implementation}")
        pairs = []
        for seed in sorted(baseline):
            ratio = comparison[seed] / baseline[seed]
            pairs.append(
                {
                    "data_seed": seed,
                    "random_median_ms": baseline[seed],
                    "sorted_median_ms": comparison[seed],
                    "sorted_minus_random_ms": comparison[seed] - baseline[seed],
                    "sorted_over_random_ratio": ratio,
                    "percent_change": (ratio - 1.0) * 100.0,
                }
            )
        ratios = [pair["sorted_over_random_ratio"] for pair in pairs]
        interval = _bootstrap_median(ratios)
        effects[implementation] = {
            "paired_seed_count": len(pairs),
            "pairs": pairs,
            "median_sorted_over_random_ratio": statistics.median(ratios),
            "median_percent_change": (statistics.median(ratios) - 1.0) * 100.0,
            "median_ratio_ci95": interval,
            "supports_directional_change": not (interval[0] <= 1.0 <= interval[1]),
        }

    return {
        "schema_version": 1,
        "method": (
            "paired per-data-seed medians; percentile bootstrap over sorted/random ratios"
        ),
        "random_source": random_config.get("json"),
        "sorted_source": sorted_config.get("json"),
        "effects": effects,
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    lines = [
        "# Paired embedding-locality analysis",
        "",
        "Each effect pairs the random and sorted-within-bag median for the same data",
        "seed. A ratio above 1 means sorting was slower. The interval bootstraps the",
        "paired ratios, rather than comparing two marginal confidence intervals.",
        "",
        "| Implementation | Seeds | Median change | Ratio 95% CI | Direction detected |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name, effect in payload["effects"].items():
        interval = effect["median_ratio_ci95"]
        lines.append(
            f"| `{name}` | {effect['paired_seed_count']} | "
            f"{effect['median_percent_change']:+.2f}% | "
            f"[{interval[0]:.3f}, {interval[1]:.3f}] | "
            f"{'yes' if effect['supports_directional_change'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "A non-detection means this experiment did not resolve a directional effect;",
            "it is not evidence that the true effect is exactly zero.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("random_json")
    parser.add_argument("sorted_json")
    parser.add_argument("--json", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()

    random_payload = json.loads(Path(args.random_json).read_text(encoding="utf-8"))
    sorted_payload = json.loads(Path(args.sorted_json).read_text(encoding="utf-8"))
    payload = compare_payloads(random_payload, sorted_payload)
    payload["random_source"] = args.random_json
    payload["sorted_source"] = args.sorted_json
    Path(args.json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    Path(args.markdown).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
