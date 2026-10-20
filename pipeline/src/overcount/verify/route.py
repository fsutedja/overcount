"""Moves families between the pipeline's folders based on verification.

staging/<slug>/        fresh generator output (gitignored)
needs_review/<slug>/   failed a gate; has a REPORT.md; fix by hand, then promote
content/families/<slug>/   verified; this is what `overcount build` publishes
"""

import shutil
from pathlib import Path

from .gates import FamilyReport, verify_family
from .report import render_report


class RouteError(RuntimeError):
    pass


def family_folders(path: Path) -> list[Path]:
    """A single family folder, or every family folder directly inside `path`."""
    if (path / "family.json").exists():
        return [path]
    if not path.is_dir():
        return []
    return sorted(p for p in path.iterdir() if p.is_dir() and not p.name.startswith("."))


def verify_folder(path: Path) -> list[FamilyReport]:
    return [verify_family(folder) for folder in family_folders(path)]


def route(report: FamilyReport, families_dir: Path, review_dir: Path) -> Path:
    """Moves a staged family to content/families/ if it passed, else to needs_review/ with a report."""
    if report.passed:
        target = families_dir / report.family_id
        if target.exists():
            raise RouteError(f"content/families/{report.family_id} already exists; rename the new family")
        (report.folder / "REPORT.md").unlink(missing_ok=True)
    else:
        target = review_dir / report.family_id
        if target.exists():
            shutil.rmtree(target)
        (report.folder / "REPORT.md").write_text(render_report(report))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(report.folder, target)
    return target


def write_review_report(report: FamilyReport) -> None:
    """Refreshes REPORT.md in place for a family that is already in needs_review/."""
    if report.passed:
        (report.folder / "REPORT.md").unlink(missing_ok=True)
    else:
        (report.folder / "REPORT.md").write_text(render_report(report))
