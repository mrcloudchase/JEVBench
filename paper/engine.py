"""A minimal engine for decision architectures on a typed decision model.

    evidence + questions  ->  belief      Believe(questions, evidence, *inputs, **values)
    beliefs  + values     ->  decision    Decide(rule, *beliefs, **values)
    decision              ->  evidence    a node's value is an input to any later node

Positional arguments are nodes whose values the function receives; keyword arguments are the author's
values: thresholds, labels, framings. The argument list is the wiring, so the graph is explicit, levels
are inferred, independent beliefs run concurrently, and an Architecture is callable, so it can be the
function of a node in another architecture. Question types and belief shape come from the wire format.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable

INPUT = "input"                       # the evidence the architecture was given


class Provider:
    """evidence + questions -> belief, through any endpoint that speaks the typed-decision wire format."""

    def __init__(self, model: str | None = None, api_key: str | None = None, base_url: str | None = None, **options):
        from typesafe_sdk import TypeSafeClient
        self.client = TypeSafeClient(api_key=api_key, base_url=base_url, model=model, **options)

    def believe(self, evidence, questions: dict) -> dict:
        return self.client.system_one(evidence, questions).model_dump(mode="json")["answers"]


class Node:
    """A function of the values of other nodes (positional) and the author's values (keyword)."""

    def __init__(self, fn: Callable, *inputs, when=None, **values):
        self.fn, self.inputs, self.when, self.values = fn, inputs or (INPUT,), when, values

    def dependencies(self) -> set:
        return {i for i in self.inputs if i is not INPUT} | ({self.when} if self.when is not None else set())

    def value(self, ctx: dict, provider: Provider):
        return self.fn(*[ctx[i] for i in self.inputs], **self.values)


class Believe(Node):
    """evidence + questions -> belief. `evidence` builds the evidence from its inputs and values; a Provider answers."""

    def __init__(self, questions: dict, evidence: Callable = lambda x: x, *inputs, provider=None, when=None, **values):
        super().__init__(evidence, *inputs, when=when, **values)
        self.questions = questions
        self.provider = Provider(provider) if isinstance(provider, str) else provider

    def value(self, ctx, provider):
        return (self.provider or provider).believe(super().value(ctx, provider), self.questions)


class Decide(Node):
    """beliefs + values -> decision. `rule` receives the beliefs positionally and the values by name."""


class Architecture:
    """Everything reachable from its output node. Levels are inferred; nodes in a level run concurrently."""

    def __init__(self, output: Node, provider: Provider | None = None, workers: int = 8):
        self.output, self.provider, self.workers = output, provider or Provider(), workers
        nodes, stack = set(), [output]
        while stack:
            n = stack.pop()
            if n not in nodes:
                nodes.add(n); stack.extend(n.dependencies())
        remaining, self.levels = {n: n.dependencies() for n in nodes}, []
        while remaining:
            ready = [n for n, d in remaining.items() if not d]
            if not ready:
                raise ValueError("cycle: feedback needs an explicit bound")
            self.levels.append(ready)
            for n in ready: del remaining[n]
            for d in remaining.values(): d.difference_update(ready)

    def run(self, input) -> dict:
        ctx = {INPUT: input}
        def step(n):
            return n, (n.value(ctx, self.provider) if n.when is None or ctx[n.when] else None)
        for level in self.levels:
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                for n, v in pool.map(step, level):
                    ctx[n] = v
        return ctx

    def __call__(self, input):
        return self.run(input)[self.output]

    @property
    def calls(self) -> int:
        """Upper bound on model calls per run."""
        return sum(n.fn.calls if isinstance(n.fn, Architecture) else isinstance(n, Believe) for level in self.levels for n in level)


def majority(*xs):
    xs = [x for x in xs if x is not None]
    best = max(set(xs), key=xs.count) if xs else None
    return best if best is not None and xs.count(best) > len(xs) / 2 else None
