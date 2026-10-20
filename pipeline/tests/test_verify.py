import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from overcount.cli import FAMILIES_DIR
from overcount.verify import sandbox
from overcount.verify.gates import verify_family
from overcount.verify.route import route
from overcount.verify.sandbox import Call, SandboxError, UnsafeCode, check_source, run_checker

# --- sandbox ----------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [
        "import os",
        "import subprocess",
        "from pathlib import Path",
        "from . import secrets",
        "def f():\n    return open('x').read()",
        "def f():\n    return ().__class__.__bases__",
        "def f():\n    return getattr(1, 'real')",
        "def f():\n    return eval('1')",
        "def f():\n    global x",
    ],
)
def test_static_check_rejects_unsafe_code(source: str) -> None:
    assert check_source(source)


def test_static_check_allows_plain_math() -> None:
    source = (
        "from itertools import combinations\nfrom fractions import Fraction\nimport math\n\n"
        "def f(n):\n    return n\n"
    )
    assert check_source(source) == []


def write_checker(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "checker.py"
    path.write_text(source)
    return path


def test_runs_a_checker_in_a_separate_process(tmp_path: Path) -> None:
    path = write_checker(tmp_path, "from fractions import Fraction\n\ndef f(n):\n    return Fraction(n, 3)\n")
    assert run_checker(path, "f", [Call({"n": 1}), Call({"n": 6})]) == ["1/3", 2]


def test_refuses_unsafe_code_before_running(tmp_path: Path) -> None:
    path = write_checker(tmp_path, "import os\n\ndef f():\n    return 1\n")
    with pytest.raises(UnsafeCode):
        run_checker(path, "f", [Call({})])


def test_reports_exceptions_and_bad_return_types(tmp_path: Path) -> None:
    path = write_checker(tmp_path, "def boom():\n    return 1 // 0\n\ndef text():\n    return 'hi'\n")
    with pytest.raises(SandboxError, match="ZeroDivisionError"):
        run_checker(path, "boom", [Call({})])
    with pytest.raises(SandboxError, match="expected a number"):
        run_checker(path, "text", [Call({})])


def test_stops_runaway_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sandbox, "WALL_TIMEOUT_SECONDS", 2)
    path = write_checker(tmp_path, "def spin():\n    while True:\n        pass\n")
    with pytest.raises(SandboxError, match="timed out"):
        run_checker(path, "spin", [Call({})])


# --- gates ------------------------------------------------------------------------------------------


def copy_family(tmp_path: Path, family_id: str = "committee-mixed") -> Path:
    target = tmp_path / family_id
    shutil.copytree(FAMILIES_DIR / family_id, target)
    return target


def edit_family(folder: Path, change: Any) -> None:
    data = json.loads((folder / "family.json").read_text())
    change(data)
    (folder / "family.json").write_text(json.dumps(data))


def test_golden_families_pass() -> None:
    for folder in FAMILIES_DIR.iterdir():
        report = verify_family(folder)
        assert report.passed, report.failures


def test_checker_gate_catches_a_wrong_answer(tmp_path: Path) -> None:
    folder = copy_family(tmp_path)
    # The classic mistake: ordered picks instead of unordered.
    edit_family(folder, lambda d: d["problems"][0]["answer"].update({"expr": "P(J,j)*P(S,s)"}))
    report = verify_family(folder)
    assert not report.passed
    assert {f.gate for f in report.failures} == {"checker"}
    assert any(f.instance_key == "J=8,S=6,j=3,s=2" for f in report.failures)


def test_checker_gate_catches_an_unsafe_checker(tmp_path: Path) -> None:
    folder = copy_family(tmp_path)
    (folder / "checker.py").write_text("import os\n\ndef solve_root(J, S, j, s):\n    return 0\n")
    report = verify_family(folder)
    assert any("not allowed" in f.message for f in report.failures)


def test_schema_gate_catches_invalid_json(tmp_path: Path) -> None:
    folder = copy_family(tmp_path)
    edit_family(folder, lambda d: d["problems"][0].pop("answer"))
    report = verify_family(folder)
    assert [f.gate for f in report.failures] == ["schema"]


def test_missing_checker_file_fails(tmp_path: Path) -> None:
    folder = copy_family(tmp_path)
    (folder / "checker.py").unlink()
    assert {f.gate for f in verify_family(folder).failures} == {"checker"}


DICE: dict[str, Any] = {
    "family_id": "dice-six",
    "problems": [
        {
            "id": "dice-six",
            "origin": {"kind": "authored"},
            "title": "At least one six",
            "statement": "A fair die is rolled {{n}} times. What is the probability of at least one six?",
            "variables": {"n": {"min": 1, "max": 6, "default": 3}},
            "difficulty": "easy",
            "tags": {"topics": ["counting/complement"], "contexts": ["dice"]},
            "answer": {
                "prompt": "P(at least one six)",
                "expr": "1-(5/6)^n",
                "type": "probability",
                "skeleton": {
                    "parts": [{"group": "no six at all", "expr": "1-([a]/[b])^[c]"}],
                    "slots": {
                        "a": {"hint": "not six", "answer": "5"},
                        "b": {"hint": "faces", "answer": "6"},
                        "c": {"hint": "rolls", "answer": "n"},
                    },
                },
            },
            "solution": [
                {
                    "kind": "complement",
                    "title": "Use the complement",
                    "expr": "1-(5/6)^n",
                    "explanation": "At least one six is everything except no sixes in {{n}} rolls.",
                }
            ],
            "simulator": "simulate",
        }
    ],
}


def write_dice(tmp_path: Path, simulator: str) -> Path:
    folder = tmp_path / "dice-six"
    folder.mkdir()
    (folder / "family.json").write_text(json.dumps(DICE))
    (folder / "checker.py").write_text(simulator)
    return folder


def test_simulation_gate_passes_a_correct_probability(tmp_path: Path) -> None:
    folder = write_dice(
        tmp_path, "def simulate(rng, n):\n    return any(rng.randint(1, 6) == 6 for _ in range(n))\n"
    )
    report = verify_family(folder)
    assert report.passed, report.failures
    assert report.checked["dice-six"]["simulation"] == 2


def test_simulation_gate_catches_a_wrong_probability(tmp_path: Path) -> None:
    # Simulates "every roll is a six", which doesn't match 1 - (5/6)^n.
    folder = write_dice(
        tmp_path, "def simulate(rng, n):\n    return all(rng.randint(1, 6) == 6 for _ in range(n))\n"
    )
    report = verify_family(folder)
    assert [f.gate for f in report.failures] == ["simulation", "simulation"]


# --- routing ----------------------------------------------------------------------------------------


def test_route_moves_passing_families_into_content(tmp_path: Path) -> None:
    staging, families, review = tmp_path / "staging", tmp_path / "families", tmp_path / "needs_review"
    staging.mkdir()
    folder = copy_family(staging)
    target = route(verify_family(folder), families, review)
    assert target == families / "committee-mixed"
    assert (target / "family.json").exists() and not folder.exists()


def test_route_sends_failures_to_review_with_a_report(tmp_path: Path) -> None:
    staging, families, review = tmp_path / "staging", tmp_path / "families", tmp_path / "needs_review"
    staging.mkdir()
    folder = copy_family(staging)
    edit_family(folder, lambda d: d["problems"][0]["answer"].update({"expr": "C(J+S,j+s)"}))
    target = route(verify_family(folder), families, review)
    assert target == review / "committee-mixed"
    report = (target / "REPORT.md").read_text()
    assert "**checker** · `committee-mixed`" in report
    assert "overcount promote committee-mixed" in report
