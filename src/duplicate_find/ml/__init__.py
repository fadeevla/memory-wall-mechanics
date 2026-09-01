"""Small ML-oriented workloads used to connect benchmarks to inference systems."""

from .embedding_lookup import (
    embedding_bag_numba,
    embedding_bag_numpy,
    embedding_bag_python,
    embedding_bags_numba,
    embedding_bags_numpy,
    embedding_bags_python,
    embedding_bags_torch,
    warmup_embedding_numba,
)

__all__ = [
    "embedding_bag_python",
    "embedding_bag_numpy",
    "embedding_bag_numba",
    "embedding_bags_python",
    "embedding_bags_numpy",
    "embedding_bags_numba",
    "embedding_bags_torch",
    "warmup_embedding_numba",
]
