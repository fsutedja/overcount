"""The ✅/❌ examples for each instance: computed by the checker, checked, and formatted for the web.

The first pair is hand-picked by the checker's example_* function; up to EXTRA_PAIRS more are
sampled from its own outcomes for "Show another example". Every pair is checked: the ✅ outcome
passes counts_*, the ❌ one doesn't, and both are real outcomes of that instance.
"""

import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .instances import Instance
from .schema import Problem
from .verify.sandbox import Call, run_examples
from .visual import UNORDERED, example_errors, outcome_text, pair_errors

#: Extra pairs per instance for "Show another example".
EXTRA_PAIRS = 4
#: Instances per sandbox process, so each stays well inside its CPU limit.
CHUNK = 10


@dataclass(frozen=True)
class InstanceExample:
    instance: Instance
    #: What the web shows: pairs of outcomes with text, reason and highlight; pool; captions.
    data: dict[str, Any]
    #: Problems found (empty when every pair is right for this instance).
    errors: list[str]


def kwargs(instance: Instance) -> dict[str, int | str]:
    return {name: int(value) if "/" not in value else value for name, value in instance.vars.items()}


def _seed(instance: Instance) -> int:
    return zlib.crc32(instance.key.encode())


def compute_examples(
    problem: Problem,
    instances: list[Instance],
    checker: Path,
    *,
    membership: bool,
    extras: int = EXTRA_PAIRS,
) -> list[InstanceExample]:
    """Runs the example functions for each instance in the sandbox and checks what comes back.

    Raises UnsafeCode / SandboxError like the other checker runs."""
    fns = problem.checker
    functions = {"counts": fns.counts, "example": fns.example, "reason": fns.reason}
    if fns.outcomes:
        functions["outcomes"] = fns.outcomes
    if fns.highlight:
        functions["highlight"] = fns.highlight
    kind = problem.visual.type
    reports: list[dict[str, Any]] = []
    for start in range(0, len(instances), CHUNK):
        chunk = instances[start : start + CHUNK]
        reports += run_examples(
            checker,
            functions,
            [Call(kwargs(i), seed=_seed(i)) for i in chunk],
            unordered=kind in UNORDERED,
            membership=membership,
            extras=extras,
        )
    return [_check(problem, instance, report) for instance, report in zip(instances, reports, strict=True)]


def _check(problem: Problem, instance: Instance, report: dict[str, Any]) -> InstanceExample:
    kind, fns = problem.visual.type, problem.checker
    first = report["pairs"][0]
    handpicked = {"yes": first["yes"]["outcome"], "no": first["no"]["outcome"], **report["extra"]}
    errors = example_errors(kind, handpicked)
    for pair in report["pairs"]:
        errors += pair_errors(kind, pair)
    if not errors:
        if not report["yes_counts"]:
            errors.append(f"the ✅ outcome {handpicked['yes']} doesn't pass {fns.counts}")
        if report["no_counts"]:
            errors.append(f"the ❌ outcome {handpicked['no']} passes {fns.counts}, so it counts")
        for side, mark in (("yes", "✅"), ("no", "❌")):
            if report.get(f"{side}_is_outcome") is False:
                errors.append(
                    f"the {mark} outcome {handpicked[side]} is not one of {fns.outcomes} for this instance"
                )
    if errors:
        return InstanceExample(instance, {}, errors)
    captions = report["extra"].get("captions")

    def shown(entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "outcome": entry["outcome"],
            "text": outcome_text(kind, entry["outcome"], captions),
            "reason": entry["reason"],
            "highlight": entry.get("highlight", []),
        }

    pairs = [{"yes": shown(p["yes"]), "no": shown(p["no"])} for p in report["pairs"]]
    data: dict[str, Any] = {"pairs": pairs}
    data |= {key: report["extra"][key] for key in ("pool", "captions") if key in report["extra"]}
    return InstanceExample(instance, data, errors)
