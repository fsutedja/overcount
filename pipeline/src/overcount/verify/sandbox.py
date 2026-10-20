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
function = namespace[request["function"]]

def decode(value):
    return Fraction(value) if isinstance(value, str) else value

def encode(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise TypeError(f"checker returned {type(value).__name__}, expected a number")
    if isinstance(value, Fraction):
        return value.numerator if value.denominator == 1 else str(value)
    return value

results = []
for call in request["calls"]:
    kwargs = {name: decode(v) for name, v in call["kwargs"].items()}
    if "trials" not in call:
        results.append(encode(function(**kwargs)))
        continue
    # Simulation: run many trials here and return only their mean and mean square.
    import random
    rng = random.Random(call["seed"])
    total = total_sq = 0.0
    for _ in range(call["trials"]):
        outcome = float(function(rng=rng, **kwargs))
        total += outcome
        total_sq += outcome * outcome
    n = call["trials"]
    results.append({"mean": total / n, "mean_sq": total_sq / n})
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
    source = checker_path.read_text()
    problems = check_source(source)
    if problems:
        raise UnsafeCode("; ".join(problems))
    request = json.dumps({"source": source, "function": function, "calls": [c.as_json() for c in calls]})
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
    results: list[Result] = json.loads(completed.stdout)
    return results
