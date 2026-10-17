"""A small, safe expression language used by policies, conditions and templates.

Expressions are a whitelisted subset of Python expression syntax evaluated against a scope
of plain data (dicts, lists, numbers, strings). Attribute access on a mapping reads a key, so
`nodes.triage.answers.dept.choice` works on the raw wire response.

Two forms are used throughout framework files:

* bare expressions, e.g. ``when: nodes.triage.answers.urgent.noul > 0.8``
* templates, e.g. ``state: "${input.ticket}"`` or ``"Ticket: ${input.ticket.subject}"``.
  A template that is exactly one ``${...}`` keeps the evaluated value's type.
"""

from __future__ import annotations

import ast
import operator
import re
import statistics
from collections.abc import Mapping
from functools import lru_cache
from typing import Any, Iterable

from jevbench.errors import ExpressionError

_TEMPLATE_RE = re.compile(r"\$\{([^{}]+)\}")
_WHOLE_TEMPLATE_RE = re.compile(r"^\s*\$\{([^{}]+)\}\s*$")

SCOPE_NAMES = ("input", "nodes", "loop")


def _argmax(mapping: Mapping[str, float]) -> Any:
    return max(mapping, key=lambda k: mapping[k]) if mapping else None


def _argmin(mapping: Mapping[str, float]) -> Any:
    return min(mapping, key=lambda k: mapping[k]) if mapping else None


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.fmean(values) if values else 0.0


def _median(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.median(values) if values else 0.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


SAFE_FUNCTIONS: dict[str, Any] = {
    "abs": abs,
    "all": all,
    "any": any,
    "argmax": _argmax,
    "argmin": _argmin,
    "bool": bool,
    "clamp": _clamp,
    "dict": dict,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "mean": _mean,
    "median": _median,
    "min": min,
    "round": round,
    "sorted": sorted,
    "str": str,
    "sum": sum,
}

_SAFE_METHODS: dict[type, frozenset[str]] = {
    str: frozenset({"lower", "upper", "strip", "startswith", "endswith", "split", "replace"}),
    dict: frozenset({"get", "keys", "values", "items"}),
    list: frozenset({"index", "count"}),
    tuple: frozenset({"index", "count"}),
}

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.Not: operator.not_, ast.USub: operator.neg, ast.UAdd: operator.pos}
_CMP_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}


@lru_cache(maxsize=4096)
def parse(expression: str) -> ast.Expression:
    """Parse and statically check an expression. Raises ExpressionError on disallowed syntax."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"invalid expression {expression!r}: {exc.msg}") from None
    _check(tree.body, expression)
    return tree


def _check(node: ast.AST, source: str) -> None:
    for child in ast.walk(node):
        if isinstance(child, (ast.Lambda, ast.Await, ast.Yield, ast.YieldFrom, ast.NamedExpr, ast.Starred, ast.FormattedValue, ast.JoinedStr)):
            raise ExpressionError(f"disallowed syntax {type(child).__name__} in {source!r}")
        if isinstance(child, ast.Attribute) and child.attr.startswith("_"):
            raise ExpressionError(f"private attribute access is not allowed in {source!r}")
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                if func.id not in SAFE_FUNCTIONS:
                    raise ExpressionError(f"unknown function {func.id!r} in {source!r}")
            elif not isinstance(func, ast.Attribute):
                raise ExpressionError(f"unsupported call target in {source!r}")
            if child.keywords:
                raise ExpressionError(f"keyword arguments are not supported in {source!r}")


class _Evaluator:
    def __init__(self, scope: Mapping[str, Any], source: str):
        self.scope = scope
        self.source = source

    def visit(self, node: ast.AST) -> Any:
        method = getattr(self, f"visit_{type(node).__name__}", None)
        if method is None:
            raise ExpressionError(f"unsupported syntax {type(node).__name__} in {self.source!r}")
        return method(node)

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.scope:
            return self.scope[node.id]
        if node.id in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[node.id]
        raise ExpressionError(f"unknown name {node.id!r} in {self.source!r}")

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        obj = self.visit(node.value)
        return self._get_attr(obj, node.attr)

    def _get_attr(self, obj: Any, name: str) -> Any:
        if isinstance(obj, Mapping):
            if name in obj:
                return obj[name]
            if name in _SAFE_METHODS[dict]:
                return getattr(obj, name)
            raise ExpressionError(f"no key {name!r} (available: {sorted(map(str, obj))[:12]}) in {self.source!r}")
        if obj is None:
            raise ExpressionError(f"cannot read {name!r} of null (a skipped node or missing input?) in {self.source!r}")
        allowed = _SAFE_METHODS.get(type(obj), frozenset())
        if name in allowed:
            return getattr(obj, name)
        raise ExpressionError(f"cannot read {name!r} of {type(obj).__name__} in {self.source!r}")

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        obj = self.visit(node.value)
        if isinstance(node.slice, ast.Slice):
            lower = self.visit(node.slice.lower) if node.slice.lower else None
            upper = self.visit(node.slice.upper) if node.slice.upper else None
            return obj[lower:upper]
        key = self.visit(node.slice)
        try:
            return obj[key]
        except (KeyError, IndexError, TypeError) as exc:
            raise ExpressionError(f"bad subscript {key!r} in {self.source!r}: {exc}") from None

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise ExpressionError(f"unsupported operator in {self.source!r}")
        try:
            return op(self.visit(node.left), self.visit(node.right))
        except (TypeError, ZeroDivisionError) as exc:
            raise ExpressionError(f"{exc} in {self.source!r}") from None

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise ExpressionError(f"unsupported unary operator in {self.source!r}")
        return op(self.visit(node.operand))

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in node.values:
                result = self.visit(value)
                if not result:
                    return result
            return result
        result = False
        for value in node.values:
            result = self.visit(value)
            if result:
                return result
        return result

    def visit_Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            try:
                if not _CMP_OPS[type(op)](left, right):
                    return False
            except TypeError as exc:
                raise ExpressionError(f"{exc} in {self.source!r}") from None
            left = right
        return True

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        return self.visit(node.body) if self.visit(node.test) else self.visit(node.orelse)

    def visit_Call(self, node: ast.Call) -> Any:
        args = [self.visit(a) for a in node.args]
        if isinstance(node.func, ast.Name):
            return SAFE_FUNCTIONS[node.func.id](*args)
        func = self.visit(node.func)
        return func(*args)

    def visit_List(self, node: ast.List) -> list:
        return [self.visit(e) for e in node.elts]

    def visit_Tuple(self, node: ast.Tuple) -> tuple:
        return tuple(self.visit(e) for e in node.elts)

    def visit_Dict(self, node: ast.Dict) -> dict:
        return {self.visit(k): self.visit(v) for k, v in zip(node.keys, node.values)}

    def visit_ListComp(self, node: ast.ListComp) -> list:
        return list(self._comprehension(node.elt, node.generators))

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> list:
        return list(self._comprehension(node.elt, node.generators))

    def _comprehension(self, elt: ast.AST, generators: list[ast.comprehension], index: int = 0):
        if index == len(generators):
            yield self.visit(elt)
            return
        gen = generators[index]
        for item in self.visit(gen.iter):
            inner = _Evaluator({**self.scope, **self._bind(gen.target, item)}, self.source)
            if all(inner.visit(cond) for cond in gen.ifs):
                yield from inner._comprehension(elt, generators, index + 1)

    def _bind(self, target: ast.AST, value: Any) -> dict[str, Any]:
        if isinstance(target, ast.Name):
            return {target.id: value}
        if isinstance(target, ast.Tuple) and all(isinstance(e, ast.Name) for e in target.elts):
            try:
                items = list(value)
            except TypeError:
                raise ExpressionError(f"cannot unpack {value!r} in {self.source!r}") from None
            if len(items) != len(target.elts):
                raise ExpressionError(f"cannot unpack {len(items)} values into {len(target.elts)} names in {self.source!r}")
            return {e.id: v for e, v in zip(target.elts, items)}
        raise ExpressionError(f"only simple loop variables are supported in {self.source!r}")


def evaluate(expression: str, scope: Mapping[str, Any]) -> Any:
    """Evaluate a bare expression against a scope."""
    tree = parse(expression)
    return _Evaluator(scope, expression).visit(tree)


def is_template(value: Any) -> bool:
    return isinstance(value, str) and _TEMPLATE_RE.search(value) is not None


def render(value: Any, scope: Mapping[str, Any]) -> Any:
    """Recursively resolve ``${expr}`` templates inside strings, lists and dicts."""
    if isinstance(value, str):
        whole = _WHOLE_TEMPLATE_RE.match(value)
        if whole:
            return evaluate(whole.group(1), scope)
        return _TEMPLATE_RE.sub(lambda m: _stringify(evaluate(m.group(1), scope)), value)
    if isinstance(value, Mapping):
        return {k: render(v, scope) for k, v in value.items()}
    if isinstance(value, list):
        return [render(v, scope) for v in value]
    return value


def _stringify(value: Any) -> str:
    if isinstance(value, (dict, list)):
        import json

        return json.dumps(value, ensure_ascii=False)
    return str(value)


def template_expressions(value: Any) -> list[str]:
    """Collect every ``${expr}`` expression embedded in a value."""
    found: list[str] = []
    if isinstance(value, str):
        found.extend(m.group(1) for m in _TEMPLATE_RE.finditer(value))
    elif isinstance(value, Mapping):
        for v in value.values():
            found.extend(template_expressions(v))
    elif isinstance(value, list):
        for v in value:
            found.extend(template_expressions(v))
    return found


def node_references(expression: str) -> tuple[set[str], bool]:
    """Return (static node ids referenced via ``nodes.<id>``/``nodes['id']``, has_dynamic_reference)."""
    tree = parse(expression)
    static: set[str] = set()
    dynamic = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "nodes":
            static.add(node.attr)
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "nodes":
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                static.add(node.slice.value)
            else:
                dynamic = True
        elif isinstance(node, ast.Name) and node.id == "nodes":
            # A bare `nodes` passed somewhere (e.g. nodes.values()) is a dynamic reference.
            parent_is_access = False
            for other in ast.walk(tree):
                if isinstance(other, (ast.Attribute, ast.Subscript)) and other.value is node:
                    parent_is_access = True
                    break
            if not parent_is_access:
                dynamic = True
    return static, dynamic
