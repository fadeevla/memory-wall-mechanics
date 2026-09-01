"""Tests for reproducibility and benchmark result reporting."""

import json
import sys

import pytest

from duplicate_find.algorithms import ALGORITHM_SPECS
from duplicate_find.benchmark.memory_runner import measure_one
from duplicate_find.benchmark.reporter import (
    bootstrap_median_ci,
    export_json,
    sample_statistics,
)
from duplicate_find.benchmark.runner import run_benchmark


def test_sample_statistics_handles_single_and_multiple_samples():
    assert sample_statistics([2.0])["stdev_ms"] == 0.0
    stats = sample_statistics([1.0, 2.0, 9.0])
    assert stats["median_ms"] == 2.0
    assert stats["min_ms"] == 1.0
    assert stats["p95_ms"] > stats["median_ms"]
    assert stats["median_ci95_low_ms"] <= stats["median_ms"]
    assert stats["median_ci95_high_ms"] >= stats["median_ms"]


def test_statistics_align_point_estimate_and_confidence_units():
    stats = sample_statistics(
        [1.0, 100.0, 101.0, 10.0, 11.0, 12.0],
        confidence_samples=[100.0, 11.0],
    )
    assert stats["median_ms"] == 55.5
    assert stats["raw_sample_median_ms"] == 11.5
    assert stats["count"] == 2
    assert stats["technical_repeat_count"] == 6


def test_bootstrap_interval_is_deterministic():
    assert bootstrap_median_ci([1.0, 2.0, 3.0]) == bootstrap_median_ci(
        [1.0, 2.0, 3.0]
    )


def test_controlled_matrix_uses_one_algorithm_with_explicit_representations():
    list_spec = ALGORITHM_SPECS["findDuplicate_bit"]
    ndarray_spec = ALGORITHM_SPECS["findDuplicate_bit_python_numpy"]
    assert list_spec.function is ndarray_spec.function
    assert list_spec.algorithm_family == ndarray_spec.algorithm_family == "bit_counting"
    assert list_spec.input_representation == "python.list[int]"
    assert ndarray_spec.input_representation == "numpy.int32"


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="requires Linux procfs")
def test_isolated_memory_measurement_reports_attributable_rss():
    measurement = measure_one("findDuplicate_set", n=1000, seed=7, repeats=1)
    assert measurement["algorithm"] == "findDuplicate_set"
    assert measurement["baseline_rss_kib"] > 0
    assert measurement["peak_increment_kib"] >= 0


def test_runner_retains_raw_samples_and_exact_sizes():
    raw = {}
    summary = run_benchmark(
        algorithms=["findDuplicate_set"],
        sizes=[15],
        repeats=3,
        use_hugepages=False,
        warmup=False,
        verbose=False,
        seed=7,
        data_seeds=[11, 12],
        raw_results=raw,
    )
    assert summary["findDuplicate_set"][0][0] == 15
    assert len(raw["findDuplicate_set"]) == 2
    assert raw["findDuplicate_set"][0]["data_seed"] == 11
    assert len(raw["findDuplicate_set"][0]["samples_ms"]) == 3


def test_runner_aggregates_across_seed_level_statistics(monkeypatch):
    values = iter([1, 100, 101, 10, 11, 12])
    monkeypatch.setattr(
        "duplicate_find.benchmark.runner.time.perf_counter_ns",
        lambda: next(values) * 1_000_000,
    )
    summary = run_benchmark(
        algorithms=["findDuplicate_set"],
        sizes=[1],
        repeats=1,
        use_hugepages=False,
        warmup=False,
        verbose=False,
        data_seeds=[1, 2, 3],
        randomize_order=False,
    )
    # Per-seed elapsed values are 99, -91, and 1 ms; their median is 1 ms.
    assert summary["findDuplicate_set"] == [(1, 1.0)]


def test_json_export_contains_reproduction_metadata(tmp_path):
    path = tmp_path / "result.json"
    summary = {"findDuplicate_set": [(15, 2.0)]}
    raw = {
        "findDuplicate_set": [
            {"n": 15, "data_seed": 1, "samples_ms": [1.0, 2.0, 3.0]},
            {"n": 15, "data_seed": 2, "samples_ms": [2.0, 3.0, 4.0]},
        ]
    }
    export_json(summary, raw, str(path), {"python": "test"}, {"data_seeds": [1, 2]})
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["configuration"]["data_seeds"] == [1, 2]
    assert payload["measurements"][0]["statistics"]["median_ms"] == 2.5
    assert payload["measurements"][0]["confidence_unit"] == "per-data-seed median"
