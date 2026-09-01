"""Batched CPU embedding-bag implementations with equivalent packed inputs."""

from typing import Any

import numpy as np
from numba import njit


def embedding_bags_python(
    table: np.ndarray, indices: np.ndarray, offsets: np.ndarray
) -> np.ndarray:
    """Sum rows into multiple bags using CPython loops."""
    output = np.zeros((len(offsets) - 1, table.shape[1]), dtype=np.float32)
    for bag in range(len(offsets) - 1):
        for position in range(offsets[bag], offsets[bag + 1]):
            row_index = indices[position]
            for column in range(table.shape[1]):
                output[bag, column] += table[row_index, column]
    return output


def embedding_bags_numpy(
    table: np.ndarray, indices: np.ndarray, offsets: np.ndarray
) -> np.ndarray:
    """Gather all rows, then reduce each non-empty bag with NumPy."""
    gathered = table[indices]
    return np.add.reduceat(gathered, offsets[:-1], axis=0, dtype=np.float32)


@njit
def embedding_bags_numba(
    table: np.ndarray, indices: np.ndarray, offsets: np.ndarray
) -> np.ndarray:
    """Fuse batched row gathering and accumulation without a gathered tensor."""
    output = np.zeros((len(offsets) - 1, table.shape[1]), dtype=np.float32)
    for bag in range(len(offsets) - 1):
        for position in range(offsets[bag], offsets[bag + 1]):
            row_index = indices[position]
            for column in range(table.shape[1]):
                output[bag, column] += table[row_index, column]
    return output


def embedding_bags_torch(weight: Any, indices: Any, offsets: Any) -> Any:
    """Run PyTorch's optimized CPU embedding_bag on pre-created tensors."""
    import torch.nn.functional as functional

    return functional.embedding_bag(
        indices,
        weight,
        offsets,
        mode="sum",
        include_last_offset=True,
    )


def embedding_bag_python(table: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """Backward-compatible single-bag wrapper."""
    offsets = np.array([0, len(indices)], dtype=np.int64)
    return embedding_bags_python(table, indices, offsets)[0]


def embedding_bag_numpy(table: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """Backward-compatible single-bag wrapper."""
    offsets = np.array([0, len(indices)], dtype=np.int64)
    return embedding_bags_numpy(table, indices, offsets)[0]


def embedding_bag_numba(table: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """Backward-compatible single-bag wrapper."""
    offsets = np.array([0, len(indices)], dtype=np.int64)
    return embedding_bags_numba(table, indices, offsets)[0]


def warmup_embedding_numba() -> None:
    """Compile the batched Numba kernel outside measured regions."""
    table = np.ones((2, 2), dtype=np.float32)
    indices = np.array([0, 1], dtype=np.int64)
    offsets = np.array([0, 1, 2], dtype=np.int64)
    embedding_bags_numba(table, indices, offsets)
