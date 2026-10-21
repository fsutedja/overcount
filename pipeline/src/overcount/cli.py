"""Command-line interface: `uv run overcount --help`."""

import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from .generate.base import load_targets
from .generate.gemini import GeminiGenerator
from .generate.prompt import PROMPT_VERSION, system_prompt, user_prompt
from .generate.ratelimit import GenerationLog, RateLimiter
from .generate.run import run_generation
from .publish import build_bank, preview_family, stale_files, write_bank
from .verify.gates import FamilyReport
from .verify.review_page import summarize, write_review
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
#: Dev-only previews of staged families (gitignored).
PREVIEW_DIR = REPO_ROOT / "web" / "public" / "preview"
TARGETS_FILE = CONTENT_DIR / "targets.yaml"
GENERATION_LOG = REPO_ROOT / "data" / "generation_log.jsonl"
#: Used when .env doesn't set GEMINI_MODEL. Check `client.models.list()` if it stops working.
DEFAULT_MODEL = "gemini-3.8-flash"


@app.command()
def generate(
    limit: Annotated[int | None, typer.Option(help="Generate at most this many families this run")] = None,
    only: Annotated[
        list[str] | None, typer.Option(help="Generate just these target ids (repeatable)")
    ] = None,
    method: Annotated[
        list[str] | None, typer.Option(help="Only targets drilling these methods (repeatable)")
    ] = None,
    force: Annotated[bool, typer.Option(help="Regenerate targets that are already done")] = False,
    dry_run: Annotated[bool, typer.Option(help="Show what would be sent, without calling the API")] = False,
) -> None:
    """Draft new problem families with Gemini into staging/. Then run `verify staging`."""
    targets = load_targets(TARGETS_FILE)
    if only:
        unknown = set(only) - {t.id for t in targets}
        if unknown:
            typer.echo(f"No target called {sorted(unknown)} in content/targets.yaml.", err=True)
            raise typer.Exit(1)
        targets = [t for t in targets if t.id in only]
    if method:
        targets = [t for t in targets if set(t.methods) & set(method)]

    if dry_run:
        prompt = system_prompt(FAMILIES_DIR)
        typer.echo(
            f"System prompt: {len(prompt):,} characters (prompts/{PROMPT_VERSION}.md + 2 example families)\n"
        )
        for target in targets[: limit or len(targets)]:
            typer.echo(user_prompt(target) + "\n")
        return

    load_dotenv(REPO_ROOT / ".env")
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        typer.echo("GEMINI_API_KEY is missing. Add it to the .env file in the repo root.", err=True)
        raise typer.Exit(1)
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    log = GenerationLog(GENERATION_LOG)
    limiter = RateLimiter(
        requests_per_minute=int(os.environ.get("GEMINI_RPM", "10")),
        requests_per_day=int(os.environ.get("GEMINI_RPD", "250")),
        used_today=log.requests_today(),
    )
    generator = GeminiGenerator.from_key(api_key, model, limiter, FAMILIES_DIR)
    existing = {p.name for d in (FAMILIES_DIR, REVIEW_DIR, STAGING_DIR) for p in family_folders(d)}

    typer.echo(f"Generating with {model} ({limiter.used_today} requests already used today)…")
    result = run_generation(generator, limiter, targets, log, STAGING_DIR, existing, limit=limit, force=force)

    for target_id in result.staged:
        typer.echo(f"  staged   {target_id}")
    for target_id, reason in result.failed:
        typer.echo(f"  failed   {target_id}: {reason}")
    if result.skipped:
        typer.echo(f"  skipped  {len(result.skipped)} already-done target(s)")
    if result.stopped_reason:
        typer.echo(f"Stopped: {result.stopped_reason}")
        typer.echo("Set GEMINI_MODEL in .env to a model your key can use.")
    if result.stopped_for_quota:
        typer.echo("Stopped: the daily free-tier quota is used up. Run again tomorrow to continue.")
    if result.staged:
        typer.echo("\nNext: `uv run overcount verify ../staging` to check the drafts.")


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
    route_staged: Annotated[
        bool, typer.Option("--route/--no-route", help="Move staged families after verifying them")
    ] = True,
) -> None:
    """Run the schema, brute-force checker, and simulation gates.

    Families verified from staging/ are moved (unless --no-route): passing ones to
    content/families/, failing ones to needs_review/ with a REPORT.md. Elsewhere, families stay
    put and are only reported on.
    """
    path = path.resolve()
    reports = verify_folder(path)
    if not reports:
        typer.echo(f"No families found in {path}")
        return
    staged = path == STAGING_DIR or path.parent == STAGING_DIR
    in_review = path == REVIEW_DIR or path.parent == REVIEW_DIR
    log = GenerationLog(GENERATION_LOG)
    for report in reports:
        _print_report(report)
        if staged or in_review:
            log.append(**summarize(report))
        if staged and route_staged:
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
def review() -> None:
    """Verify every staged family (without moving it) and write staging/review.html."""
    reports = verify_folder(STAGING_DIR)
    if not reports:
        typer.echo("Nothing is staged.")
        return
    log = GenerationLog(GENERATION_LOG)
    for report in reports:
        _print_report(report)
        log.append(**summarize(report))
    page = write_review(reports, FAMILIES_DIR, STAGING_DIR / "review.html")
    typer.echo(f"\nWrote {page.relative_to(REPO_ROOT)}. Open it, then approve or reject each family.")
    # Passing drafts also go to a gitignored preview folder, so the dev server can show them on
    # the real problem page (with diagrams) at /dev/preview/<slug>.
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for stale in PREVIEW_DIR.glob("*.json"):
        stale.unlink()
    for report in reports:
        if report.passed:
            (PREVIEW_DIR / f"{report.family_id}.json").write_text(preview_family(report.folder))
            typer.echo(f"Preview: http://localhost:5173/dev/preview/{report.family_id}")


@app.command()
def approve(slug: Annotated[str, typer.Argument(help="Folder name in staging/")]) -> None:
    """Re-verify a staged family, publish it (replacing the live version, if any), rebuild the bank."""
    folder = STAGING_DIR / slug
    if not (folder / "family.json").exists():
        typer.echo(f"staging/{slug} doesn't exist.", err=True)
        raise typer.Exit(1)
    report = verify_folder(folder)[0]
    _print_report(report)
    if not report.passed:
        typer.echo("Not approved: it fails a gate. Fix it, or reject it.", err=True)
        raise typer.Exit(1)
    target = FAMILIES_DIR / slug
    replaced = target.exists()
    if replaced:
        shutil.rmtree(target)  # the old version stays in git history
    (folder / "REPORT.md").unlink(missing_ok=True)
    shutil.move(folder, target)
    write_bank(build_bank(CONTENT_DIR), BANK_DIR)
    GenerationLog(GENERATION_LOG).append(target_id=slug, status="approved", replaced=replaced)
    typer.echo(f"Approved {slug}{' (replaced the live version)' if replaced else ''}; the bank is rebuilt.")


@app.command()
def reject(slug: Annotated[str, typer.Argument(help="Folder name in staging/")]) -> None:
    """Delete a staged draft. The live version, if any, stays as it is."""
    folder = STAGING_DIR / slug
    if not folder.exists():
        typer.echo(f"staging/{slug} doesn't exist.", err=True)
        raise typer.Exit(1)
    shutil.rmtree(folder)
    GenerationLog(GENERATION_LOG).append(target_id=slug, status="rejected")
    typer.echo(f"Rejected {slug}; the staged draft is deleted.")


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

    statuses = Counter(e.get("status") for e in GenerationLog(GENERATION_LOG).entries())
    typer.echo("Funnel (from data/generation_log.jsonl)")
    typer.echo(f"  generated     {statuses['staged']} drafts")
    typer.echo(f"  sent back     {statuses['check_failed']} replies that failed the checks (auto-fix)")
    typer.echo(f"  verify runs   {statuses['verified_pass']} passed, {statuses['verified_fail']} failed")
    typer.echo(f"  approved      {statuses['approved']}")
    typer.echo(f"  rejected      {statuses['rejected']}")
    typer.echo(f"  API problems  {statuses['error'] + statuses['invalid_reply'] + statuses['quota']}\n")
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
