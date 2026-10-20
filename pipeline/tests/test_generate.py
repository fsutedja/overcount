import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from google.genai import errors

from overcount.cli import FAMILIES_DIR
from overcount.generate.base import FamilyDraft, Target, write_draft
from overcount.generate.gemini import GeminiGenerator, InvalidReply, parse_reply, stamp
from overcount.generate.ratelimit import GenerationLog, QuotaExhausted, RateLimiter
from overcount.generate.run import run_generation

TARGET = Target(id="candy-bags", topic="counting/stars-bars", context="balls-urns", difficulty="easy")
GOLDEN = json.loads((FAMILIES_DIR / "round-table" / "family.json").read_text())
REPLY = json.dumps({"family": GOLDEN, "checker_code": "def solve_root(n):\n    return 1\n"})


def quota_error(per_day: bool, retry_delay: str | None = None) -> errors.ClientError:
    details: list[dict[str, Any]] = [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
         "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier" if per_day
                         else "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"}]},
    ]  # fmt: skip
    if retry_delay:
        details.append({"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay})
    return errors.ClientError(429, {"error": {"code": 429, "message": "quota", "details": details}})


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeModels:
    """Plays back a script of replies (strings) and errors, recording each request."""

    def __init__(self, script: list[str | Exception]) -> None:
        self.script: Iterator[str | Exception] = iter(script)
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        step = next(self.script)
        if isinstance(step, Exception):
            raise step
        return FakeResponse(step)


class FakeClient:
    def __init__(self, script: list[str | Exception]) -> None:
        self.models = FakeModels(script)


def make_generator(
    script: list[str | Exception], rpd: int = 100
) -> tuple[GeminiGenerator, FakeClient, list[float]]:
    retry_sleeps: list[float] = []
    limiter = RateLimiter(
        requests_per_minute=600, requests_per_day=rpd, clock=lambda: 0.0, sleep=lambda _: None
    )
    client = FakeClient(script)
    generator = GeminiGenerator(client, "gemini-test", limiter, FAMILIES_DIR, sleep=retry_sleeps.append)
    return generator, client, retry_sleeps


# --- reply parsing ----------------------------------------------------------------------------------


def test_parses_a_plain_or_fenced_reply() -> None:
    family, code = parse_reply(REPLY)
    assert family["family_id"] == "round-table" and code.startswith("def solve_root")
    assert parse_reply(f"```json\n{REPLY}\n```")[0] == family


@pytest.mark.parametrize("text", ["not json", "[]", '{"family": {}}', '{"family": {}, "checker_code": ""}'])
def test_rejects_malformed_replies(text: str) -> None:
    with pytest.raises(InvalidReply):
        parse_reply(text)


def test_stamp_pins_ids_and_provenance() -> None:
    family = stamp(json.loads(json.dumps(GOLDEN)), TARGET, "gemini-test")
    root, variant = family["problems"]
    assert family["family_id"] == root["id"] == "candy-bags"
    assert "variant_of" not in root and variant["variant_of"] == "candy-bags"
    assert root["origin"] == {
        "kind": "generated",
        "generator": "gemini",
        "model": "gemini-test",
        "prompt_version": "family-v1",
        "inspired_by": None,
    }


def test_drafts_are_written_under_our_own_target_id(tmp_path: Path) -> None:
    folder = write_draft(FamilyDraft("candy-bags", {"family_id": "x"}, "def f():\n    return 1"), tmp_path)
    assert folder == tmp_path / "candy-bags"
    assert (folder / "checker.py").read_text().endswith("return 1\n")
    with pytest.raises(ValueError):
        write_draft(FamilyDraft("../escape", {}, ""), tmp_path)


# --- rate limiting and retries ----------------------------------------------------------------------


def test_limiter_spaces_requests_and_enforces_the_daily_budget() -> None:
    sleeps: list[float] = []
    limiter = RateLimiter(
        requests_per_minute=10, requests_per_day=2, used_today=0, clock=lambda: 0.0, sleep=sleeps.append
    )
    limiter.acquire()
    limiter.acquire()
    assert sleeps == [6.0]
    with pytest.raises(QuotaExhausted):
        limiter.acquire()


def test_retries_a_rate_limit_using_the_server_delay() -> None:
    generator, client, sleeps = make_generator([quota_error(per_day=False, retry_delay="37s"), REPLY])
    draft = generator.generate(TARGET)
    assert draft.family["family_id"] == "candy-bags"
    assert len(client.models.calls) == 2
    assert 37.0 in sleeps


def test_backs_off_on_server_errors() -> None:
    server_error = errors.ServerError(503, {"error": {"code": 503, "message": "overloaded"}})
    generator, client, sleeps = make_generator([server_error, server_error, REPLY])
    generator.generate(TARGET)
    assert len(client.models.calls) == 3
    assert len(sleeps) == 2 and all(0 < s <= 60 for s in sleeps)


def test_stops_on_the_daily_quota() -> None:
    generator, _, _ = make_generator([quota_error(per_day=True)])
    with pytest.raises(QuotaExhausted):
        generator.generate(TARGET)


def test_does_not_retry_a_bad_request() -> None:
    bad = errors.ClientError(400, {"error": {"code": 400, "message": "bad model"}})
    generator, client, _ = make_generator([bad])
    with pytest.raises(errors.ClientError):
        generator.generate(TARGET)
    assert len(client.models.calls) == 1


def test_sends_the_system_prompt_and_asks_for_json() -> None:
    generator, client, _ = make_generator([REPLY])
    generator.generate(TARGET)
    config = client.models.calls[0]["config"]
    assert config.response_mime_type == "application/json"
    assert "committee-mixed" in config.system_instruction
    assert "target id: candy-bags" in client.models.calls[0]["contents"]


# --- runs -------------------------------------------------------------------------------------------

TARGETS = [
    TARGET,
    Target(id="dice-at-least-one-six", topic="counting/complement", context="dice", difficulty="easy"),
    Target(
        id="hearts-or-face-cards",
        topic="counting/inclusion-exclusion",
        context="cards-poker",
        difficulty="medium",
    ),
]


def test_run_stages_drafts_and_logs_them(tmp_path: Path) -> None:
    generator, _, _ = make_generator([REPLY, "oops, not json", REPLY])
    log = GenerationLog(tmp_path / "log.jsonl")
    result = run_generation(generator, generator.limiter, TARGETS, log, tmp_path / "staging", set())
    assert result.staged == ["candy-bags", "hearts-or-face-cards"]
    assert [t for t, _ in result.failed] == ["dice-at-least-one-six"]
    assert (tmp_path / "staging" / "candy-bags" / "family.json").exists()
    assert [e["status"] for e in log.entries()] == ["staged", "invalid_reply", "staged"]
    assert log.requests_today() == 3


def test_run_resumes_and_respects_the_limit(tmp_path: Path) -> None:
    log = GenerationLog(tmp_path / "log.jsonl")
    log.append(target_id="candy-bags", status="staged", requests=1)
    generator, client, _ = make_generator([REPLY, REPLY])
    result = run_generation(
        generator, generator.limiter, TARGETS, log, tmp_path, {"hearts-or-face-cards"}, limit=5
    )
    assert result.skipped == ["candy-bags", "hearts-or-face-cards"]
    assert result.staged == ["dice-at-least-one-six"]
    assert len(client.models.calls) == 1


def test_run_stops_cleanly_when_the_quota_runs_out(tmp_path: Path) -> None:
    generator, _, _ = make_generator([REPLY, quota_error(per_day=True)])
    log = GenerationLog(tmp_path / "log.jsonl")
    result = run_generation(generator, generator.limiter, TARGETS, log, tmp_path, set())
    assert result.staged == ["candy-bags"] and result.stopped_for_quota
    assert log.entries()[-1]["status"] == "quota"


def test_run_stops_at_once_when_the_model_is_unavailable(tmp_path: Path) -> None:
    gone = errors.ClientError(404, {"error": {"code": 404, "message": "model retired"}})
    generator, client, _ = make_generator([gone])
    log = GenerationLog(tmp_path / "log.jsonl")
    result = run_generation(generator, generator.limiter, TARGETS, log, tmp_path, set())
    assert result.stopped_reason is not None and "gemini-test" in result.stopped_reason
    assert len(client.models.calls) == 1
    assert result.staged == [] and result.failed == []
