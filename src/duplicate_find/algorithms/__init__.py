"""Algorithm catalog and registry."""

from typing import Callable, Dict, List

from .baselines import (
    findDuplicate_sort,
    findDuplicate_set,
    findDuplicate_bs,
    findDuplicate_floyd,
    findDuplicate_sign,
    findDuplicate_bit,
    findDuplicate_bit_optimal,
)
from .bit_numpy import (
    findDuplicate_bit_numpy,
    findDuplicate_bit_numpy_full,
)
from .bit_numba import (
    findDuplicate_bit_numba,
    findDuplicate_bit_numba_prange,
    findDuplicate_bit_optimal_numba,
    findDuplicate_floyd_numba,
    warmup_numba_kernels,
)

ALGORITHMS: Dict[str, Callable] = {
    # CPython Baselines
    "findDuplicate_sort": findDuplicate_sort,
    "findDuplicate_set": findDuplicate_set,
    "findDuplicate_bs": findDuplicate_bs,
    "findDuplicate_floyd": findDuplicate_floyd,
    "findDuplicate_sign": findDuplicate_sign,
    "findDuplicate_bit": findDuplicate_bit,
    "findDuplicate_bit_optimal": findDuplicate_bit_optimal,
    # NumPy
    "findDuplicate_bit_numpy": findDuplicate_bit_numpy,
    "findDuplicate_bit_numpy_full": findDuplicate_bit_numpy_full,
    # Numba JIT / Multi-threaded
    "findDuplicate_floyd_numba": findDuplicate_floyd_numba,
    "findDuplicate_bit_numba": findDuplicate_bit_numba,
    "findDuplicate_bit_optimal_numba": findDuplicate_bit_optimal_numba,
    "findDuplicate_bit_numba_prange": findDuplicate_bit_numba_prange,
}

__all__ = [
    "ALGORITHMS",
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
