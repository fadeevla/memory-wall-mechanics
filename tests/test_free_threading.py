"""Tests for the stdlib-only CPython free-threading experiment."""

import sys

from duplicate_find.benchmark.free_threading import run_worker, sum_low_bits


def test_sum_low_bits_handles_even_and_odd_lengths():
    assert sum_low_bits(list(range(10))) == 5
    assert sum_low_bits(list(range(11))) == 5


def test_worker_records_runtime_gil_and_thread_measurements():
    result = run_worker(length=1000, repeats=2)
    assert isinstance(result["gil_enabled_at_runtime"], bool)
    assert result["python_int_zero_bytes"] == sys.getsizeof(0)
    assert result["python_compiler"]
    assert len(result["executable_sha256"]) == 64
    assert result["length_per_task"] == 1000
    assert set(result["measurements"]) == {
        "one_task",
        "two_tasks_sequential",
        "two_tasks_threads",
    }
    assert result["thread_speedup_for_two_tasks"] > 0
