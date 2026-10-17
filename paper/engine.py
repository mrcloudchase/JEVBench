"""A minimal engine for decision architectures on a typed decision model.

    evidence + questions  ->  belief      (Believe: one call to a Provider; the belief is the API's answers, untouched)
    beliefs  + values     ->  decision    (Decide: operations over beliefs)
    decision              ->  evidence    (any node's value may feed another node)

A decision is the atomic component: a belief and the operations that turn it into a decision.
The question types and the shape of a belief come from the wire format, not from here; a Provider is any
endpoint that speaks it, selected by base_url, api_key and model.
An Architecture is whatever its output node references: levels are inferred, independent beliefs
run concurrently, and an Architecture can be a node of another (Use).
"""

from __future__ import annotations

import operator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable


# ====================================================================== provider
class Provider:
    """evidence + questions -> belief, through any endpoint that speaks the typed-decision wire format.

    Uses the official typesafe-sdk; base_url, api_key and model select the endpoint. Defaults come from
    TYPESAFE_BASE_URL, TYPESAFE_API_KEY and TYPESAFE_DEFAULT_MODEL."""

    def __init__(self, model: str | None = None, api_key: str | None = None, base_url: str | None = None, **options):
        from typesafe_sdk import TypeSafeClient
        self.client = TypeSafeClient(api_key=api_key, base_url=base_url, model=model, **options)

    def believe(self, evidence, questions: dict) -> dict:
        return self.client.system_one(evidence, questions).model_dump(mode="json")["answers"]


# ====================================================================== operations
class Expr:
    """An operation over beliefs and values. Python's operators build the tree; eval runs it; refs lists the nodes read."""

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
    def __getattr__(self, name):                                  # belief.q.choice, belief.q.confidence, ...
        if name.startswith("_"):
            raise AttributeError(name)
        return Op(lambda v, n: v[n] if isinstance(v, dict) else getattr(v, n), self, name)
    def __getitem__(self, key): return Op(operator.getitem, self, key)


def lift(x) -> Expr: return x if isinstance(x, Expr) else Const(x)


class Const(Expr):
    def __init__(self, value): self.value = value
    def eval(self, ctx): return self.value


class Input(Expr):
    """The evidence the architecture was given."""
    def eval(self, ctx): return ctx["input"]


class Op(Expr):
    """One binary operation: comparison, arithmetic, boolean, or access."""
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
    """Shape evidence for the next belief from the input and earlier nodes."""
    def __init__(self, **fields): self.fields = {k: lift(v) for k, v in fields.items()}
    def eval(self, ctx): return {k: v.eval(ctx) for k, v in self.fields.items()}
    def refs(self): return set().union(*[v.refs() for v in self.fields.values()])


def majority(xs):
    xs = [x for x in xs if x is not None]
    best = max(set(xs), key=xs.count) if xs else None
    return best if best is not None and xs.count(best) > len(xs) / 2 else None


# ====================================================================== nodes
class Node(Expr):
    """A unit of an architecture. Referring to a node in an operation reads its value."""
    when: Expr | None = None

    def eval(self, ctx): return ctx[self]
    def refs(self): return {self}
    def dependencies(self) -> set: return self.when.refs() if self.when is not None else set()
    def compute(self, ctx, provider): raise NotImplementedError


class Believe(Node):
    """evidence + questions -> belief"""
    def __init__(self, questions: dict, evidence=None, provider=None, when=None):
        self.questions, self.evidence, self.when = questions, lift(evidence) if evidence is not None else Input(), when
        self.provider = Provider(provider) if isinstance(provider, str) else provider   # a model name selects a model at the default endpoint
    def dependencies(self): return super().dependencies() | self.evidence.refs()
    def compute(self, ctx, provider): return (self.provider or provider).believe(self.evidence.eval(ctx), self.questions)


class Decide(Node):
    """beliefs + values -> decision"""
    def __init__(self, rule, when=None): self.rule, self.when = lift(rule), when
    def dependencies(self): return super().dependencies() | self.rule.refs()
    def compute(self, ctx, provider): return self.rule.eval(ctx)


class Use(Node):
    """An architecture as a node: its decision is a value here, and may be evidence elsewhere."""
    def __init__(self, architecture, evidence=None, when=None):
        self.architecture, self.evidence, self.when = architecture, lift(evidence) if evidence is not None else Input(), when
    def dependencies(self): return super().dependencies() | self.evidence.refs()
    def compute(self, ctx, provider): return self.architecture(self.evidence.eval(ctx))


# ====================================================================== architecture
class Architecture:
    """Everything reachable from its output node. Levels are inferred; beliefs in a level run concurrently."""

    def __init__(self, output: Node, provider: Provider | None = None, workers: int = 8):
        self.output, self.provider, self.workers = output, provider or Provider(), workers
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
            return n, (n.compute(ctx, self.provider) if n.when is None or n.when.eval(ctx) else None)
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
