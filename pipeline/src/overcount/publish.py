"""Builds the static problem bank the web app loads (PLAN.md §2b).

content/families/<slug>/family.json  →  web/public/bank/index.json
                                        web/public/bank/families/<slug>.json
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .expr import display_text, parse, to_group_latex, to_latex
from .instances import build_instances
from .schema import Family, Mistake, Problem, SkeletonGroup

_OP_DISPLAY = {"*": "×", "+": "+", "-": "−", "/": "÷"}
_OP_LATEX = {"*": "\\times", "+": "+", "-": "-", "/": "\\div"}

Json = dict[str, Any]


def load_family(path: Path) -> Family:
    return Family.model_validate_json(path.read_text())


def _latex(source: str) -> str:
    return to_latex(parse(source))


def _mistake(mistake: Mistake) -> Json:
    return {"latex": _latex(mistake.expr), "feedback": mistake.feedback, "mistake_tag": mistake.mistake_tag}


def mistake_tags(problem: Problem) -> list[str]:
    tags = {m.mistake_tag for m in problem.answer.common_wrong} | {
        m.mistake_tag for m in problem.answer.skeleton.slot_mistakes
    }
    return sorted(tags)


def problem_json(problem: Problem, family_id: str) -> Json:
    skeleton = problem.answer.skeleton
    parts: list[Json] = [
        {
            "group": {
                "label": part.group,
                "display": display_text(part.expr),
                "latex": to_group_latex(parse(part.expr)),
            }
        }
        if isinstance(part, SkeletonGroup)
        else {"op": {"display": _OP_DISPLAY[part.op], "latex": _OP_LATEX[part.op]}}
        for part in skeleton.parts
    ]
    return {
        "id": problem.id,
        "family_id": family_id,
        "variant_of": problem.variant_of,
        "twist": problem.twist,
        "title": problem.title,
        "statement": problem.statement,
        "difficulty": problem.difficulty,
        "tags": {"topics": list(problem.tags.topics), "contexts": list(problem.tags.contexts)},
        "answer": {
            "prompt": problem.answer.prompt,
            "latex": _latex(problem.answer.expr),
            "common_wrong": [_mistake(m) for m in problem.answer.common_wrong],
            "skeleton": {
                "parts": parts,
                "slots": {slot: {"hint": spec.hint} for slot, spec in skeleton.slots.items()},
                "slot_mistakes": [{"slot": m.slot, **_mistake(m)} for m in skeleton.slot_mistakes],
            },
        },
        "solution": [
            {
                "kind": step.kind,
                "title": step.title,
                "latex": _latex(step.expr),
                "explanation": step.explanation,
            }
            for step in problem.solution
        ],
        "instances": [instance.as_json() for instance in build_instances(problem)],
    }


def index_entry(problem_data: Json, problem: Problem) -> Json:
    return {
        "id": problem.id,
        "family_id": problem_data["family_id"],
        "variant_of": problem.variant_of,
        "twist": problem.twist,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "tags": problem_data["tags"],
        "mistake_tags": mistake_tags(problem),
        "instance_count": len(problem_data["instances"]),
    }


@dataclass(frozen=True)
class Bank:
    """Every output file, keyed by its path relative to the bank folder."""

    files: dict[str, str]


def _dump(data: Json, compact: bool = False) -> str:
    if compact:
        return json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def build_bank(content_dir: Path) -> Bank:
    family_paths = sorted((content_dir / "families").glob("*/family.json"))
    files: dict[str, str] = {}
    index: list[Json] = []
    seen_ids: set[str] = set()
    for path in family_paths:
        family = load_family(path)
        if family.family_id != path.parent.name:
            raise ValueError(f"{path}: family_id {family.family_id!r} must match its folder name")
        problems = []
        for problem in family.problems:
            if problem.id in seen_ids:
                raise ValueError(f"problem id {problem.id!r} is used more than once in the bank")
            seen_ids.add(problem.id)
            data = problem_json(problem, family.family_id)
            problems.append(data)
            index.append(index_entry(data, problem))
        # Family files hold ~100 instances per problem and are only read by the app: keep them compact.
        family_data = {"family_id": family.family_id, "problems": problems}
        files[f"families/{family.family_id}.json"] = _dump(family_data, compact=True)
    files["index.json"] = _dump({"schema_version": 1, "problems": index})
    return Bank(files)


def write_bank(bank: Bank, out_dir: Path) -> None:
    for relative, text in bank.files.items():
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    # Drop families that no longer exist in content/.
    for stale in (out_dir / "families").glob("*.json"):
        if f"families/{stale.name}" not in bank.files:
            stale.unlink()


def stale_files(bank: Bank, out_dir: Path) -> list[str]:
    """Paths whose committed contents differ from a fresh build (for `build --check` in CI)."""
    stale = [
        rel
        for rel, text in bank.files.items()
        if not (out_dir / rel).exists() or (out_dir / rel).read_text() != text
    ]
    stale += [
        f"families/{p.name}"
        for p in (out_dir / "families").glob("*.json")
        if f"families/{p.name}" not in bank.files
    ]
    return sorted(stale)
