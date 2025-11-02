"""
Minimal replacement for nptyping compatible with NumPy ≥ 2.0
Provides NDArray, Shape, DType and simple dtype markers such as Float64.
"""

from typing import TypeAlias, Any
import numpy as np

# Shape and dtype aliases
Shape: TypeAlias = tuple[int, ...]
DType: TypeAlias = type[np.dtype]

# Generic ndarray alias
NDArray: TypeAlias = np.ndarray[Any, np.dtype[Any]]

# Common dtype markers (for readability in hints)
Float64: TypeAlias = np.float64
Float32: TypeAlias = np.float32
Int32:   TypeAlias = np.int32
Int64:   TypeAlias = np.int64
Bool:    TypeAlias = np.bool_

__all__ = [
    "NDArray", "Shape", "DType",
    "Float64", "Float32", "Int32", "Int64", "Bool",
]
__version__ = "2.6.0-local"
