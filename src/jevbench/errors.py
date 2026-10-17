"""Exception hierarchy for JEVBench."""

from __future__ import annotations


class JevBenchError(Exception):
    """Base class for all JEVBench errors."""


class SchemaError(JevBenchError):
    """A framework file failed structural or semantic validation."""

    def __init__(self, problems: list[str] | str):
        self.problems = [problems] if isinstance(problems, str) else list(problems)
        super().__init__("\n".join(self.problems))


class ExpressionError(JevBenchError):
    """An expression could not be parsed or evaluated."""


class ProviderError(JevBenchError):
    """A provider is misconfigured or a provider call failed."""


class ExecutionError(JevBenchError):
    """A node failed while a framework was executing."""

    def __init__(self, message: str, node_path: str | None = None, trace=None):
        self.node_path = node_path
        self.trace = trace
        super().__init__(message)


class StoreError(JevBenchError):
    """The framework store could not save or load a framework."""
