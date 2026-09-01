"""Algorithm catalog, metadata, and compatibility registry."""

from dataclasses import dataclass
from typing import Callable, Dict, Optional

import numpy as np

from .baselines import (
    findDuplicate_bit,
    findDuplicate_bit_optimal,
    findDuplicate_bs,
    findDuplicate_floyd,
    findDuplicate_set,
    findDuplicate_sign,
    findDuplicate_sort,
)
from .bit_numba import (
    findDuplicate_bit_numba,
    findDuplicate_bit_numba_prange,
    findDuplicate_bit_optimal_numba,
    findDuplicate_floyd_numba,
    warmup_numba_kernels,
)
from .bit_numpy import findDuplicate_bit_numpy, findDuplicate_bit_numpy_full


@dataclass(frozen=True)
class AlgorithmSpec:
    """Describe execution and input requirements independently of a function name."""

    function: Callable[[object], int]
    algorithm_family: str
    execution_model: str
    input_representation: str
    mutates_temporarily: bool = False
    compiled: bool = False
    temporary_bytes: Optional[Callable[[int], int]] = None

    def prepare_input(self, canonical: np.ndarray) -> object:
        """Create the representation expected by this implementation."""
        if self.input_representation == "numpy.int32":
            return canonical.copy()
        if self.input_representation == "python.list[int]":
            return canonical.tolist()
        raise ValueError(f"unsupported input representation: {self.input_representation}")


def _broadcast_bytes(n: int) -> int:
    return (n + 1) * n.bit_length() * np.dtype(np.int32).itemsize


ALGORITHM_SPECS: Dict[str, AlgorithmSpec] = {
    "findDuplicate_sort": AlgorithmSpec(
        findDuplicate_sort, "sorting", "cpython", "python.list[int]"
    ),
    "findDuplicate_set": AlgorithmSpec(
        findDuplicate_set, "hash_set", "cpython", "python.list[int]"
    ),
    "findDuplicate_bs": AlgorithmSpec(
        findDuplicate_bs, "value_binary_search", "cpython", "python.list[int]"
    ),
    "findDuplicate_floyd": AlgorithmSpec(
        findDuplicate_floyd, "floyd", "cpython", "python.list[int]"
    ),
    "findDuplicate_sign": AlgorithmSpec(
        findDuplicate_sign,
        "sign_marking",
        "cpython",
        "python.list[int]",
        mutates_temporarily=True,
    ),
    "findDuplicate_bit": AlgorithmSpec(
        findDuplicate_bit, "bit_counting", "cpython", "python.list[int]"
    ),
    # Controlled counterpart: identical Python bytecode over packed ndarray scalars.
    "findDuplicate_bit_python_numpy": AlgorithmSpec(
        findDuplicate_bit, "bit_counting", "cpython", "numpy.int32"
    ),
    "findDuplicate_bit_optimal": AlgorithmSpec(
        findDuplicate_bit_optimal, "bit_counting_single_pass", "cpython", "python.list[int]"
    ),
    "findDuplicate_bit_numpy": AlgorithmSpec(
        findDuplicate_bit_numpy, "bit_counting", "numpy", "numpy.int32"
    ),
    "findDuplicate_bit_numpy_full": AlgorithmSpec(
        findDuplicate_bit_numpy_full,
        "bit_counting",
        "numpy_broadcast",
        "numpy.int32",
        temporary_bytes=_broadcast_bytes,
    ),
    "findDuplicate_floyd_numba": AlgorithmSpec(
        findDuplicate_floyd_numba, "floyd", "numba", "numpy.int32", compiled=True
    ),
    "findDuplicate_bit_numba": AlgorithmSpec(
        findDuplicate_bit_numba, "bit_counting", "numba", "numpy.int32", compiled=True
    ),
    "findDuplicate_bit_optimal_numba": AlgorithmSpec(
        findDuplicate_bit_optimal_numba,
        "bit_counting_single_pass",
        "numba",
        "numpy.int32",
        compiled=True,
    ),
    "findDuplicate_bit_numba_prange": AlgorithmSpec(
        findDuplicate_bit_numba_prange,
        "bit_counting",
        "numba_parallel",
        "numpy.int32",
        compiled=True,
    ),
}

# Compatibility mapping retained for callers that only need name -> callable.
ALGORITHMS: Dict[str, Callable[[object], int]] = {
    name: spec.function for name, spec in ALGORITHM_SPECS.items()
}

__all__ = [
    "ALGORITHMS",
    "ALGORITHM_SPECS",
    "AlgorithmSpec",
    "findDuplicate_sort",
    "findDuplicate_set",
    "findDuplicate_bs",
    "findDuplicate_floyd",
    "findDuplicate_sign",
    "findDuplicate_bit",
    "findDuplicate_bit_optimal",
    "findDuplicate_bit_numpy",
    "findDuplicate_bit_numpy_full",
    "findDuplicate_bit_numba",
    "findDuplicate_bit_numba_prange",
    "findDuplicate_bit_optimal_numba",
    "findDuplicate_floyd_numba",
    "warmup_numba_kernels",
]
