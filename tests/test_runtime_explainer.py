"""Tests for the generated Python runtime explanation."""

import sys

import numpy as np
import pytest

from duplicate_find.benchmark.runtime_explainer import (
    collect_representation_metadata,
    measure_representation_memory,
    sum_low_bits_numba_parallel,
    sum_low_bits_numba_serial,
    sum_low_bits_python,
)


def test_low_bit_reductions_agree():
    values = np.arange(101, dtype=np.int32)
    expected = sum_low_bits_python(values.tolist())
    assert sum_low_bits_numba_serial(values) == expected
    assert sum_low_bits_numba_parallel(values) == expected


def test_representation_metadata_distinguishes_ownership_and_strides():
    metadata = collect_representation_metadata(100)
    assert metadata["list_deep_bytes"] > metadata["ndarray"]["nbytes"]
    assert metadata["ndarray"]["strides"] == (4,)
    assert metadata["strided_view"]["strides"] == (8,)
    assert metadata["strided_view"]["shares_memory"] is True
    assert metadata["strided_view"]["c_contiguous"] is False


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="requires Linux procfs")
def test_memory_worker_reports_tracemalloc_and_rss():
    result = measure_representation_memory("numpy.int32", 1000)
    assert result["tracemalloc_peak_bytes"] >= 4000
    assert result["rss_before_kib"] > 0
    assert result["rss_after_kib"] > 0
