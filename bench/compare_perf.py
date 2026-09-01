#!/usr/bin/env python3
"""Normalize perf-stat CSV artifacts by input elements and retired instructions."""

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional


def read_perf_csv(path: Path) -> Dict[str, float]:
    """Read numeric event counts from ``perf stat -x, --no-big-num`` output."""
    events = {}
    with path.open(encoding="utf-8") as file:
        for row in csv.reader(file):
            if len(row) < 3:
                continue
            try:
                value = float(row[0].strip())
            except ValueError:
                continue
            event = row[2].strip().split(":", 1)[0]
            events[event] = value
    return events


def _rate(events: Dict[str, float], event: str, work_items: int, scale: float = 1.0) -> Optional[float]:
    value = events.get(event)
    return value / work_items * scale if value is not None else None


def normalize(path: Path) -> Dict[str, object]:
    events = read_perf_csv(path)
    metadata_path = Path(f"{path}.metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    configuration = metadata["configuration"]
    work_items = int(configuration["n"]) * int(configuration["repeats"])
    cycles = events.get("cycles")
    instructions = events.get("instructions")
    derived = {
        "ipc": (
            instructions / cycles
            if cycles is not None and instructions is not None and cycles > 0
            else None
        ),
        "cycles_per_input_element": _rate(events, "cycles", work_items),
        "instructions_per_input_element": _rate(events, "instructions", work_items),
        "cache_misses_per_1000_elements": _rate(
            events, "cache-misses", work_items, 1000.0
        ),
        "l1d_load_misses_per_1000_elements": _rate(
            events, "L1-dcache-load-misses", work_items, 1000.0
        ),
        "dtlb_load_misses_per_1000_elements": _rate(
            events, "dTLB-load-misses", work_items, 1000.0
        ),
    }
    return {
        "source": str(path),
        "algorithm": configuration["algorithm"],
        "n": configuration["n"],
        "repeats": configuration["repeats"],
        "normalization_denominator": "n * repeats",
        "events": events,
        "derived": derived,
        "environment": metadata["environment"],
    }


def _format(value: Optional[float], digits: int = 3) -> str:
    return "N/A" if value is None else f"{value:.{digits}f}"


def render_markdown(payload: Dict[str, object]) -> str:
    lines = [
        "# Normalized hardware-counter comparison",
        "",
        "Counts are normalized by `N × repeats`. Generic cache events are proxies;",
        "they do not identify DRAM traffic or load latency by themselves.",
        "",
        "| Algorithm | IPC | Cycles/element | Instructions/element | L1D misses/1k | dTLB misses/1k |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in payload["runs"]:
        values = run["derived"]
        lines.append(
            f"| `{run['algorithm']}` | {_format(values['ipc'])} | "
            f"{_format(values['cycles_per_input_element'])} | "
            f"{_format(values['instructions_per_input_element'])} | "
            f"{_format(values['l1d_load_misses_per_1000_elements'])} | "
            f"{_format(values['dtlb_load_misses_per_1000_elements'])} |"
        )
    lines.extend(
        [
            "",
            "The algorithms perform different amounts of logical work per input element.",
            "These rates therefore describe complete algorithm executions, not one equivalent",
            "load or loop iteration.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("perf_csv", nargs="+")
    parser.add_argument("--json", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()
    payload = {
        "schema_version": 1,
        "runs": [normalize(Path(path)) for path in args.perf_csv],
    }
    Path(args.json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    Path(args.markdown).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
