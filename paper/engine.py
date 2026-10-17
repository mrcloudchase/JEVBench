"""A minimal object-oriented engine for decision architectures.

    evidence + question  ->  belief      (a Believe node, through a Model)
    beliefs  + values    ->  decision    (a Decide node, through Expressions)
    decision             ->  evidence    (any node's value may feed another node)

Questions declare alternatives (Nominal, Ordinal; Binary is Nominal with two). Beliefs are calibrated
distributions over them. Expressions are operator objects (Compare, Arithmetic, Boolean, Aggregate,
Select) built with ordinary Python operators. Nodes are expressions too, so `node.confidence >= 0.6`
is a valid rule. An Architecture is identified by its output node; the graph is discovered from
references, independent beliefs run concurrently, and an Architecture can itself be a node (Use).
"""

from __future__ import annotations

import json
import operator
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable


# ====================================================================== questions
class Question:
    """A declared set of alternatives. The set is unordered (Nominal) or ordered (Ordinal)."""

    def wire(self) -> dict: raise NotImplementedError
    def belief(self, answer: dict) -> "Belief": raise NotImplementedError


@dataclass(frozen=True)
class Nominal(Question):
    instructions: str
    alternatives: dict                      # name -> description or None

    def wire(self): return {"type": "choice", "instructions": self.instructions, "criteria": self.alternatives}
    def belief(self, a): return Belief(dict(a["probabilities"]), a["confidence"], ordered=False)


@dataclass(frozen=True)
class Binary(Question):
    """Nominal with two alternatives, yes and no. The wire's noul."""
    instructions: str

    def wire(self): return {"type": "noul", "instructions": self.instructions}
    def belief(self, a):
        p = a["noul"]
        return Belief({"yes": p, "no": 1 - p}, abs(2 * p - 1), ordered=False)


@dataclass(frozen=True)
class Ordinal(Question):
    instructions: str
    levels: list                            # lowest to highest

    def wire(self): return {"type": "score", "instructions": self.instructions, "criteria": self.levels}
    def belief(self, a): return Belief({str(k): v for k, v in a["probabilities"].items()}, a["confidence"], ordered=True)


# ====================================================================== beliefs
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
    def expected(self):                     # ordinal only
        assert self.ordered, "expected position needs an ordered question"
        return sum(int(k) * v for k, v in self.probabilities.items())

    def at_least(self, level):              # ordinal only
        assert self.ordered, "at_least needs an ordered question"
        return sum(v for k, v in self.probabilities.items() if int(k) >= level)


# ====================================================================== model
class Model:
    """The only thing that turns evidence and a question into a belief."""

    def __init__(self, name="jev-latest", key=None, url="https://api.typesafe.ai/v1/systemone"):
        self.name, self.key, self.url = name, key or os.environ["TYPESAFE_API_KEY"], url

    def believe(self, evidence, question: Question) -> Belief:
        body = json.dumps({"model": self.name, "state": evidence, "questions": {"q": question.wire()}}).encode()
        req = urllib.request.Request(self.url, data=body, headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        return question.belief(json.loads(urllib.request.urlopen(req).read())["answers"]["q"])


# ====================================================================== expressions
class Expr:
    """A deterministic computation. Operators build a tree; eval runs it; refs lists the nodes it reads."""

    def eval(self, ctx: dict) -> Any: raise NotImplementedError
    def refs(self) -> set: return set()

    # comparison
    def __lt__(self, o): return Compare(operator.lt, self, lift(o))
    def __le__(self, o): return Compare(operator.le, self, lift(o))
    def __gt__(self, o): return Compare(operator.gt, self, lift(o))
    def __ge__(self, o): return Compare(operator.ge, self, lift(o))
    def __eq__(self, o): return Compare(operator.eq, self, lift(o))   # type: ignore[override]
    def __ne__(self, o): return Compare(operator.ne, self, lift(o))   # type: ignore[override]
    __hash__ = object.__hash__
    # arithmetic
    def __add__(self, o): return Arithmetic(operator.add, self, lift(o))
    def __sub__(self, o): return Arithmetic(operator.sub, self, lift(o))
    def __mul__(self, o): return Arithmetic(operator.mul, self, lift(o))
    def __truediv__(self, o): return Arithmetic(operator.truediv, self, lift(o))
    def __radd__(self, o): return Arithmetic(operator.add, lift(o), self)
    def __rmul__(self, o): return Arithmetic(operator.mul, lift(o), self)
    # boolean
    def __and__(self, o): return Boolean(lambda a, b: bool(a) and bool(b), self, lift(o))
    def __or__(self, o): return Boolean(lambda a, b: bool(a) or bool(b), self, lift(o))
    def __invert__(self): return Boolean(lambda a, _: not a, self, Const(None))
    # access
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return Attr(self, name)
    def __getitem__(self, key): return Item(self, lift(key))
    def __call__(self, *args): return Call(self, [lift(a) for a in args])
    def is_none(self): return Compare(operator.is_, self, Const(None))


def lift(x) -> Expr: return x if isinstance(x, Expr) else Const(x)


@dataclass(frozen=True, eq=False)
class Const(Expr):
    value: Any
    def eval(self, ctx): return self.value


class Input(Expr):
    """The evidence the architecture was given."""
    def eval(self, ctx): return ctx["input"]


@dataclass(frozen=True, eq=False)
class Attr(Expr):
    base: Expr; name: str
    def eval(self, ctx):
        v = self.base.eval(ctx)
        return v[self.name] if isinstance(v, dict) else getattr(v, self.name)
    def refs(self): return self.base.refs()


@dataclass(frozen=True, eq=False)
class Item(Expr):
    base: Expr; key: Expr
    def eval(self, ctx): return self.base.eval(ctx)[self.key.eval(ctx)]
    def refs(self): return self.base.refs() | self.key.refs()


@dataclass(frozen=True, eq=False)
class Call(Expr):
    base: Expr; args: list
    def eval(self, ctx): return self.base.eval(ctx)(*[a.eval(ctx) for a in self.args])
    def refs(self): return self.base.refs().union(*[a.refs() for a in self.args])


@dataclass(frozen=True, eq=False)
class Compare(Expr):
    op: Callable; left: Expr; right: Expr
    def eval(self, ctx): return self.op(self.left.eval(ctx), self.right.eval(ctx))
    def refs(self): return self.left.refs() | self.right.refs()


class Arithmetic(Compare): pass
class Boolean(Compare): pass


@dataclass(frozen=True, eq=False)
class Aggregate(Expr):
    """Reduce several values to one: Sum, Mean, Min, Max, Count, Any, All, Majority."""
    fn: Callable; items: tuple
    def eval(self, ctx): return self.fn([i.eval(ctx) for i in self.items])
    def refs(self): return set().union(*[i.refs() for i in self.items])


def _majority(xs):
    xs = [x for x in xs if x is not None]
    best = max(set(xs), key=xs.count) if xs else None
    return best if best is not None and xs.count(best) > len(xs) / 2 else None

def Sum(*xs): return Aggregate(sum, tuple(map(lift, xs)))
def Mean(*xs): return Aggregate(lambda v: sum(v) / len(v), tuple(map(lift, xs)))
def Min(*xs): return Aggregate(min, tuple(map(lift, xs)))
def Max(*xs): return Aggregate(max, tuple(map(lift, xs)))
def Count(*xs): return Aggregate(lambda v: sum(1 for x in v if x), tuple(map(lift, xs)))
def Any(*xs): return Aggregate(any, tuple(map(lift, xs)))
def All(*xs): return Aggregate(all, tuple(map(lift, xs)))
def Majority(*xs): return Aggregate(_majority, tuple(map(lift, xs)))


@dataclass(frozen=True, eq=False)
class Select(Expr):
    """First case whose condition holds; otherwise the default. If-then-else, routing, abstention, veto."""
    cases: tuple; default: Expr
    def eval(self, ctx):
        for cond, value in self.cases:
            if cond.eval(ctx):
                return value.eval(ctx)
        return self.default.eval(ctx)
    def refs(self): return set().union(*[c.refs() | v.refs() for c, v in self.cases]) | self.default.refs()


def When(*cases, default=None) -> Select:
    return Select(tuple((lift(c), lift(v)) for c, v in cases), lift(default))


@dataclass(frozen=True, eq=False)
class Record(Expr):
    """Build evidence: a dict of expressions."""
    fields: dict
    def eval(self, ctx): return {k: v.eval(ctx) for k, v in self.fields.items()}
    def refs(self): return set().union(*[v.refs() for v in self.fields.values()])


def Evidence(**fields) -> Record: return Record({k: lift(v) for k, v in fields.items()})
def List(*items): return Aggregate(list, tuple(map(lift, items)))


# ====================================================================== nodes
class Node(Expr):
    """A unit of an architecture. Referring to a node in an expression reads its value."""
    when: Expr | None = None

    def eval(self, ctx): return ctx[self]
    def refs(self): return {self}
    def dependencies(self) -> set: return self.when.refs() if self.when is not None else set()
    def compute(self, ctx, model: Model): raise NotImplementedError


class Believe(Node):
    """evidence + question -> belief"""

    def __init__(self, question: Question, evidence: Expr | None = None, model: Model | str | None = None, when: Expr | None = None):
        self.question, self.evidence, self.when = question, lift(evidence) if evidence is not None else Input(), when
        self.model = Model(model) if isinstance(model, str) else model

    def dependencies(self): return super().dependencies() | self.evidence.refs()
    def compute(self, ctx, model): return (self.model or model).believe(self.evidence.eval(ctx), self.question)


class Decide(Node):
    """beliefs + values -> decision"""

    def __init__(self, rule: Expr, when: Expr | None = None):
        self.rule, self.when = lift(rule), when

    def dependencies(self): return super().dependencies() | self.rule.refs()
    def compute(self, ctx, model): return self.rule.eval(ctx)


class Use(Node):
    """An architecture as a node: its decision becomes a value here, and may be evidence elsewhere."""

    def __init__(self, architecture: "Architecture", evidence: Expr | None = None, when: Expr | None = None):
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
        return sum(1 for level in self.levels for n in level if isinstance(n, Believe)) + \
               sum(n.architecture.calls for level in self.levels for n in level if isinstance(n, Use))
