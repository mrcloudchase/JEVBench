"""Judging policy nodes: how rulings are interpreted and combined.

Every policy is pure data in, data out. Values come from expressions over ``input`` and the
outputs of other nodes (``nodes.<id>``), so the same policy composes with any judge or graph.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, ClassVar, Literal

from pydantic import Field, model_validator

from jevbench.engine.context import Context
from jevbench.engine.expressions import parse
from jevbench.engine.nodes.base import Node, NodeConfig, Numeric, registry
from jevbench.errors import ExecutionError


# -- expr ----------------------------------------------------------------------------------------

class ExprConfig(NodeConfig):
    value: str = Field(description="Expression whose result is the node output.")


@registry.register
class ExprNode(Node):
    """General-purpose computation: comparisons, arithmetic, reshaping."""

    type_name = "expr"
    Config = ExprConfig
    expression_fields = ("value",)
    config: ExprConfig

    def execute(self, ctx: Context) -> Any:
        return ctx.eval(self.config.value)


# -- threshold -----------------------------------------------------------------------------------

class ThresholdConfig(NodeConfig):
    value: str
    min: Numeric | None = Field(default=None, description="Number, or an expression yielding one.")
    max: Numeric | None = Field(default=None, description="Number, or an expression yielding one.")
    exclusive: bool = False

    @model_validator(mode="after")
    def _bounds(self) -> "ThresholdConfig":
        if self.min is None and self.max is None:
            raise ValueError("threshold needs min and/or max")
        return self


@registry.register
class ThresholdNode(Node):
    """True when a numeric value lies within [min, max] (or strictly within, if exclusive)."""

    type_name = "threshold"
    Config = ThresholdConfig
    expression_fields = ("value",)
    numeric_fields = ("min", "max")
    config: ThresholdConfig

    def execute(self, ctx: Context) -> bool:
        value = ctx.eval(self.config.value)
        if not isinstance(value, (int, float)):
            raise ExecutionError(f"threshold value is not numeric: {value!r}", ctx.node_path(self.id))
        low, high = self.number(ctx, "min"), self.number(ctx, "max")
        exclusive = self.config.exclusive
        if low is not None and (value <= low if exclusive else value < low):
            return False
        if high is not None and (value >= high if exclusive else value > high):
            return False
        return True


# -- decide --------------------------------------------------------------------------------------

class Case(NodeConfig):
    when: str
    then: Any


class DecideConfig(NodeConfig):
    cases: list[Case] = Field(min_length=1)
    default: Any = None


@registry.register
class DecideNode(Node):
    """First matching case wins. Used for branching, escalation and abstention labels."""

    type_name = "decide"
    Config = DecideConfig
    template_fields = ("default",)
    config: DecideConfig

    def expressions(self) -> list[str]:
        from jevbench.engine.expressions import template_expressions

        found = super().expressions()
        for case in self.config.cases:
            parse(case.when)
            found.append(case.when)
            found.extend(template_expressions(case.then))
        return found

    def execute(self, ctx: Context) -> Any:
        for case in self.config.cases:
            if ctx.eval(case.when):
                return ctx.render(case.then)
        return ctx.render(self.config.default)


# -- shared: collecting values ------------------------------------------------------------------

class CollectConfig(NodeConfig):
    values: list[str] | None = Field(default=None, description="Expressions, one per value.")
    source: str | None = Field(default=None, alias="from", description="Expression yielding a list of values.")
    weights: list[float] | str | None = None

    model_config = {"extra": "forbid", "populate_by_name": True}

    @model_validator(mode="after")
    def _one_source(self) -> "CollectConfig":
        if (self.values is None) == (self.source is None):
            raise ValueError("give exactly one of 'values' or 'from'")
        return self


class CollectNode(Node):
    expression_fields = ("values", "source")
    config: CollectConfig

    def expressions(self) -> list[str]:
        found = super().expressions()
        if isinstance(self.config.weights, str):
            parse(self.config.weights)
            found.append(self.config.weights)
        return found

    def collect(self, ctx: Context) -> tuple[list[Any], list[float]]:
        if self.config.values is not None:
            values = [ctx.eval(e) for e in self.config.values]
        else:
            values = list(ctx.eval(self.config.source))
        weights = self.config.weights
        if isinstance(weights, str):
            weights = list(ctx.eval(weights))
        if weights is None:
            weights = [1.0] * len(values)
        if len(weights) != len(values):
            raise ExecutionError(f"{len(weights)} weights for {len(values)} values", ctx.node_path(self.id))
        return values, [float(w) for w in weights]


# -- vote ----------------------------------------------------------------------------------------

class VoteConfig(CollectConfig):
    method: Literal["plurality", "majority", "unanimous"] = "plurality"
    min_share: Numeric | None = Field(default=None, description="Required winner share; majority defaults to > 0.5.")
    tie: Literal["none", "first"] = "none"


@registry.register
class VoteNode(CollectNode):
    """Weighted voting over labels. Output: winner (or null), tally, share, unanimous."""

    type_name = "vote"
    Config = VoteConfig
    numeric_fields = ("min_share",)
    config: VoteConfig

    def execute(self, ctx: Context) -> dict[str, Any]:
        values, weights = self.collect(ctx)
        min_share = self.number(ctx, "min_share")
        tally: dict[Any, float] = {}
        for value, weight in zip(values, weights):
            tally[value] = tally.get(value, 0.0) + weight
        total = sum(tally.values())
        ranked = sorted(tally.items(), key=lambda kv: -kv[1])
        winner = ranked[0][0] if ranked else None
        share = ranked[0][1] / total if ranked and total else 0.0
        tied = len(ranked) > 1 and ranked[0][1] == ranked[1][1]
        unanimous = len(tally) == 1 and bool(values)
        if tied and self.config.tie == "none":
            winner = None
        if self.config.method == "unanimous" and not unanimous:
            winner = None
        if self.config.method == "majority" and not share > (min_share if min_share is not None else 0.5):
            winner = None
        if self.config.method == "plurality" and min_share is not None and share < min_share:
            winner = None
        return {"winner": winner, "tally": {str(k): v for k, v in tally.items()}, "share": round(share, 4),
                "total": total, "unanimous": unanimous, "tied": tied}


# -- aggregate -----------------------------------------------------------------------------------

class AggregateConfig(CollectConfig):
    method: Literal["mean", "sum", "min", "max", "median", "count", "any", "all", "spread", "product"] = "mean"


@registry.register
class AggregateNode(CollectNode):
    """Combine numeric or boolean values into one. ``mean`` honours weights (weighted mean)."""

    type_name = "aggregate"
    Config = AggregateConfig
    config: AggregateConfig

    def execute(self, ctx: Context) -> Any:
        values, weights = self.collect(ctx)
        method = self.config.method
        if method == "count":
            return len(values)
        if method == "any":
            return any(values)
        if method == "all":
            return all(values)
        numbers = []
        for v in values:
            if not isinstance(v, (int, float)) or isinstance(v, bool) and method not in ("sum", "mean"):
                raise ExecutionError(f"aggregate {method} needs numbers, got {v!r}", ctx.node_path(self.id))
            numbers.append(float(v))
        if not numbers:
            return None
        if method == "mean":
            total_w = sum(weights)
            return sum(v * w for v, w in zip(numbers, weights)) / total_w if total_w else 0.0
        if method == "sum":
            return sum(v * w for v, w in zip(numbers, weights))
        if method == "product":
            result = 1.0
            for v in numbers:
                result *= v
            return result
        if method == "min":
            return min(numbers)
        if method == "max":
            return max(numbers)
        if method == "median":
            ordered = sorted(numbers)
            mid = len(ordered) // 2
            return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
        if method == "spread":
            return max(numbers) - min(numbers)
        raise ExecutionError(f"unknown aggregate method {method}", ctx.node_path(self.id))


# -- consensus -----------------------------------------------------------------------------------

class ConsensusConfig(CollectConfig):
    tolerance: Numeric = Field(default=0.0, description="Max spread for numeric agreement; number or expression.")


@registry.register
class ConsensusNode(CollectNode):
    """Do independent judges agree? Labels must match exactly; numbers within tolerance."""

    type_name = "consensus"
    Config = ConsensusConfig
    numeric_fields = ("tolerance",)
    config: ConsensusConfig

    def execute(self, ctx: Context) -> dict[str, Any]:
        values, _ = self.collect(ctx)
        tolerance = self.number(ctx, "tolerance")
        if not values:
            return {"agreed": False, "value": None, "spread": None}
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            spread = max(values) - min(values)
            agreed = spread <= tolerance
            return {"agreed": agreed, "value": sum(values) / len(values) if agreed else None, "spread": spread}
        counts = Counter(values)
        agreed = len(counts) == 1
        return {"agreed": agreed, "value": values[0] if agreed else None, "spread": len(counts) - 1}


# -- constraint ----------------------------------------------------------------------------------

class Rule(NodeConfig):
    name: str
    require: str


class ConstraintConfig(NodeConfig):
    rules: list[Rule] = Field(min_length=1)


@registry.register
class ConstraintNode(Node):
    """Hard constraints: every rule must hold. Output lists the violated rule names."""

    type_name = "constraint"
    Config = ConstraintConfig
    config: ConstraintConfig

    def expressions(self) -> list[str]:
        found = super().expressions()
        for rule in self.config.rules:
            parse(rule.require)
            found.append(rule.require)
        return found

    def execute(self, ctx: Context) -> dict[str, Any]:
        violations = [rule.name for rule in self.config.rules if not ctx.eval(rule.require)]
        return {"satisfied": not violations, "violations": violations}
