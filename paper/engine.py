"""A minimal object-oriented engine for decision architectures.

    evidence + question  ->  belief      (Believe, through a Model)
    beliefs  + values    ->  decision    (Decide, through Expressions)
    decision             ->  evidence    (any node's value may feed another node)

A Question declares alternatives, unordered (Nominal) or ordered (Ordinal). A Belief is a calibrated
distribution over them. An Expression is an operator object; Python's own operators build the tree.
A node is an expression too, so `intent.confidence >= 0.6` is a rule. An Architecture is whatever
its output node references: levels are inferred, independent beliefs run concurrently, and an
Architecture can be a node of another (Use).
"""

from __future__ import annotations

import json
import operator
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable


# ====================================================================== questions and beliefs
@dataclass(frozen=True)
class Nominal:
    """An unordered set of alternatives. Two alternatives is the yes/no case."""
    instructions: str
    alternatives: dict                                   # name -> description or None

    def wire(self): return {"type": "choice", "instructions": self.instructions, "criteria": self.alternatives}
    def belief(self, a): return Belief(dict(a["probabilities"]), a["confidence"], ordered=False)


@dataclass(frozen=True)
class Ordinal:
    """An ordered set of alternatives, lowest to highest."""
    instructions: str
    levels: list

    def wire(self): return {"type": "score", "instructions": self.instructions, "criteria": self.levels}
    def belief(self, a): return Belief({str(k): v for k, v in a["probabilities"].items()}, a["confidence"], ordered=True)


@dataclass(frozen=True)
class Belief:
    """A calibrated distribution over a question's alternatives, with a confidence."""
    probabilities: dict
    confidence: float
    ordered: bool

    @property
    def top(self): return max(self.probabilities, key=self.probabilities.get)

    def p(self, alternative): return self.probabilities.get(str(alternative), 0.0)

    @property
    def margin(self):
        ps = sorted(self.probabilities.values(), reverse=True)
        return ps[0] - (ps[1] if len(ps) > 1 else 0.0)

    @property
    def expected(self):                                  # ordinal only
        return sum(int(k) * v for k, v in self.probabilities.items())

    def at_least(self, level):                           # ordinal only
        return sum(v for k, v in self.probabilities.items() if int(k) >= level)


# ====================================================================== model
class Model:
    """The only thing that turns evidence and a question into a belief."""

    def __init__(self, name="jev-latest", key=None, url="https://api.typesafe.ai/v1/systemone"):
        self.name, self.key, self.url = name, key or os.environ["TYPESAFE_API_KEY"], url

    def believe(self, evidence, question) -> Belief:
        body = json.dumps({"model": self.name, "state": evidence, "questions": {"q": question.wire()}}).encode()
        req = urllib.request.Request(self.url, data=body, headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        return question.belief(json.loads(urllib.request.urlopen(req).read())["answers"]["q"])


# ====================================================================== expressions
class Expr:
    """A deterministic computation over beliefs and values. eval runs it; refs lists the nodes it reads."""

    def eval(self, ctx: dict) -> Any: raise NotImplementedError
    def refs(self) -> set: return set()

    def __lt__(self, o): return Op(operator.lt, self, o)
    def __le__(self, o): return Op(operator.le, self, o)
    def __gt__(self, o): return Op(operator.gt, self, o)
    def __ge__(self, o): return Op(operator.ge, self, o)
    def __eq__(self, o): return Op(operator.eq, self, o)          # type: ignore[override]
    def __ne__(self, o): return Op(operator.ne, self, o)          # type: ignore[override]
    __hash__ = object.__hash__
    def __add__(self, o): return Op(operator.add, self, o)
    def __sub__(self, o): return Op(operator.sub, self, o)
    def __mul__(self, o): return Op(operator.mul, self, o)
    def __truediv__(self, o): return Op(operator.truediv, self, o)
    def __and__(self, o): return Op(lambda a, b: bool(a) and bool(b), self, o)
    def __or__(self, o): return Op(lambda a, b: bool(a) or bool(b), self, o)
    def __invert__(self): return Op(lambda a, _: not a, self, None)
    def is_none(self): return Op(operator.is_, self, None)

    def __getattr__(self, name):                         # belief.confidence, belief.top, ...
        if name.startswith("_"):
            raise AttributeError(name)
        return Op(lambda v, n: v[n] if isinstance(v, dict) else getattr(v, n), self, name)
    def __getitem__(self, key): return Op(operator.getitem, self, key)
    def __call__(self, *args): return Aggregate(lambda v: v[0](*v[1:]), self, *args)


def lift(x) -> Expr: return x if isinstance(x, Expr) else Const(x)


@dataclass(frozen=True, eq=False)
class Const(Expr):
    value: Any
    def eval(self, ctx): return self.value


class Input(Expr):
    """The evidence the architecture was given."""
    def eval(self, ctx): return ctx["input"]


class Op(Expr):
    """A binary operator: comparison, arithmetic, boolean, or access."""
    def __init__(self, fn: Callable, left, right):
        self.fn, self.left, self.right = fn, lift(left), lift(right)
    def eval(self, ctx): return self.fn(self.left.eval(ctx), self.right.eval(ctx))
    def refs(self): return self.left.refs() | self.right.refs()


class Aggregate(Expr):
    """Reduce several values to one with any function: sum, max, mean, majority, ..."""
    def __init__(self, fn: Callable, *items):
        self.fn, self.items = fn, [lift(i) for i in items]
    def eval(self, ctx): return self.fn([i.eval(ctx) for i in self.items])
    def refs(self): return set().union(*[i.refs() for i in self.items])


class Select(Expr):
    """First case whose condition holds, else the default: routing, abstention, veto."""
    def __init__(self, *cases, default=None):
        self.cases, self.default = [(lift(c), lift(v)) for c, v in cases], lift(default)
    def eval(self, ctx):
        for cond, value in self.cases:
            if cond.eval(ctx):
                return value.eval(ctx)
        return self.default.eval(ctx)
    def refs(self): return set().union(*[c.refs() | v.refs() for c, v in self.cases]) | self.default.refs()


class Evidence(Expr):
    """Shape evidence for a question from the input and earlier nodes."""
    def __init__(self, **fields):
        self.fields = {k: lift(v) for k, v in fields.items()}
    def eval(self, ctx): return {k: v.eval(ctx) for k, v in self.fields.items()}
    def refs(self): return set().union(*[v.refs() for v in self.fields.values()])


def majority(xs):
    xs = [x for x in xs if x is not None]
    best = max(set(xs), key=xs.count) if xs else None
    return best if best is not None and xs.count(best) > len(xs) / 2 else None


# ====================================================================== nodes
class Node(Expr):
    """A unit of an architecture. Referring to a node in an expression reads its value."""
    when: Expr | None = None

    def eval(self, ctx): return ctx[self]
    def refs(self): return {self}
    def dependencies(self) -> set: return self.when.refs() if self.when is not None else set()
    def compute(self, ctx, model): raise NotImplementedError


class Believe(Node):
    """evidence + question -> belief"""
    def __init__(self, question, evidence=None, model=None, when=None):
        self.question, self.evidence, self.when = question, lift(evidence) if evidence is not None else Input(), when
        self.model = Model(model) if isinstance(model, str) else model
    def dependencies(self): return super().dependencies() | self.evidence.refs()
    def compute(self, ctx, model): return (self.model or model).believe(self.evidence.eval(ctx), self.question)


class Decide(Node):
    """beliefs + values -> decision"""
    def __init__(self, rule, when=None):
        self.rule, self.when = lift(rule), when
    def dependencies(self): return super().dependencies() | self.rule.refs()
    def compute(self, ctx, model): return self.rule.eval(ctx)


class Use(Node):
    """An architecture as a node: its decision is a value here, and may be evidence elsewhere."""
    def __init__(self, architecture, evidence=None, when=None):
        self.architecture, self.evidence, self.when = architecture, lift(evidence) if evidence is not None else Input(), when
    def dependencies(self): return super().dependencies() | self.evidence.refs()
    def compute(self, ctx, model): return self.architecture(self.evidence.eval(ctx))


# ====================================================================== architecture
class Architecture:
    """Everything reachable from its output node. Levels are inferred; beliefs in a level run concurrently."""

    def __init__(self, output: Node, model: Model | None = None, workers: int = 8):
        self.output, self.model, self.workers = output, model or Model(), workers
        self.levels = self._levels()

    def _levels(self):
        nodes, stack = set(), [self.output]
        while stack:
            n = stack.pop()
            if n not in nodes:
                nodes.add(n); stack.extend(n.dependencies())
        remaining, levels = {n: n.dependencies() for n in nodes}, []
        while remaining:
            ready = [n for n, d in remaining.items() if not d]
            if not ready:
                raise ValueError("cycle: feedback needs an explicit bound")
            levels.append(ready)
            for n in ready: del remaining[n]
            for d in remaining.values(): d.difference_update(ready)
        return levels

    def run(self, input) -> dict:
        ctx = {"input": input}
        def step(n):
            return n, (n.compute(ctx, self.model) if n.when is None or n.when.eval(ctx) else None)
        for level in self.levels:
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                for n, v in pool.map(step, level):
                    ctx[n] = v
        return ctx

    def __call__(self, input): return self.run(input)[self.output]

    @property
    def calls(self) -> int:
        """Upper bound on model calls per run."""
        return sum(n.architecture.calls if isinstance(n, Use) else isinstance(n, Believe) for level in self.levels for n in level)
