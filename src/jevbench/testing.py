"""Declarative framework tests: run cases, evaluate expectations, report."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jevbench.engine.executor import run
from jevbench.engine.expressions import evaluate
from jevbench.errors import JevBenchError
from jevbench.providers.config import ProviderRegistry
from jevbench.schema.models import Framework, TestCase


@dataclass
class CaseResult:
    name: str
    passed: bool
    judgment: Any = None
    failures: list[str] = field(default_factory=list)
    error: str | None = None
    api_calls: int = 0
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class TestReport:
    results: list[CaseResult]

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def counts(self) -> tuple[int, int]:
        ok = sum(1 for r in self.results if r.passed)
        return ok, len(self.results) - ok

    def to_dict(self) -> dict[str, Any]:
        ok, failed = self.counts
        return {"passed": ok, "failed": failed, "results": [r.to_dict() for r in self.results]}


def run_tests(framework: Framework, cases: list[TestCase] | None = None, *, providers: ProviderRegistry | None = None,
              base_dir: str | Path | None = None, store=None, mock_all: bool = False, live: bool = False,
              max_workers: int = 8) -> TestReport:
    """Run test cases. Cases that define ``mock`` never call a provider; others do unless ``mock_all``.

    ``live=False`` (the default) skips cases that would need a provider, so a plain
    ``jevbench test`` is always offline; pass ``live=True`` to run them for real.
    """
    cases = framework.tests if cases is None else cases
    results: list[CaseResult] = []
    for case in cases:
        offline = mock_all or bool(case.mock)
        if not offline and not live:
            results.append(CaseResult(case.name, True, failures=[], error="skipped: needs a provider (use --live or add mock)"))
            continue
        try:
            result = run(framework, case.input, providers=providers, mocks=case.mock or None,
                         mock_all=mock_all or (offline and not case.mock), max_workers=max_workers,
                         base_dir=base_dir, store=store)
        except JevBenchError as exc:
            results.append(CaseResult(case.name, False, error=str(exc)))
            continue
        scope = {"input": result.trace.input, "nodes": _outputs(result), "judgment": result.judgment, "loop": None}
        failures = []
        for expression in case.expect:
            try:
                if not evaluate(expression, scope):
                    failures.append(f"{expression}  (false)")
            except JevBenchError as exc:
                failures.append(f"{expression}  ({exc})")
        if case.expect_judgment is not None and result.judgment != case.expect_judgment:
            failures.append(f"judgment {result.judgment!r} != expected {case.expect_judgment!r}")
        results.append(CaseResult(case.name, not failures, result.judgment, failures,
                                  api_calls=result.trace.totals()["api_calls"], duration_ms=result.trace.duration_ms))
    return TestReport(results)


def _outputs(result) -> dict[str, Any]:
    return {trace.id: trace.output for trace in result.trace.nodes}
