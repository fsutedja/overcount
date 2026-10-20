"""Command-line interface: `uv run overcount --help`."""

import json
from collections import Counter
from pathlib import Path
from typing import Annotated

import typer

from .publish import build_bank, stale_files, write_bank
from .verify.gates import FamilyReport
from .verify.route import RouteError, family_folders, route, verify_folder, write_review_report

REPO_ROOT = Path(__file__).resolve().parents[3]

app = typer.Typer(
    help="Overcount content pipeline: verify problem templates and publish the static bank.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Overcount content pipeline."""


CONTENT_DIR = REPO_ROOT / "content"
FAMILIES_DIR = CONTENT_DIR / "families"
STAGING_DIR = REPO_ROOT / "staging"
REVIEW_DIR = REPO_ROOT / "needs_review"
BANK_DIR = REPO_ROOT / "web" / "public" / "bank"


def _print_report(report: FamilyReport) -> None:
    status = typer.style("PASS", fg="green") if report.passed else typer.style("FAIL", fg="red")
    checks = ", ".join(
        f"{problem}: {' · '.join(f'{gate} {n}' for gate, n in gates.items())}"
        for problem, gates in report.checked.items()
    )
    typer.echo(f"{status}  {report.family_id}  ({checks})" if checks else f"{status}  {report.family_id}")
    for failure in report.failures:
        where = f" [{failure.instance_key}]" if failure.instance_key else ""
        typer.echo(f"      {failure.gate} · {failure.problem_id}{where}: {failure.message}")


@app.command()
def verify(
    path: Annotated[
        Path, typer.Argument(help="staging/, needs_review/<slug>, or content/families")
    ] = FAMILIES_DIR,
) -> None:
    """Run the schema, brute-force checker, and simulation gates.

    Families verified from staging/ are moved: passing ones to content/families/, failing ones to
    needs_review/ with a REPORT.md. Elsewhere, families stay put and are only reported on.
    """
    path = path.resolve()
    reports = verify_folder(path)
    if not reports:
        typer.echo(f"No families found in {path}")
        return
    staged = path == STAGING_DIR or path.parent == STAGING_DIR
    in_review = path == REVIEW_DIR or path.parent == REVIEW_DIR
    for report in reports:
        _print_report(report)
        if staged:
            try:
                target = route(report, FAMILIES_DIR, REVIEW_DIR)
            except RouteError as error:
                typer.echo(f"      not moved: {error}", err=True)
                continue
            typer.echo(f"      → {target.relative_to(REPO_ROOT)}")
        elif in_review:
            write_review_report(report)
            if report.passed:
                typer.echo(f"      ready: run `uv run overcount promote {report.family_id}`")
    failed = sum(not r.passed for r in reports)
    typer.echo(f"\n{len(reports) - failed} passed, {failed} failed.")
    if failed and not staged:
        raise typer.Exit(1)


@app.command()
def promote(slug: Annotated[str, typer.Argument(help="Folder name in needs_review/")]) -> None:
    """Re-verify a fixed family in needs_review/ and move it into content/families/."""
    folder = REVIEW_DIR / slug
    if not (folder / "family.json").exists():
        typer.echo(f"needs_review/{slug} doesn't exist.", err=True)
        raise typer.Exit(1)
    report = verify_folder(folder)[0]
    _print_report(report)
    if not report.passed:
        write_review_report(report)
        typer.echo("Still failing; REPORT.md is updated.", err=True)
        raise typer.Exit(1)
    try:
        target = route(report, FAMILIES_DIR, REVIEW_DIR)
    except RouteError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Promoted to {target.relative_to(REPO_ROOT)}. Run `uv run overcount build` to publish it.")


@app.command()
def stats() -> None:
    """Counts of verified, waiting, and staged families, plus coverage by topic and difficulty."""
    roots = variants = instances = 0
    topics: Counter[str] = Counter()
    difficulties: Counter[str] = Counter()
    for folder in family_folders(FAMILIES_DIR):
        family = json.loads((folder / "family.json").read_text())
        for problem in family["problems"]:
            if problem.get("variant_of"):
                variants += 1
            else:
                roots += 1
                topics[problem["tags"]["topics"][0]] += 1
                difficulties[problem["difficulty"]] += 1
    index = BANK_DIR / "index.json"
    if index.exists():
        instances = sum(p["instance_count"] for p in json.loads(index.read_text())["problems"])

    typer.echo("Pipeline")
    typer.echo(f"  staged        {len(family_folders(STAGING_DIR))} families")
    typer.echo(f"  needs review  {len(family_folders(REVIEW_DIR))} families")
    verified = len(family_folders(FAMILIES_DIR))
    typer.echo(f"  verified      {verified} families: {roots} problems + {variants} variants")
    typer.echo(f"  published     {instances:,} problem instances in the bank")
    typer.echo("\nRoot problems by primary topic")
    for topic, count in sorted(topics.items()):
        typer.echo(f"  {count:>3}  {topic}")
    typer.echo("\nRoot problems by difficulty")
    for level in ("easy", "medium", "hard"):
        typer.echo(f"  {difficulties[level]:>3}  {level}")


@app.command()
def build(
    content: Annotated[Path, typer.Option(help="Folder with families/<slug>/family.json")] = CONTENT_DIR,
    out: Annotated[Path, typer.Option(help="Where the web app loads the bank from")] = BANK_DIR,
    check: Annotated[bool, typer.Option(help="Only check the committed bank is up to date (CI)")] = False,
) -> None:
    """Build the problem bank from content/ into web/public/bank/."""
    bank = build_bank(content)
    if check:
        stale = stale_files(bank, out)
        if stale:
            typer.echo("The committed bank is out of date. Run `uv run overcount build`:", err=True)
            for path in stale:
                typer.echo(f"  {path}", err=True)
            raise typer.Exit(1)
        typer.echo("Bank is up to date.")
        return
    write_bank(bank, out)
    typer.echo(f"Wrote {len(bank.files)} files to {out}")
