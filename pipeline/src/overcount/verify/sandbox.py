"""Runs a family's checker.py safely.

Checker code may be written by an LLM, so it is treated as untrusted:

1. Static check: an AST allowlist permits only a few pure-math stdlib imports and rejects
   builtins and attributes that reach the file system, the network, or the interpreter.
2. Isolation: the code runs in a separate `python -I` process (ignores environment variables
   and user site-packages) with a CPU-time limit, a memory limit, no file writes, and a
   wall-clock timeout.

This is a strong guard for a local pipeline, not a hardened sandbox against a determined attacker.
"""

import ast
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_IMPORTS = {"itertools", "fractions", "math", "random", "functools", "collections"}
BANNED_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars", "getattr",
    "setattr", "delattr", "input", "breakpoint", "help", "memoryview", "exit", "quit",
}  # fmt: skip

WALL_TIMEOUT_SECONDS = 60
CPU_SECONDS = 50
MEMORY_BYTES = 1024 * 1024 * 1024


class UnsafeCode(ValueError):
    """Checker code that uses something outside the allowlist."""


class SandboxError(RuntimeError):
    """The checker ran but failed: an exception, a timeout, or a resource limit."""


def check_source(source: str) -> list[str]:
    """Returns the problems found in checker source code (empty when it's allowed)."""
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [f"syntax error on line {error.lineno}: {error.msg}"]
    problems = []
    for node in ast.walk(tree):
        match node:
            case ast.Import(names=names):
                problems += [
                    f"import of {a.name!r} is not allowed" for a in names if a.name not in ALLOWED_IMPORTS
                ]
            case ast.ImportFrom(module=module, level=level):
                if level or module not in ALLOWED_IMPORTS:
                    problems.append(f"import from {module!r} is not allowed")
            case ast.Name(id=name) if name in BANNED_NAMES:
                problems.append(f"line {node.lineno}: {name!r} is not allowed")
            case ast.Attribute(attr=attr) if attr.startswith("__"):
                problems.append(f"line {node.lineno}: dunder attribute {attr!r} is not allowed")
            case ast.Global() | ast.Nonlocal():
                problems.append(f"line {node.lineno}: global/nonlocal is not allowed")
    return problems


# The child process: limit resources, load the checker, call the function for each input,
# and print JSON results. Fractions are sent as "p/q" strings both ways.
_RUNNER = r"""
import json, resource, sys
from fractions import Fraction

cpu, memory = int(sys.argv[1]), int(sys.argv[2])
resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
try:
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
except (ValueError, OSError):
    pass  # macOS doesn't support RLIMIT_AS; the CPU limit and timeout still apply.
resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))

request = json.load(sys.stdin)
namespace = {"__name__": "checker"}
exec(compile(request["source"], "checker.py", "exec"), namespace)
functions = {role: namespace[name] for role, name in request["functions"].items()}
unordered = request.get("unordered", False)

def decode(value):
    return Fraction(value) if isinstance(value, str) else value

def encode(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise TypeError(f"checker returned {type(value).__name__}, expected a number")
    if isinstance(value, Fraction):
        return value.numerator if value.denominator == 1 else str(value)
    return value

def plain(value):
    # Outcomes as JSON: tuples become lists, and unordered outcomes are sorted to compare.
    if isinstance(value, (list, tuple)):
        items = [plain(v) for v in value]
        return sorted(items, key=repr) if unordered else items
    if isinstance(value, Fraction):
        return str(value)
    return value

def outcome_json(value):
    return [outcome_json(v) for v in value] if isinstance(value, (list, tuple)) else value

def counts(outcome, kwargs):
    result = functions["counts"](outcome, **kwargs)
    if not isinstance(result, bool):
        raise TypeError(f"counts_* returned {type(result).__name__}, expected True or False")
    return result

def run_value(kwargs, call):
    function = functions["value"]
    if "trials" not in call:
        return encode(function(**kwargs))
    # Simulation: run many trials here and return only their mean and mean square.
    import random
    rng = random.Random(call["seed"])
    total = total_sq = 0.0
    for _ in range(call["trials"]):
        outcome = float(function(rng=rng, **kwargs))
        total += outcome
        total_sq += outcome * outcome
    n = call["trials"]
    return {"mean": total / n, "mean_sq": total_sq / n}

def run_count(kwargs, call):
    good = total = 0
    for outcome in functions["outcomes"](**kwargs):
        total += 1
        good += counts(outcome, kwargs)
    return encode(Fraction(good, total) if request.get("ratio") else good)

def describe(outcome, kwargs):
    entry = {"outcome": outcome_json(outcome), "reason": functions["reason"](outcome, **kwargs)}
    if "highlight" in functions:
        entry["highlight"] = outcome_json(functions["highlight"](outcome, **kwargs))
    return entry

def run_example(kwargs, call):
    example = functions["example"](**kwargs)
    if not isinstance(example, dict) or "yes" not in example or "no" not in example:
        raise TypeError('example_* must return a dict with "yes" and "no"')
    report = {"extra": {k: outcome_json(v) for k, v in example.items() if k not in ("yes", "no")}}
    report["yes_counts"] = counts(example["yes"], kwargs)
    report["no_counts"] = counts(example["no"], kwargs)
    yes_samples, no_samples = [], []
    if "outcomes" in functions and (request.get("membership") or request.get("extras")):
        # One pass over every outcome: check the hand-picked pair are real outcomes, and pick a
        # few more of each kind at random (reservoir sampling, seeded so builds are repeatable).
        import random
        rng = random.Random(call.get("seed", 0))
        extras = request.get("extras", 0)
        wanted = {"yes": plain(example["yes"]), "no": plain(example["no"])}
        found = {"yes": False, "no": False}
        seen = {"yes": 0, "no": 0}
        for outcome in functions["outcomes"](**kwargs):
            normal = plain(outcome)
            if normal == wanted["yes"]:
                found["yes"] = True
                continue
            if normal == wanted["no"]:
                found["no"] = True
                continue
            if not extras:
                continue
            side = "yes" if counts(outcome, kwargs) else "no"
            bucket = yes_samples if side == "yes" else no_samples
            seen[side] += 1
            if len(bucket) < extras:
                bucket.append(outcome)
            else:
                k = rng.randrange(seen[side])
                if k < extras:
                    bucket[k] = outcome
        if request.get("membership"):
            report["yes_is_outcome"], report["no_is_outcome"] = found["yes"], found["no"]
    pairs = [(example["yes"], example["no"])] + list(zip(yes_samples, no_samples))
    report["pairs"] = [{"yes": describe(y, kwargs), "no": describe(n, kwargs)} for y, n in pairs]
    return report

def run_list(kwargs, call):
    # The outcomes that count, up to a limit (one more tells the caller there are too many).
    found = []
    for outcome in functions["outcomes"](**kwargs):
        if counts(outcome, kwargs):
            found.append(outcome_json(outcome))
            if len(found) > request["limit"]:
                break
    return found

run = {"value": run_value, "count": run_count, "example": run_example, "list": run_list}[request["mode"]]
results = []
for call in request["calls"]:
    kwargs = {name: decode(v) for name, v in call["kwargs"].items()}
    results.append(run(kwargs, call))
json.dump(results, sys.stdout)
"""


@dataclass(frozen=True)
class Call:
    kwargs: dict[str, int | str]
    #: For simulators: how many trials to run, each given the same seeded `random.Random` as `rng`.
    trials: int | None = None
    seed: int = 0

    def as_json(self) -> dict[str, Any]:
        data: dict[str, Any] = {"kwargs": self.kwargs}
        if self.trials is not None:
            data |= {"trials": self.trials, "seed": self.seed}
        return data


Result = int | float | str | dict[str, float]


def run_checker(checker_path: Path, function: str, calls: list[Call]) -> list[Result]:
    """Runs `function` from checker.py once per call in an isolated process and returns its results."""
    results: list[Result] = _run(checker_path, {"mode": "value", "functions": {"value": function}}, calls)
    return results


def run_count(checker_path: Path, outcomes: str, counts: str, calls: list[Call], ratio: bool) -> list[Result]:
    """Counts the outcomes that pass `counts` (as a fraction of all outcomes when `ratio`)."""
    request = {"mode": "count", "functions": {"outcomes": outcomes, "counts": counts}, "ratio": ratio}
    results: list[Result] = _run(checker_path, request, calls)
    return results


def run_examples(
    checker_path: Path,
    functions: dict[str, str],
    calls: list[Call],
    *,
    unordered: bool,
    membership: bool,
    extras: int = 0,
) -> list[dict[str, Any]]:
    """Calls example_* per call and reports whether its yes/no outcomes count (and exist, when
    `membership` and an outcomes function are given), plus up to `extras` more sampled pairs.
    Every outcome comes back with its reason (and highlight, when the checker has one)."""
    request = {
        "mode": "example",
        "functions": functions,
        "unordered": unordered,
        "membership": membership,
        "extras": extras,
    }
    results: list[dict[str, Any]] = _run(checker_path, request, calls)
    return results


def run_list(checker_path: Path, outcomes: str, counts: str, call: Call, limit: int) -> list[Any]:
    """The outcomes that pass `counts` for one instance, at most `limit` + 1 of them."""
    request = {"mode": "list", "functions": {"outcomes": outcomes, "counts": counts}, "limit": limit}
    results: list[list[Any]] = _run(checker_path, request, [call])
    return results[0]


def _run(checker_path: Path, request_fields: dict[str, Any], calls: list[Call]) -> Any:
    source = checker_path.read_text()
    problems = check_source(source)
    if problems:
        raise UnsafeCode("; ".join(problems))
    function = ", ".join(request_fields["functions"].values())
    request = json.dumps({"source": source, **request_fields, "calls": [c.as_json() for c in calls]})
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-c", _RUNNER, str(CPU_SECONDS), str(MEMORY_BYTES)],
            input=request,
            capture_output=True,
            text=True,
            timeout=WALL_TIMEOUT_SECONDS,
            cwd=checker_path.parent,
            env={},
        )
    except subprocess.TimeoutExpired as error:
        raise SandboxError(f"{function} timed out after {WALL_TIMEOUT_SECONDS}s") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()[-1:] or [f"exit code {completed.returncode}"]
        raise SandboxError(f"{function} failed: {detail[0]}\n{completed.stderr.strip()}")
    return json.loads(completed.stdout)
