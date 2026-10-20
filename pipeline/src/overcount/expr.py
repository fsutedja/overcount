"""The storage expression grammar: parse once, then evaluate with sympy or print as LaTeX.

Grammar (PLAN.md §1): integers, variables (one letter, optionally a digit), `+ - * / ^`, unary
minus, parentheses, `C(n, k)`, `P(n, k)`, postfix `n!`, the constant `e`, and `[slot]` markers
in Help skeletons. Expressions are parsed with Python's `ast` and checked against a whitelist, so
content is never `eval`'d. That matters because some of it is written by an LLM.
"""

import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

import sympy as sp

SLOT_PREFIX = "slot__"
_SLOT = re.compile(r"\[(\w+)\]")
_FUNCTIONS = {"C", "P", "fact"}


class ExprError(ValueError):
    """An expression that doesn't fit the grammar."""


@dataclass(frozen=True)
class Expr:
    source: str
    tree: ast.expr

    @property
    def variables(self) -> set[str]:
        return {n.id for n in ast.walk(self.tree) if isinstance(n, ast.Name) and _is_variable(n.id)}

    @property
    def slots(self) -> set[str]:
        return {
            n.id.removeprefix(SLOT_PREFIX)
            for n in ast.walk(self.tree)
            if isinstance(n, ast.Name) and _is_slot(n.id)
        }


def _is_slot(name: str) -> bool:
    return name.startswith(SLOT_PREFIX)


def _is_variable(name: str) -> bool:
    return not _is_slot(name) and name not in _FUNCTIONS and name != "e"


def _rewrite_factorials(text: str) -> str:
    """Turns postfix `x!` and `(…)!` into `fact(…)` so Python's parser can read it."""
    while "!" in text:
        end = text.index("!")
        start = end - 1
        if start < 0:
            raise ExprError("'!' needs something before it")
        if text[start] == ")":
            depth = 0
            while start >= 0:
                depth += {")": 1, "(": -1}.get(text[start], 0)
                if depth == 0:
                    break
                start -= 1
            if start < 0:
                raise ExprError("unbalanced parentheses before '!'")
            while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
                start -= 1
        else:
            while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
                start -= 1
        text = f"{text[:start]}fact({text[start:end]}){text[end + 1 :]}"
    return text


def _check(node: ast.AST) -> None:
    match node:
        case ast.BinOp(op=ast.Add() | ast.Sub() | ast.Mult() | ast.Div() | ast.Pow()):
            _check(node.left)
            _check(node.right)
        case ast.UnaryOp(op=ast.USub()):
            _check(node.operand)
        case ast.Call(func=ast.Name(id=name), args=args, keywords=[]) if name in _FUNCTIONS:
            expected = 1 if name == "fact" else 2
            if len(args) != expected:
                raise ExprError(f"{name if name != 'fact' else '!'} takes {expected} argument(s)")
            for arg in args:
                _check(arg)
        case ast.Name(id=name) if name not in _FUNCTIONS:
            pass
        case ast.Constant(value=int() as value) if not isinstance(value, bool):
            pass
        case ast.Constant(value=float()):
            raise ExprError("write exact numbers, e.g. 1/6 instead of 0.1667")
        case _:
            raise ExprError(f"unsupported syntax: {ast.dump(node)[:60]}")


def parse(source: str) -> Expr:
    text = _SLOT.sub(lambda m: SLOT_PREFIX + m[1], source).replace("^", "**")
    try:
        tree = ast.parse(_rewrite_factorials(text), mode="eval").body
    except SyntaxError as error:
        raise ExprError(f"can't parse {source!r}: {error.msg}") from error
    _check(tree)
    return Expr(source, tree)


_COMPARISONS = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!="}


@dataclass(frozen=True)
class Constraint:
    """A chained comparison between expressions, e.g. "j < J" or "2 <= k <= n"."""

    source: str
    terms: tuple[Expr, ...]
    operators: tuple[str, ...]

    @property
    def variables(self) -> set[str]:
        return set().union(*(term.variables for term in self.terms))

    def holds(self, values: Mapping[str, sp.Expr]) -> bool:
        numbers = [evaluate(term, values) for term in self.terms]
        checks = {"<": sp.Lt, "<=": sp.Le, ">": sp.Gt, ">=": sp.Ge, "==": sp.Eq, "!=": sp.Ne}
        return all(
            bool(checks[op](a, b)) for op, a, b in zip(self.operators, numbers, numbers[1:], strict=False)
        )


def parse_constraint(source: str) -> Constraint:
    try:
        tree = ast.parse(_rewrite_factorials(source.replace("^", "**")), mode="eval").body
    except SyntaxError as error:
        raise ExprError(f"can't parse constraint {source!r}: {error.msg}") from error
    if not isinstance(tree, ast.Compare):
        raise ExprError(f"constraint {source!r} must be a comparison such as 'j < J'")
    nodes = [tree.left, *tree.comparators]
    for node in nodes:
        _check(node)
    operators = []
    for op in tree.ops:
        if type(op) not in _COMPARISONS:
            raise ExprError(f"unsupported comparison in {source!r}")
        operators.append(_COMPARISONS[type(op)])
    return Constraint(source, tuple(Expr(ast.unparse(n), n) for n in nodes), tuple(operators))


# --- sympy -----------------------------------------------------------------------------------------


def to_sympy(expr: Expr, values: Mapping[str, sp.Expr]) -> sp.Expr:
    """Builds the sympy expression; variables and slots missing from `values` stay symbolic."""

    def build(node: ast.expr) -> sp.Expr:
        match node:
            case ast.BinOp(left=left, op=op, right=right):
                a, b = build(left), build(right)
                match op:
                    case ast.Add():
                        return a + b
                    case ast.Sub():
                        return a - b
                    case ast.Mult():
                        return a * b
                    case ast.Div():
                        return a / b
                    case _:
                        return a**b
            case ast.UnaryOp(operand=operand):
                return -build(operand)
            case ast.Call(func=ast.Name(id="C"), args=[n, k]):
                return sp.binomial(build(n), build(k))
            case ast.Call(func=ast.Name(id="P"), args=[n, k]):
                return sp.ff(build(n), build(k))
            case ast.Call(func=ast.Name(id="fact"), args=[n]):
                return sp.factorial(build(n))
            case ast.Name(id="e"):
                return sp.E
            case ast.Name(id=name):
                key = name.removeprefix(SLOT_PREFIX)
                return values[key] if key in values else sp.Symbol(name)
            case ast.Constant(value=int() as value):
                return sp.Integer(value)
        raise ExprError(f"unexpected node {ast.dump(node)[:60]}")

    return build(expr.tree)


def evaluate(expr: Expr, values: Mapping[str, sp.Expr]) -> sp.Expr:
    """Evaluates to an exact sympy number; raises if anything is left symbolic or undefined."""
    missing = (expr.variables | expr.slots) - set(values)
    if missing:
        raise ExprError(f"{expr.source!r} needs values for {sorted(missing)}")
    result = to_sympy(expr, values).doit()
    if result.has(sp.zoo, sp.oo, sp.nan) or not result.is_number:
        raise ExprError(f"{expr.source!r} is undefined for {dict(values)}")
    return result


StoredValue = dict[str, str | float]


def stored_value(value: sp.Expr) -> StoredValue:
    """An exact rational as "p" or "p/q"; anything else (e.g. involving e) as a 17-digit float."""
    if value.is_Rational:
        rational = sp.Rational(value)
        exact = str(rational.p) if rational.q == 1 else f"{rational.p}/{rational.q}"
        return {"type": "rational", "exact": exact}
    if value.is_real is False:
        raise ExprError(f"{value} is not a real number")
    return {"type": "real", "approx": float(sp.N(value, 17))}


# --- LaTeX -----------------------------------------------------------------------------------------

_PRECEDENCE = {ast.Add: 1, ast.Sub: 1, ast.Mult: 2, ast.Div: 2}
_ATOM = 9


def _precedence(node: ast.expr) -> int:
    match node:
        case ast.BinOp(op=ast.Pow()):
            return 4
        case ast.BinOp(op=op):
            return _PRECEDENCE[type(op)]
        case ast.UnaryOp():
            return 3
        case ast.Constant(value=int() as value) if value < 0:
            return 3
    return _ATOM


def to_latex(expr: Expr, variables: Literal["placeholders", "names"] = "placeholders") -> str:
    """Prints LaTeX that follows the author's structure. Variables become ` {{J}} ` placeholders
    (filled in by the web app) and slots become `[a]` markers."""

    def wrap(node: ast.expr, minimum: int) -> str:
        text = emit(node)
        return f"\\left({text}\\right)" if _precedence(node) < minimum else text

    def emit(node: ast.expr) -> str:
        match node:
            case ast.BinOp(left=left, op=ast.Add(), right=right):
                return f"{wrap(left, 1)} + {wrap(right, 1)}"
            case ast.BinOp(left=left, op=ast.Sub(), right=right):
                return f"{wrap(left, 1)} - {wrap(right, 2)}"
            case ast.BinOp(left=left, op=ast.Mult(), right=right):
                return f"{wrap(left, 2)} \\times {wrap(right, 2)}"
            case ast.BinOp(left=left, op=ast.Div(), right=right):
                return f"\\frac{{{emit(left)}}}{{{emit(right)}}}"
            case ast.BinOp(left=left, op=ast.Pow(), right=right):
                return f"{wrap(left, _ATOM)}^{{{emit(right)}}}"
            case ast.UnaryOp(operand=operand):
                return f"-{wrap(operand, 3)}"
            case ast.Call(func=ast.Name(id="C"), args=[n, k]):
                return f"\\binom{{{emit(n)}}}{{{emit(k)}}}"
            case ast.Call(func=ast.Name(id="P"), args=[n, k]):
                return f"\\operatorname{{P}}\\left({emit(n)}, {emit(k)}\\right)"
            case ast.Call(func=ast.Name(id="fact"), args=[n]):
                return f"{wrap(n, _ATOM)}!"
            case ast.Name(id="e"):
                return "e"
            case ast.Name(id=name) if _is_slot(name):
                return f"[{name.removeprefix(SLOT_PREFIX)}]"
            case ast.Name(id=name):
                return f" {{{{{name}}}}} " if variables == "placeholders" else name
            case ast.Constant(value=value):
                return str(value)
        raise ExprError(f"unexpected node {ast.dump(node)[:60]}")

    return re.sub(r"\s+", " ", emit(expr.tree)).strip()


def to_group_latex(expr: Expr) -> str:
    """LaTeX for a Help skeleton group. Groups are joined with × or ÷, so a sum or difference
    keeps its brackets: "([a]+[b])" must stay (7 + 5), never become 7 + 5 × 4."""
    latex = to_latex(expr)
    return f"\\left({latex}\\right)" if _precedence(expr.tree) < 2 else latex


def display_text(source: str) -> str:
    """Plain-text form for the Help skeleton, e.g. "C([a],[b])" → "C([a], [b])"."""
    text = re.sub(r"\s*,\s*", ", ", source.strip())
    return re.sub(r"\s*\*\s*", " × ", text)
