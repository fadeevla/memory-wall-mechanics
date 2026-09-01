"""Tests for paired embedding-locality reporting."""

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bench" / "compare_embedding_locality.py"
SPEC = importlib.util.spec_from_file_location("compare_embedding_locality", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _payload(locality, groups):
    return {
        "configuration": {"locality": locality, "rows": 10, "json": "ignored.json"},
        "measurements": {"kernel": {"sample_groups": groups}},
    }


def test_paired_locality_effect_uses_matching_seed_medians():
    random_payload = _payload(
        "random",
        [
            {"data_seed": 1, "samples_ms": [1.0, 2.0, 3.0]},
            {"data_seed": 2, "samples_ms": [3.0, 4.0, 5.0]},
        ],
    )
    sorted_payload = _payload(
        "sorted-within-bag",
        [
            {"data_seed": 1, "samples_ms": [2.0, 4.0, 6.0]},
            {"data_seed": 2, "samples_ms": [6.0, 8.0, 10.0]},
        ],
    )
    effect = MODULE.compare_payloads(random_payload, sorted_payload)["effects"]["kernel"]
    assert effect["paired_seed_count"] == 2
    assert effect["median_sorted_over_random_ratio"] == 2.0
    assert effect["median_percent_change"] == 100.0
