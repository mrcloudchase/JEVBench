"""JEVBench: a file-driven workbench for judging frameworks built on JEV decision models."""

from jevbench.api import (
    inspect_framework,
    load_framework,
    run_framework,
    run_tests,
    validate_framework,
)
from jevbench.errors import (
    ExecutionError,
    ExpressionError,
    JevBenchError,
    ProviderError,
    SchemaError,
    StoreError,
)

__version__ = "0.1.0"

__all__ = [
    "ExecutionError",
    "ExpressionError",
    "JevBenchError",
    "ProviderError",
    "SchemaError",
    "StoreError",
    "inspect_framework",
    "load_framework",
    "run_framework",
    "run_tests",
    "validate_framework",
]
