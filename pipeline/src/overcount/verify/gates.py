"""The MVP verification gates (PLAN.md §3). A family passes only if every problem passes all of them.

1. schema      the family validates and every problem yields enough valid instances
2. checker     the brute-force checker agrees with the answer on the default instance, the
               range corners, and random instances
3. simulation  Monte Carlo estimates land within a 99.9% interval of the exact answer
"""

import itertools
import math
import random
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import sympy as sp
from pydantic import ValidationError

from ..expr import evaluate, parse
from ..instances import Instance, InstanceError, build_instance, build_instances
from ..schema import Family, IntRange, Problem
from .sandbox import Call, Result, SandboxError, UnsafeCode, run_checker

#: Fewer instances than this and "New numbers" has too little to offer.
MIN_INSTANCES = 5
RANDOM_CHECKS = 10
MAX_CORNERS = 16
SIMULATION_TRIALS = 200_000
#: Two-sided 99.9% normal quantile.
Z_999 = 3.29


@dataclass(frozen=True)
class Failure:
    gate: str
    problem_id: str
    message: str
    instance_key: str | None = None
    detail: str | None = None


@dataclass
class FamilyReport:
    family_id: str
    folder: Path
    failures: list[Failure] = field(default_factory=list)
    #: problem id → number of instances each gate checked
    checked: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.failures


def _kwargs(instance: Instance) -> dict[str, int | str]:
    return {name: int(value) if "/" not in value else value for name, value in instance.vars.items()}


def _exact(stored: dict[str, str | float]) -> Fraction | float:
    return Fraction(str(stored["exact"])) if stored["type"] == "rational" else float(stored["approx"])


def _same(result: Result, expected: Fraction | float) -> bool:
    if isinstance(result, dict):
        return False
    got = Fraction(result) if isinstance(result, (int, str)) else result
    if isinstance(expected, Fraction) and isinstance(got, Fraction):
        return got == expected
    return math.isclose(float(got), float(expected), rel_tol=1e-9)


def corner_instances(problem: Problem) -> list[Instance]:
    """Instances at the extremes of each integer range (all min/max combinations), where valid."""
    ranges = {n: v for n, v in problem.variables.items() if isinstance(v, IntRange)}
    defaults = {n: v.default for n, v in problem.variables.items() if not isinstance(v, IntRange)}
    corners = []
    for combo in itertools.islice(itertools.product(*[(v.min, v.max) for v in ranges.values()]), MAX_CORNERS):
        assignment = {n: sp.Integer(x) for n, x in zip(ranges, combo, strict=True)}
        assignment |= {n: evaluate(parse(v), {}) for n, v in defaults.items()}
        instance = build_instance(problem, assignment)
        if instance is not None:
            corners.append(instance)
    return corners


def _checker_targets(problem: Problem, instances: list[Instance]) -> list[Instance]:
    rng = random.Random(f"{problem.id}:checker")
    sample = rng.sample(instances[1:], min(RANDOM_CHECKS, len(instances) - 1))
    targets, seen = [], set()
    for instance in [instances[0], *corner_instances(problem), *sample]:
        if instance.key not in seen:
            seen.add(instance.key)
            targets.append(instance)
    return targets


def _gate_checker(problem: Problem, instances: list[Instance], checker: Path, report: FamilyReport) -> None:
    assert problem.checker is not None
    targets = _checker_targets(problem, instances)
    try:
        results = run_checker(checker, problem.checker, [Call(_kwargs(i)) for i in targets])
    except (UnsafeCode, SandboxError) as error:
        report.failures.append(Failure("checker", problem.id, str(error).splitlines()[0], detail=str(error)))
        return
    for instance, result in zip(targets, results, strict=True):
        expected = _exact(instance.values["answer"])
        if not _same(result, expected):
            report.failures.append(
                Failure(
                    "checker",
                    problem.id,
                    f"brute force gives {result}, the answer expression gives {expected}",
                    instance.key,
                )
            )
    report.checked.setdefault(problem.id, {})["checker"] = len(targets)


def _gate_simulation(
    problem: Problem, instances: list[Instance], checker: Path, report: FamilyReport
) -> None:
    assert problem.simulator is not None
    targets = instances[:1] + random.Random(f"{problem.id}:sim").sample(
        instances[1:], min(1, len(instances) - 1)
    )
    calls = [Call(_kwargs(i), trials=SIMULATION_TRIALS, seed=index) for index, i in enumerate(targets)]
    try:
        results = run_checker(checker, problem.simulator, calls)
    except (UnsafeCode, SandboxError) as error:
        report.failures.append(
            Failure("simulation", problem.id, str(error).splitlines()[0], detail=str(error))
        )
        return
    for instance, result in zip(targets, results, strict=True):
        if not isinstance(result, dict):
            report.failures.append(
                Failure("simulation", problem.id, "simulator returned no statistics", instance.key)
            )
            continue
        exact = float(_exact(instance.values["answer"]))
        mean, variance = result["mean"], max(result["mean_sq"] - result["mean"] ** 2, 0.0)
        margin = Z_999 * math.sqrt(variance / SIMULATION_TRIALS) + 1e-9
        if abs(mean - exact) > margin:
            report.failures.append(
                Failure(
                    "simulation",
                    problem.id,
                    f"{SIMULATION_TRIALS:,} trials average {mean:.5f} ± {margin:.5f}; "
                    f"the answer is {exact:.5f}",
                    instance.key,
                )
            )
    report.checked.setdefault(problem.id, {})["simulation"] = len(targets)


def verify_family(folder: Path) -> FamilyReport:
    report = FamilyReport(folder.name, folder)
    try:
        family = Family.model_validate_json((folder / "family.json").read_text())
    except FileNotFoundError:
        report.failures.append(Failure("schema", folder.name, "family.json is missing"))
        return report
    except ValidationError as error:
        report.failures.append(
            Failure("schema", folder.name, f"{error.error_count()} schema error(s)", detail=str(error))
        )
        return report
    if family.family_id != folder.name:
        report.failures.append(
            Failure("schema", folder.name, f"family_id {family.family_id!r} must match the folder name")
        )

    checker = folder / "checker.py"
    for problem in family.problems:
        try:
            instances = build_instances(problem)
        except (InstanceError, ValueError) as error:
            report.failures.append(Failure("schema", problem.id, str(error)))
            continue
        report.checked[problem.id] = {"instances": len(instances)}
        if len(instances) < MIN_INSTANCES:
            report.failures.append(
                Failure(
                    "schema",
                    problem.id,
                    f"only {len(instances)} valid instances; need at least {MIN_INSTANCES}",
                )
            )
            continue
        if not checker.exists():
            report.failures.append(Failure("checker", problem.id, "checker.py is missing"))
            continue
        if problem.checker:
            _gate_checker(problem, instances, checker, report)
        if problem.simulator:
            _gate_simulation(problem, instances, checker, report)
    return report
