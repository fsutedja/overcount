"""Turns a problem template into concrete, precomputed instances ("New numbers")."""

import itertools
import random
from dataclasses import dataclass

import sympy as sp

from .expr import ExprError, StoredValue, evaluate, parse, parse_constraint, stored_value, to_sympy
from .schema import IntRange, Problem

#: Instances shipped per problem. The default instance is always first.
MAX_INSTANCES = 100
#: Above this many raw combinations, sample randomly instead of enumerating.
ENUMERATION_LIMIT = 20_000


@dataclass(frozen=True)
class Instance:
    key: str
    vars: dict[str, str]
    values: dict[str, StoredValue]

    def as_json(self) -> dict[str, object]:
        return {"key": self.key, "vars": self.vars, "values": self.values}


class InstanceError(ValueError):
    pass


def _choices(problem: Problem) -> dict[str, list[sp.Expr]]:
    choices: dict[str, list[sp.Expr]] = {}
    for name, variable in problem.variables.items():
        if isinstance(variable, IntRange):
            choices[name] = [sp.Integer(v) for v in range(variable.min, variable.max + 1)]
        else:
            choices[name] = [evaluate(parse(v), {}) for v in variable.values]
    return choices


def _default(problem: Problem) -> dict[str, sp.Expr]:
    return {
        name: sp.Integer(v.default) if isinstance(v, IntRange) else evaluate(parse(v.default), {})
        for name, v in problem.variables.items()
    }


def _format(value: sp.Expr) -> str:
    rational = sp.Rational(value)
    return str(rational.p) if rational.q == 1 else f"{rational.p}/{rational.q}"


def build_instance(problem: Problem, assignment: dict[str, sp.Expr]) -> Instance | None:
    """Computes every value an instance needs, or returns None if the assignment isn't valid."""
    constraints = [parse_constraint(c) for c in problem.constraints]
    try:
        if not all(c.holds(assignment) for c in constraints):
            return None
        answer = evaluate(parse(problem.answer.expr), assignment)
        skeleton = problem.answer.skeleton
        indices = skeleton.slot_indices
        # A slot inside a Σ body may use the index (its value is an expression in k); every other
        # slot is a number.
        slots = {
            slot: to_sympy(parse(spec.answer), assignment)
            if slot in indices
            else evaluate(parse(spec.answer), assignment)
            for slot, spec in skeleton.slots.items()
        }
        filled = evaluate(parse(skeleton.source), assignment | slots)
    except ExprError:
        return None
    if not _plausible(problem, answer):
        return None
    if sp.simplify(filled - answer) != 0:
        raise InstanceError(
            f"the skeleton filled with its slot answers gives {filled}, not the answer {answer} "
            f"(for {', '.join(f'{k}={v}' for k, v in assignment.items())})"
        )

    vars_ = {name: _format(value) for name, value in assignment.items()}
    values = {"answer": stored_value(answer)} | {
        f"slot.{slot}": _slot_value(v, indices.get(slot)) for slot, v in slots.items()
    }
    key = ",".join(f"{name}={vars_[name]}" for name in problem.variables)
    return Instance(key, vars_, values)


def _slot_value(value: sp.Expr, index: str | None) -> StoredValue:
    """A number, or for a slot inside a Σ body, the expression in its index, e.g. "5 - k"."""
    if index is not None and value.free_symbols:
        return {"type": "indexed", "latex": sp.latex(value), "index": index}
    return stored_value(value)


def _plausible(problem: Problem, answer: sp.Expr) -> bool:
    match problem.answer.type:
        case "count":
            return bool(answer.is_integer and answer > 0)
        case "probability":
            return bool(0 <= answer <= 1)
        case _:
            return bool(answer.is_real)


def build_instances(problem: Problem, limit: int = MAX_INSTANCES) -> list[Instance]:
    """The default instance first, then up to `limit - 1` more valid ones, in a fixed order."""
    default = build_instance(problem, _default(problem))
    if default is None:
        raise InstanceError(f"{problem.id}: the default variable values don't give a valid instance")

    choices = _choices(problem)
    names = list(choices)
    total = 1
    for options in choices.values():
        total *= len(options)
    rng = random.Random(problem.id)
    if total <= ENUMERATION_LIMIT:
        candidates = [dict(zip(names, combo, strict=True)) for combo in itertools.product(*choices.values())]
        rng.shuffle(candidates)
    else:
        candidates = [{n: rng.choice(choices[n]) for n in names} for _ in range(ENUMERATION_LIMIT)]

    instances = [default]
    seen = {default.key}
    for assignment in candidates:
        if len(instances) >= limit:
            break
        instance = build_instance(problem, assignment)
        if instance is not None and instance.key not in seen:
            seen.add(instance.key)
            instances.append(instance)
    return instances
