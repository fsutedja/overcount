"""REPORT.md for families that fail verification and land in needs_review/."""

from datetime import date

from .gates import FamilyReport

FIX_STEPS = """## How to fix

1. Open `family.json` and `checker.py` in this folder and fix the issues above.
2. Re-run `uv run overcount verify needs_review/{slug}` (from `pipeline/`) until it passes.
3. Move it into the bank with `uv run overcount promote {slug}`.
"""


def render_report(report: FamilyReport) -> str:
    lines = [f"# Needs review: {report.family_id}", "", f"Verified on {date.today().isoformat()}. "]
    lines[-1] += f"{len(report.failures)} problem(s) found.\n"
    for failure in report.failures:
        where = f" · instance `{failure.instance_key}`" if failure.instance_key else ""
        lines.append(f"- **{failure.gate}** · `{failure.problem_id}`{where}: {failure.message}")
        if failure.detail and failure.detail != failure.message:
            lines += ["", "  ```", *[f"  {line}" for line in failure.detail.splitlines()[:30]], "  ```"]
    lines += ["", FIX_STEPS.format(slug=report.family_id)]
    return "\n".join(lines)
