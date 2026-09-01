"""Correctness tests for the ML-oriented embedding-bag workload."""

import numpy as np
import pytest

from duplicate_find.ml import (
    embedding_bag_numba,
    embedding_bag_numpy,
    embedding_bag_python,
    embedding_bags_numba,
    embedding_bags_numpy,
    embedding_bags_python,
    embedding_bags_torch,
)


def test_embedding_implementations_agree_without_mutation():
    rng = np.random.default_rng(7)
    table = rng.standard_normal((32, 8), dtype=np.float32)
    indices = np.array([7, 1, 7, 15, 2], dtype=np.int64)
    original_table = table.copy()
    original_indices = indices.copy()

    expected = embedding_bag_numpy(table, indices)
    np.testing.assert_allclose(embedding_bag_python(table, indices), expected, rtol=1e-5)
    np.testing.assert_allclose(embedding_bag_numba(table, indices), expected, rtol=1e-5)
    np.testing.assert_array_equal(table, original_table)
    np.testing.assert_array_equal(indices, original_indices)


def test_batched_embedding_implementations_agree():
    rng = np.random.default_rng(11)
    table = rng.standard_normal((32, 8), dtype=np.float32)
    indices = np.array([7, 1, 7, 15, 2, 3], dtype=np.int64)
    offsets = np.array([0, 2, 5, 6], dtype=np.int64)
    expected = embedding_bags_numpy(table, indices, offsets)
    np.testing.assert_allclose(
        embedding_bags_python(table, indices, offsets), expected, rtol=1e-5
    )
    np.testing.assert_allclose(
        embedding_bags_numba(table, indices, offsets), expected, rtol=1e-5
    )


def test_torch_embedding_bag_agrees_when_available():
    torch = pytest.importorskip("torch")
    rng = np.random.default_rng(13)
    table = rng.standard_normal((32, 8), dtype=np.float32)
    indices = np.array([7, 1, 7, 15, 2, 3], dtype=np.int64)
    offsets = np.array([0, 2, 5, 6], dtype=np.int64)
    expected = embedding_bags_numpy(table, indices, offsets)
    result = embedding_bags_torch(
        torch.from_numpy(table), torch.from_numpy(indices), torch.from_numpy(offsets)
    )
    np.testing.assert_allclose(result.numpy(), expected, rtol=1e-5)
