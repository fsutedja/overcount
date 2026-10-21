"""Builds the generation prompt from the versioned template and two golden families."""

import json
from pathlib import Path

from ..taxonomy import CONTEXTS, METHODS, MISTAKE_TAGS, STEP_KINDS, TOPICS
from .base import Feedback, Target

PROMPT_VERSION = "family-v3"
PROMPTS_DIR = Path(__file__).parent / "prompts"
EXAMPLE_FAMILIES = ("committee-mixed", "round-table")


def _quoted(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{v}"' for v in values)


def system_prompt(families_dir: Path) -> str:
    examples = []
    for family_id in EXAMPLE_FAMILIES:
        folder = families_dir / family_id
        examples.append(
            f"### {family_id}\n\nfamily:\n```json\n{(folder / 'family.json').read_text().strip()}\n```\n\n"
            f"checker_code:\n```python\n{(folder / 'checker.py').read_text().strip()}\n```"
        )
    template = (PROMPTS_DIR / f"{PROMPT_VERSION}.md").read_text()
    return (
        template.replace("<<TOPICS>>", _quoted(TOPICS))
        .replace("<<CONTEXTS>>", _quoted(CONTEXTS))
        .replace("<<METHODS>>", _quoted(METHODS))
        .replace("<<MISTAKE_TAGS>>", _quoted(MISTAKE_TAGS))
        .replace("<<STEP_KINDS>>", _quoted(STEP_KINDS))
        .replace("<<EXAMPLES>>", "\n\n".join(examples))
    )


def user_prompt(target: Target, feedback: Feedback | None = None) -> str:
    lines = [
        "Write one problem family for this target.",
        f"- target id: {target.id}",
        f"- primary topic: {target.topic}",
        f"- context: {target.context}",
        f"- root difficulty: {target.difficulty}",
        f"- methods: {', '.join(target.methods)}",
        f"- number of variants: {target.variants}",
    ]
    if target.keep_variants:
        lines.append("- this REPLACES an existing family; keep these variant ids and twists, in this order:")
        lines += [
            f'  - id "{variant_id}", twist "{twist}"' for variant_id, twist in target.keep_variants.items()
        ]
    if target.inspiration:
        lines.append(f"- inspiration (adapt, don't copy): {target.inspiration}")
    if target.notes:
        lines.append(f"- notes: {target.notes}")
    if feedback:
        lines += ["", "Your previous reply was rejected by the checks. Fix every problem below and reply"]
        lines += ["with the whole corrected JSON object (family and checker_code):"]
        lines += [f"- {problem}" for problem in feedback.problems]
        if feedback.previous:
            previous = {"family": feedback.previous.family, "checker_code": feedback.previous.checker_code}
            lines += ["", "Previous reply:", json.dumps(previous, ensure_ascii=False)]
    return "\n".join(lines)
