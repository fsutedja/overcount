"""staging/review.html: one page to review staged drafts before approving them.

For each staged family it shows the gate results and, per problem, the statement (with the
default numbers filled in), answer formula and value, Help skeleton, solution, and common
mistakes. When the family replaces one already in content/, the old version is shown alongside.
"""

import html
import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..expr import display_text
from ..instances import Instance, build_instances
from ..schema import Family, Problem, SkeletonGroup
from .gates import FamilyReport

_OP = {"*": "×", "+": "+", "-": "−", "/": "÷"}


def _fill(text: str, instance: Instance | None) -> str:
    if instance is None:
        return text
    return re.sub(r"\{\{(\w+)\}\}", lambda m: instance.vars.get(m[1], m[0]), text)


def _value(instance: Instance | None) -> str:
    if instance is None:
        return "—"
    value = instance.values["answer"]
    return str(value.get("exact", value.get("approx")))


def _problem_card(problem: Problem | None) -> str:
    if problem is None:
        return '<div class="card empty">Not in this version</div>'
    try:
        instances = build_instances(problem)
    except ValueError:
        instances = []
    default = instances[0] if instances else None
    e = html.escape
    skeleton = " ".join(
        f"<b>{e(display_text(p.expr))}</b><small>{e(p.group)}</small>"
        if isinstance(p, SkeletonGroup)
        else e(_OP[p.op])
        for p in problem.answer.skeleton.parts
    )
    hints = ", ".join(f"[{slot}] {e(spec.hint)}" for slot, spec in problem.answer.skeleton.slots.items())
    steps = "".join(
        f"<li><b>{e(s.title)}</b> <code>{e(s.expr)}</code><br>{e(_fill(s.explanation, default))}</li>"
        for s in problem.solution
    )
    wrong = "".join(
        f"<li><code>{e(m.expr)}</code> <i>{e(m.mistake_tag)}</i>: {e(_fill(m.feedback, default))}</li>"
        for m in problem.answer.common_wrong
    )
    meta = f"{problem.difficulty} · {', '.join(problem.tags.methods)}" + (
        f" · twist: {e(problem.twist)}" if problem.twist else ""
    )
    return f"""<div class="card">
  <p class="meta">{e(meta)} · {len(instances)} number sets{f" · deck: {problem.deck}" if problem.deck else ""}</p>
  <h4>{e(problem.title)}</h4>
  <p>{e(_fill(problem.statement, default))}</p>
  <p class="answer"><code>{e(problem.answer.expr)}</code> = <b>{e(_value(default))}</b>
     <span class="meta">({e(default.key) if default else "no valid instance"})</span></p>
  <p class="label">Help skeleton</p><p class="skeleton">{skeleton}</p><p class="meta">{hints}</p>
  <p class="label">Solution</p><ol>{steps}</ol>
  <p class="label">Common mistakes</p><ul>{wrong}</ul>
</div>"""


def _load(folder: Path) -> tuple[Family | None, str | None]:
    try:
        return Family.model_validate_json((folder / "family.json").read_text()), None
    except (ValidationError, FileNotFoundError, json.JSONDecodeError) as error:
        return None, str(error)


def _family_section(report: FamilyReport, families_dir: Path) -> str:
    e = html.escape
    new, error = _load(report.folder)
    old_folder = families_dir / report.family_id
    old = _load(old_folder)[0] if old_folder.exists() else None
    status = "pass" if report.passed else "fail"
    failures = "".join(
        f"<li><b>{e(f.gate)}</b> · {e(f.problem_id)}{f' [{e(f.instance_key)}]' if f.instance_key else ''}: {e(f.message)}</li>"
        for f in report.failures
    )
    checks = " · ".join(
        f"{e(pid)}: " + ", ".join(f"{g} {n}" for g, n in gates.items())
        for pid, gates in report.checked.items()
    )
    header = f"""<section id="{e(report.family_id)}">
<h2>{e(report.family_id)} <span class="badge {status}">{"passes every gate" if report.passed else "fails a gate"}</span>
    {'<span class="badge regen">replaces the live version</span>' if old else '<span class="badge">new family</span>'}</h2>
<p class="meta">{checks}</p>{f"<ul class='fail'>{failures}</ul>" if failures else ""}
<p class="cmd"><code>uv run overcount approve {e(report.family_id)}</code> &nbsp; or &nbsp; <code>uv run overcount reject {e(report.family_id)}</code></p>"""
    if new is None:
        return header + f"<pre>{e(error or '')}</pre></section>"
    rows = []
    new_problems = {p.id: p for p in new.problems}
    old_problems = {p.id: p for p in old.problems} if old else {}
    for problem_id in [*new_problems, *[i for i in old_problems if i not in new_problems]]:
        if old:
            rows.append(
                f'<h3>{e(problem_id)}</h3><div class="pair"><div><p class="label">Old (live)</p>'
                f"{_problem_card(old_problems.get(problem_id))}</div><div><p class='label'>New (staged)</p>"
                f"{_problem_card(new_problems.get(problem_id))}</div></div>"
            )
        else:
            rows.append(f"<h3>{e(problem_id)}</h3>{_problem_card(new_problems.get(problem_id))}")
    return header + "".join(rows) + "</section>"


def render_review(reports: list[FamilyReport], families_dir: Path) -> str:
    toc = "".join(
        f'<li><a href="#{html.escape(r.family_id)}">{html.escape(r.family_id)}</a> {"✓" if r.passed else "✗"}</li>'
        for r in reports
    )
    body = "".join(_family_section(r, families_dir) for r in reports)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Review staged families</title>
<style>
body{{margin:0;background:#F4EFE6;color:#2B2823;font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1200px;margin:0 auto;padding:24px 16px 64px}}
section{{border-top:2px solid #E4D9C6;margin-top:28px;padding-top:8px}}
.card{{background:#FFFBF3;border:1px solid #E4D9C6;border-radius:10px;padding:10px 14px;margin:6px 0}}
.card.empty{{color:#675F53;font-style:italic}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} @media(max-width:800px){{.pair{{grid-template-columns:1fr}}}}
.meta{{color:#675F53;font-size:13px;margin:2px 0}} .label{{color:#675F53;font-size:12px;text-transform:uppercase;letter-spacing:.04em;margin:10px 0 2px}}
.answer code,.cmd code{{background:#E3EEEC;padding:1px 5px;border-radius:4px}} .skeleton b{{font-family:ui-monospace,monospace}}
.skeleton small{{color:#675F53;margin:0 6px 0 4px}} h4{{margin:4px 0}} h3{{margin:18px 0 0}}
.badge{{font-size:12px;border:1px solid #E4D9C6;border-radius:6px;padding:1px 8px;margin-left:6px;font-weight:600}}
.badge.pass{{background:#E1ECD8;color:#35652F}} .badge.fail{{background:#F3E0E7;color:#8E3352}} .badge.regen{{background:#E3EEEC;color:#276660}}
ul.fail{{color:#8E3352}} pre{{white-space:pre-wrap;background:#FFFBF3;padding:8px}}
</style></head><body><main>
<h1>Review staged families</h1>
<p class="meta">Nothing here is published. Approve or reject each family with the commands shown.</p>
<ul>{toc}</ul>{body}</main></body></html>"""


def write_review(reports: list[FamilyReport], families_dir: Path, out: Path) -> Path:
    out.write_text(render_review(reports, families_dir))
    return out


def summarize(report: FamilyReport) -> dict[str, Any]:
    """A compact record of a verify run for the generation log."""
    return {
        "target_id": report.family_id,
        "status": "verified_pass" if report.passed else "verified_fail",
        "gates": sorted({f.gate for f in report.failures}),
    }
