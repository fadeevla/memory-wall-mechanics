"""Tests for normalized perf-stat reporting."""

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bench" / "compare_perf.py"
SPEC = importlib.util.spec_from_file_location("compare_perf", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_perf_counts_are_normalized_by_total_elements(tmp_path):
    csv_path = tmp_path / "run.csv"
    csv_path.write_text(
        "2000,,cycles,100.00,\n1000,,instructions,100.00,\n"
        "20,,L1-dcache-load-misses,100.00,\n",
        encoding="utf-8",
    )
    Path(f"{csv_path}.metadata.json").write_text(
        json.dumps(
            {
                "configuration": {"algorithm": "example", "n": 100, "repeats": 2},
                "environment": {},
            }
        ),
        encoding="utf-8",
    )
    run = MODULE.normalize(csv_path)
    assert run["derived"]["ipc"] == 0.5
    assert run["derived"]["cycles_per_input_element"] == 10.0
    assert run["derived"]["l1d_load_misses_per_1000_elements"] == 100.0
