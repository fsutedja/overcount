"""One generation run: targets → drafts in staging/, with a resumable log."""

from dataclasses import dataclass, field
from pathlib import Path

from google.genai import errors

from .base import Generator, Target, write_draft
from .gemini import InvalidReply, ModelUnavailable
from .ratelimit import GenerationLog, QuotaExhausted, RateLimiter


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
) -> RunResult:
    """Generates drafts for targets that aren't done yet, stopping at `limit` or the daily quota.

    A target is done if it was staged before (per the log) or a family with its id already exists
    in staging/, needs_review/, or content/. `force` regenerates anyway."""
    result = RunResult()
    done = log.staged_targets() | existing
    for target in targets:
        if not force and target.id in done:
            result.skipped.append(target.id)
            continue
        if limit is not None and len(result.staged) + len(result.failed) >= limit:
            break
        before = limiter.made
        common = {
            "target_id": target.id,
            "model": generator.model,
            "prompt_version": generator.prompt_version,
        }
        try:
            draft = generator.generate(target)
        except QuotaExhausted as error:
            log.append(**common, status="quota", requests=limiter.made - before, detail=str(error))
            result.stopped_for_quota = True
            break
        except ModelUnavailable as error:
            log.append(**common, status="error", requests=limiter.made - before, detail=str(error))
            result.stopped_reason = str(error)
            break
        except InvalidReply as error:
            log.append(**common, status="invalid_reply", requests=limiter.made - before, detail=str(error))
            result.failed.append((target.id, str(error)))
            continue
        except errors.APIError as error:
            detail = f"API error {error.code}: {error.message}"
            log.append(**common, status="error", requests=limiter.made - before, detail=detail)
            result.failed.append((target.id, detail))
            continue
        write_draft(draft, staging_dir)
        log.append(**common, status="staged", requests=limiter.made - before)
        result.staged.append(target.id)
    return result
