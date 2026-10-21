"""The small-case check shown at the end of Help ("for n = 3: 6 − 6 + 3 − 1 = 2: BCA, CAB").

It is computed from the problem itself, never written by hand or by the LLM: the smallest
number set, the terms of the skeleton's Σ (when the skeleton is one Σ), and the outcomes that
count, listed by the checker when there are only a few.
"""

import ast
import re
from pathlib import Path
from typing import Any

import sympy as sp

from .examples import kwargs
from .expr import evaluate, parse, to_group_latex, to_sympy
from .instances import Instance, assignment_of, slot_values
from .schema import Problem, SkeletonGroup
from .verify.sandbox import Call, run_list
from .visual import outcome_text

#: List the counting outcomes only when there are at most this many.
MAX_LISTED = 8
MAX_TERMS = 12


def _size(instance: Instance) -> tuple[float, str]:
    return (sum(float(sp.Rational(v)) for v in instance.vars.values()), instance.key)


def _sum_terms(problem: Problem, instance: Instance) -> list[sp.Expr] | None:
    """The terms of the skeleton's Σ, filled in, when the whole skeleton is a single Σ."""
    skeleton = parse(problem.answer.skeleton.source)
    if not (isinstance(skeleton.tree, ast.Call) and isinstance(skeleton.tree.func, ast.Name)):
        return None
    if skeleton.tree.func.id != "Sum":
        return None
    assignment = assignment_of(instance)
    total = to_sympy(skeleton, assignment | slot_values(problem, assignment))
    if not isinstance(total, sp.Sum):
        return None
    (index, low, high), body = total.limits[0], total.function
    if high - low + 1 > MAX_TERMS:
        return None
    return [body.subs(index, k).doit() for k in range(int(low), int(high) + 1)]


_OP_LATEX = {"*": "\\times", "+": "+", "-": "-", "/": "\\div"}


def _worked(problem: Problem, instance: Instance) -> str:
    """The skeleton worked out for these numbers, as LaTeX: each group's value joined by its
    operators, e.g. "216 - 125", or a single Σ's terms, e.g. "6 - 6 + 3 - 1"."""
    terms = _sum_terms(problem, instance)
    if terms is not None:
        text = _exact(terms[0])
        for term in terms[1:]:
            text += f" - {_exact(-term)}" if term < 0 else f" + {_exact(term)}"
        return text
    assignment = assignment_of(instance)
    values = assignment | slot_values(problem, assignment)
    pieces = []
    for part in problem.answer.skeleton.parts:
        if isinstance(part, SkeletonGroup):
            pieces.append(_exact(evaluate(parse(part.expr), values)))
        else:
            pieces.append(_OP_LATEX[part.op])
    return " ".join(pieces)


def _filled(problem: Problem, instance: Instance) -> str:
    """The skeleton as LaTeX with this number set's slot values in the blanks."""
    assignment = assignment_of(instance)
    slots = slot_values(problem, assignment)

    def blank(match: re.Match[str]) -> str:
        value = slots[match[1]]
        return "{" + (_exact(value) if not value.free_symbols else sp.latex(value)) + "}"

    pieces = [
        re.sub(r"\[(\w+)\]", blank, to_group_latex(parse(part.expr)))
        if isinstance(part, SkeletonGroup)
        else _OP_LATEX[part.op]
        for part in problem.answer.skeleton.parts
    ]
    return " ".join(pieces)


def _exact(value: sp.Expr) -> str:
    rational = sp.Rational(value)
    return str(rational.p) if rational.q == 1 else f"{rational.p}/{rational.q}"


def help_check(problem: Problem, instances: list[Instance], checker: Path) -> dict[str, Any]:
    """The check for the smallest number set; raises if the Σ terms don't add up to the answer."""
    small = min(instances, key=_size)
    check: dict[str, Any] = {"key": small.key, "vars": small.vars, "answer": small.values["answer"]}
    terms = _sum_terms(problem, small)
    if terms is not None and small.values["answer"]["type"] == "rational":
        answer = sp.Rational(str(small.values["answer"]["exact"]))
        if sum(terms) != answer:
            raise ValueError(f"{problem.id}: the Σ terms add up to {sum(terms)}, not {answer}")
    check["filled"] = _filled(problem, small)
    check["worked"] = _worked(problem, small)
    fns = problem.checker
    value = small.values["answer"]
    if (
        fns.outcomes
        and problem.answer.type == "count"
        and value["type"] == "rational"
        and int(str(value["exact"])) <= MAX_LISTED
    ):
        found = run_list(checker, fns.outcomes, fns.counts, Call(kwargs(small)), MAX_LISTED)
        if len(found) <= MAX_LISTED:
            check["outcomes"] = [outcome_text(problem.visual.type, list(o)) for o in found]
    return check
