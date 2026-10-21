"""The storage expression grammar: parse once, then evaluate with sympy or print as LaTeX.

Grammar (PLAN.md §1): integers, variables (one letter, optionally a digit), `+ - * / ^`, unary
minus, parentheses, `C(n, k)`, `P(n, k)`, postfix `n!`, the constant `e`, sums
`Sum(body, k, lo, hi)` (Σ from k = lo to hi, with k bound inside the body), and `[slot]` markers
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
_FUNCTIONS = {"C", "P", "fact", "Sum"}
#: Largest number of terms a Σ may have, so content can't ask for an enormous sum.
MAX_SUM_TERMS = 1001


class ExprError(ValueError):
    """An expression that doesn't fit the grammar."""


@dataclass(frozen=True)
class Expr:
    source: str
    tree: ast.expr

    @property
    def variables(self) -> set[str]:
        """Free variable names; a Σ's index is bound inside its body, so it isn't one."""
        return _free_names(self.tree, frozenset())

    @property
    def sum_indices(self) -> set[str]:
        return {
            index
            for n in ast.walk(self.tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "Sum"
            and len(n.args) == 4
            and isinstance(index_node := n.args[1], ast.Name)
            for index in [index_node.id]
        }

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


def _free_names(node: ast.AST, bound: frozenset[str]) -> set[str]:
    match node:
        case ast.Call(func=ast.Name(id="Sum"), args=[body, ast.Name(id=index), lo, hi]):
            return _free_names(body, bound | {index}) | _free_names(lo, bound) | _free_names(hi, bound)
        case ast.Name(id=name):
            return {name} if _is_variable(name) and name not in bound else set()
    return set().union(*(_free_names(child, bound) for child in ast.iter_child_nodes(node)))


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
        case ast.Call(func=ast.Name(id="Sum"), args=args, keywords=[]):
            match args:
                case [body, ast.Name(id=index), lo, hi] if re.fullmatch(r"[A-Za-z]", index):
                    for part in (body, lo, hi):
                        _check(part)
                case _:
                    raise ExprError("Sum takes (body, index letter, lower bound, upper bound)")
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


def slot_indices(expr: Expr) -> dict[str, str]:
    """Slots inside a Σ body → that Σ's index letter. Such a slot's answer may use the index
    (e.g. `n-k`), so the learner fills in an expression rather than a number."""
    found: dict[str, str] = {}

    def visit(node: ast.AST, index: str | None) -> None:
        match node:
            case ast.Call(func=ast.Name(id="Sum"), args=[body, ast.Name(id=name), lo, hi]):
                visit(lo, index)
                visit(hi, index)
                visit(body, name)
                return
            case ast.Name(id=slot) if _is_slot(slot) and index is not None:
                found[slot.removeprefix(SLOT_PREFIX)] = index
        for child in ast.iter_child_nodes(node):
            visit(child, index)

    visit(expr.tree, None)
    return found


def unblanked_numbers(expr: Expr) -> list[str]:
    """Numbers in a Help-skeleton group that the learner can't fill in (empty when every number is
    a [slot]). Only 1 (as in (−1)^k or 1/k!) and a Σ's own index may appear as-is."""
    problems: list[str] = []

    def is_slot(node: ast.expr) -> bool:
        return isinstance(node, ast.Name) and _is_slot(node.id)

    def visit(node: ast.expr, bound: frozenset[str]) -> None:
        match node:
            case ast.Call(func=ast.Name(id="Sum"), args=[body, ast.Name(id=index), lo, hi]):
                for side, bound_node in (("lower", lo), ("upper", hi)):
                    if not is_slot(bound_node):
                        problems.append(f"the Σ {side} bound must be a [slot]")
                visit(body, bound | {index})
                return
            case ast.Call(func=ast.Name(id="fact"), args=[arg]):
                if not (is_slot(arg) or (isinstance(arg, ast.Name) and arg.id in bound)):
                    problems.append("a factorial's base must be a [slot] (or the Σ index)")
                    return
            case ast.Constant(value=int() as value) if value != 1:
                problems.append(f"the number {value} must be a [slot]")
            case ast.Name(id=name) if not _is_slot(name) and name not in bound and name not in _FUNCTIONS:
                problems.append(f"{name} must be a [slot] (the learner fills in its number)")
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                visit(child, bound)

    visit(expr.tree, frozenset())
    return problems


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

    def build(node: ast.expr, bound: frozenset[str] = frozenset()) -> sp.Expr:
        match node:
            case ast.Call(func=ast.Name(id="Sum"), args=[body, ast.Name(id=index), lo, hi]):
                low, high = build(lo, bound), build(hi, bound)
                if low.is_number and high.is_number:
                    if not (low.is_integer and high.is_integer):
                        raise ExprError(f"Σ bounds must be whole numbers, got {low} and {high}")
                    if high - low + 1 > MAX_SUM_TERMS:
                        raise ExprError(f"Σ has too many terms ({high - low + 1})")
                return sp.Sum(build(body, bound | {index}), (sp.Symbol(index), low, high))
            case ast.Name(id=name) if name in bound:
                return sp.Symbol(name)
            case ast.BinOp(left=left, op=op, right=right):
                a, b = build(left, bound), build(right, bound)
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
                return -build(operand, bound)
            case ast.Call(func=ast.Name(id="C"), args=[n, k]):
                return sp.binomial(build(n, bound), build(k, bound))
            case ast.Call(func=ast.Name(id="P"), args=[n, k]):
                return sp.ff(build(n, bound), build(k, bound))
            case ast.Call(func=ast.Name(id="fact"), args=[n]):
                return sp.factorial(build(n, bound))
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
        case ast.Call(func=ast.Name(id="Sum")):
            # A Σ swallows everything to its right, so treat it like a sum when deciding brackets.
            return 1
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

    bound: set[str] = set()

    def wrap(node: ast.expr, minimum: int) -> str:
        text = emit(node)
        return f"\\left({text}\\right)" if _precedence(node) < minimum else text

    def emit(node: ast.expr) -> str:
        match node:
            case ast.Call(func=ast.Name(id="Sum"), args=[body, ast.Name(id=index), lo, hi]):
                limits = f"\\sum_{{{index}={emit(lo)}}}^{{{emit(hi)}}}"
                bound.add(index)
                text = f"{limits} {wrap(body, 2)}"
                bound.discard(index)
                return text
            case ast.Name(id=name) if name in bound:
                return name
            case ast.BinOp(left=left, op=ast.Add(), right=right):
                return f"{wrap(left, 1)} + {wrap(right, 1)}"
            case ast.BinOp(left=left, op=ast.Sub(), right=right):
                return f"{wrap(left, 1)} - {wrap(right, 2)}"
            case ast.BinOp(left=left, op=ast.Mult(), right=right):
                return f"{wrap(left, 2)} \\times {wrap(right, 2)}"
            case ast.BinOp(left=left, op=ast.Div(), right=right):
                return f"\\frac{{{emit(left)}}}{{{emit(right)}}}"
            case ast.BinOp(left=left, op=ast.Pow(), right=right):
                # (a!)^g keeps its brackets: a!^g would read as a!·…
                is_factorial = (
                    isinstance(left, ast.Call) and isinstance(left.func, ast.Name) and left.func.id == "fact"
                )
                base = f"\\left({emit(left)}\\right)" if is_factorial else wrap(left, _ATOM)
                return f"{base}^{{{emit(right)}}}"
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


def to_plain(expr: Expr) -> str:
    """Plain-text form with the same structure as `to_latex`, e.g. "Σ(k=0..[n]) (−1)^k / k!"."""

    def wrap(node: ast.expr, minimum: int) -> str:
        text = emit(node)
        return f"({text})" if _precedence(node) < minimum else text

    def emit(node: ast.expr) -> str:
        match node:
            case ast.Call(func=ast.Name(id="Sum"), args=[body, ast.Name(id=index), lo, hi]):
                return f"Σ({index}={emit(lo)}..{emit(hi)}) {wrap(body, 2)}"
            case ast.BinOp(left=left, op=ast.Add(), right=right):
                return f"{wrap(left, 1)} + {wrap(right, 1)}"
            case ast.BinOp(left=left, op=ast.Sub(), right=right):
                return f"{wrap(left, 1)} − {wrap(right, 2)}"
            case ast.BinOp(left=left, op=ast.Mult(), right=right):
                return f"{wrap(left, 2)} × {wrap(right, 2)}"
            case ast.BinOp(left=left, op=ast.Div(), right=right):
                return f"{wrap(left, 2)} / {wrap(right, 3)}"
            case ast.BinOp(left=left, op=ast.Pow(), right=right):
                return f"{wrap(left, _ATOM)}^{wrap(right, _ATOM)}"
            case ast.UnaryOp(operand=operand):
                return f"−{wrap(operand, 3)}"
            case ast.Call(func=ast.Name(id="fact"), args=[n]):
                return f"{wrap(n, _ATOM)}!"
            case ast.Call(func=ast.Name(id=name), args=args):
                return f"{name}({', '.join(emit(a) for a in args)})"
            case ast.Name(id=name) if _is_slot(name):
                return f"[{name.removeprefix(SLOT_PREFIX)}]"
            case ast.Name(id=name):
                return name
            case ast.Constant(value=value):
                return str(value)
        raise ExprError(f"unexpected node {ast.dump(node)[:60]}")

    return emit(expr.tree)


def display_text(source: str) -> str:
    """Plain-text form of a Help skeleton group. Sums and differences keep their brackets, like
    `to_group_latex`: "([a]+[b])" → "([a] + [b])", "C([a],[b])" → "C([a], [b])"."""
    expr = parse(source)
    text = to_plain(expr)
    return f"({text})" if _precedence(expr.tree) < 2 else text
