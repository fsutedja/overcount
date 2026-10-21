"""One generation run: targets → drafts in staging/, with a resumable log."""

import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from google.genai import errors

from ..verify.gates import verify_family
from .base import FamilyDraft, Feedback, Generator, Target, write_draft
from .gemini import InvalidReply, ModelUnavailable
from .ratelimit import GenerationLog, QuotaExhausted, RateLimiter

#: Times a rejected reply is sent back with the problems found, before the target counts as failed.
MAX_FIXES = 2
#: Problems quoted back to the model per retry.
MAX_PROBLEMS = 12


def check_draft(draft: FamilyDraft) -> list[str]:
    """Runs every verify gate on a draft in a scratch folder; returns the problems (empty = ok).

    This catches missing or wrong examples and visuals right away, so the model can fix them."""
    with tempfile.TemporaryDirectory() as scratch:
        folder = write_draft(draft, Path(scratch))
        report = verify_family(folder)
    problems = []
    for failure in report.failures:
        where = f" [{failure.instance_key}]" if failure.instance_key else ""
        detail = f": {failure.detail.strip()}" if failure.detail and failure.gate == "schema" else ""
        problems.append(f"{failure.gate} · {failure.problem_id}{where}: {failure.message}{detail}")
    return problems[:MAX_PROBLEMS]


@dataclass
class RunResult:
    staged: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    stopped_for_quota: bool = False
    #: Set when the run stopped early because the model can't be used at all.
    stopped_reason: str | None = None


def run_generation(
    generator: Generator,
    limiter: RateLimiter,
    targets: list[Target],
    log: GenerationLog,
    staging_dir: Path,
    existing: set[str],
    limit: int | None = None,
    force: bool = False,
    check: Callable[[FamilyDraft], list[str]] = check_draft,
) -> RunResult:
    """Generates drafts for targets that aren't done yet, stopping at `limit` or the daily quota.

    A target is done if it was staged before (per the log) or a family with its id already exists
    in staging/, needs_review/, or content/. `force` regenerates anyway.

    Each reply is checked at once (`check`: schema plus every verify gate). A rejected or
    unreadable reply is sent back with the problems, up to MAX_FIXES times."""
    result = RunResult()
    done = log.staged_targets() | existing
    for target in targets:
        if not force and target.id in done:
            result.skipped.append(target.id)
            continue
        if limit is not None and len(result.staged) + len(result.failed) >= limit:
            break
        common = {
            "target_id": target.id,
            "model": generator.model,
            "prompt_version": generator.prompt_version,
        }
        feedback: Feedback | None = None
        draft: FamilyDraft | None = None
        before = limiter.made
        stop = False
        for attempt in range(MAX_FIXES + 1):
            last = attempt == MAX_FIXES
            before = limiter.made
            try:
                draft = generator.generate(target, feedback)
            except QuotaExhausted as error:
                log.append(**common, status="quota", requests=limiter.made - before, detail=str(error))
                result.stopped_for_quota = stop = True
                break
            except ModelUnavailable as error:
                log.append(**common, status="error", requests=limiter.made - before, detail=str(error))
                result.stopped_reason = str(error)
                stop = True
                break
            except InvalidReply as error:
                used = limiter.made - before
                log.append(**common, status="invalid_reply", requests=used, detail=str(error))
                draft, feedback = None, Feedback([str(error)])
                if last:
                    result.failed.append((target.id, str(error)))
                continue
            except errors.APIError as error:
                detail = f"API error {error.code}: {error.message}"
                log.append(**common, status="error", requests=limiter.made - before, detail=detail)
                result.failed.append((target.id, detail))
                draft = None
                if error.code is not None and error.code >= 500:
                    # Still failing after the generator's own retries: Gemini is overloaded or
                    # down, so the next targets would only burn requests too. Stop the run.
                    result.stopped_reason = f"Gemini is not responding properly ({detail}); try again later"
                    stop = True
                break
            problems = check(draft)
            if not problems:
                break
            log.append(
                **common, status="check_failed", requests=limiter.made - before, detail="; ".join(problems)
            )
            feedback = Feedback(problems, draft)
            if last:
                summary = f"{len(problems)} problem(s) after {MAX_FIXES} fixes: {problems[0]}"
                result.failed.append((target.id, summary))
                draft = None
        if stop:
            break
        if draft is None:
            continue
        write_draft(draft, staging_dir)
        log.append(**common, status="staged", requests=limiter.made - before)
        result.staged.append(target.id)
    return result
