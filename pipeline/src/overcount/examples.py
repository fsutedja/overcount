"""The ✅/❌ example for each instance: computed by the checker, checked, and formatted for the web."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .instances import Instance
from .schema import Problem
from .verify.sandbox import Call, run_examples
from .visual import UNORDERED, example_errors, outcome_text


@dataclass(frozen=True)
class InstanceExample:
    instance: Instance
    #: What the web shows: outcomes, their text form, highlight, pool, captions.
    data: dict[str, Any]
    #: Problems found (empty when the example is right for this instance).
    errors: list[str]


def kwargs(instance: Instance) -> dict[str, int | str]:
    return {name: int(value) if "/" not in value else value for name, value in instance.vars.items()}


def compute_examples(
    problem: Problem, instances: list[Instance], checker: Path, *, membership: bool
) -> list[InstanceExample]:
    """Runs example_* for each instance in one sandbox call and checks what comes back.

    Raises UnsafeCode / SandboxError like the other checker runs."""
    functions = {"counts": problem.checker.counts, "example": problem.checker.example}
    if problem.checker.outcomes:
        functions["outcomes"] = problem.checker.outcomes
    kind = problem.visual.type
    reports = run_examples(
        checker,
        functions,
        [Call(kwargs(i)) for i in instances],
        unordered=kind in UNORDERED,
        membership=membership,
    )
    results = []
    for instance, report in zip(instances, reports, strict=True):
        example = report["example"]
        errors = example_errors(kind, example)
        if not errors:
            if not report["yes_counts"]:
                errors.append(f"the ✅ outcome {example['yes']} doesn't pass {problem.checker.counts}")
            if report["no_counts"]:
                errors.append(f"the ❌ outcome {example['no']} passes {problem.checker.counts}, so it counts")
            for side in ("yes", "no"):
                if report.get(f"{side}_is_outcome") is False:
                    errors.append(
                        f"the {'✅' if side == 'yes' else '❌'} outcome {example[side]} is not one of "
                        f"{problem.checker.outcomes} for this instance"
                    )
        data: dict[str, Any] = {}
        if not errors:
            data = {
                "yes": {"outcome": example["yes"], "text": outcome_text(kind, example["yes"])},
                "no": {"outcome": example["no"], "text": outcome_text(kind, example["no"])},
                "highlight": example.get("highlight", []),
            }
            data |= {key: example[key] for key in ("pool", "captions") if key in example}
        results.append(InstanceExample(instance, data, errors))
    return results
