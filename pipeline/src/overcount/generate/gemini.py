"""Generates problem families with the Gemini API (free tier).

The API key is read from the environment (loaded from the gitignored .env) and is never logged.
"""

import json
import random
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google import genai
from google.genai import errors, types

from .base import FamilyDraft, Target
from .prompt import PROMPT_VERSION, system_prompt, user_prompt
from .ratelimit import QuotaExhausted, RateLimiter

MAX_ATTEMPTS = 5
RETRYABLE = {429, 500, 502, 503, 504}
TEMPERATURE = 0.7


class InvalidReply(ValueError):
    """The model answered, but not with the JSON object we asked for."""


class ModelUnavailable(RuntimeError):
    """The configured model doesn't exist for this key (e.g. retired); every request would fail."""


def _retry_delay(error: errors.APIError) -> float | None:
    """The server's suggested wait, e.g. RetryInfo {"retryDelay": "37s"}, if it sent one."""
    match = re.search(r'"retryDelay":\s*"(\d+(?:\.\d+)?)s"', json.dumps(error.details or {}))
    return float(match.group(1)) if match else None


def _is_daily_quota(error: errors.APIError) -> bool:
    return error.code == 429 and "PerDay" in json.dumps(error.details or {})


def parse_reply(text: str) -> tuple[dict[str, Any], str]:
    """Extracts {"family": {...}, "checker_code": "..."} from the model's reply."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise InvalidReply(f"reply is not valid JSON: {error.msg} at position {error.pos}") from error
    if not isinstance(data, dict) or not isinstance(data.get("family"), dict):
        raise InvalidReply('reply must be an object with a "family" object')
    if not isinstance(data.get("checker_code"), str) or not data["checker_code"].strip():
        raise InvalidReply('reply must include "checker_code" as a string')
    return data["family"], data["checker_code"]


def stamp(family: dict[str, Any], target: Target, model: str) -> dict[str, Any]:
    """Pins the ids and provenance we control, whatever the model wrote."""
    family["family_id"] = target.id
    problems = family.get("problems")
    if isinstance(problems, list) and problems and all(isinstance(p, dict) for p in problems):
        problems[0]["id"] = target.id
        problems[0].pop("variant_of", None)
        problems[0].pop("twist", None)
        for problem in problems:
            problem["origin"] = {
                "kind": "generated",
                "generator": "gemini",
                "model": model,
                "prompt_version": PROMPT_VERSION,
                "inspired_by": target.inspiration,
            }
        for variant in problems[1:]:
            variant["variant_of"] = target.id
        # Regenerations keep the old variant ids and twists, in order, so saved progress still matches.
        for variant, (variant_id, twist) in zip(problems[1:], target.keep_variants.items(), strict=False):
            variant["id"], variant["twist"] = variant_id, twist
        # Every problem drills the target's methods (the model may add more).
        for problem in problems:
            tags = problem.setdefault("tags", {})
            if isinstance(tags, dict):
                extra = [m for m in tags.get("methods", []) if m not in target.methods]
                tags["methods"] = [*target.methods, *extra]
    return family


@dataclass
class GeminiGenerator:
    client: Any
    model: str
    limiter: RateLimiter
    families_dir: Path
    sleep: Callable[[float], None] = time.sleep
    name: str = "gemini"
    prompt_version: str = PROMPT_VERSION
    _system: str | None = field(default=None, init=False)

    @classmethod
    def from_key(
        cls, api_key: str, model: str, limiter: RateLimiter, families_dir: Path
    ) -> "GeminiGenerator":
        return cls(genai.Client(api_key=api_key), model, limiter, families_dir)

    def generate(self, target: Target) -> FamilyDraft:
        if self._system is None:
            self._system = system_prompt(self.families_dir)
        config = types.GenerateContentConfig(
            system_instruction=self._system,
            response_mime_type="application/json",
            temperature=TEMPERATURE,
        )
        for attempt in range(MAX_ATTEMPTS):
            self.limiter.acquire()
            try:
                response = self.client.models.generate_content(
                    model=self.model, contents=user_prompt(target), config=config
                )
            except errors.APIError as error:
                if _is_daily_quota(error):
                    raise QuotaExhausted("Gemini's daily free-tier quota is used up") from error
                if error.code == 404:
                    raise ModelUnavailable(
                        f"model {self.model!r} is not available: {error.message}"
                    ) from error
                if error.code not in RETRYABLE or attempt == MAX_ATTEMPTS - 1:
                    raise
                # Server hint first; otherwise exponential backoff with jitter.
                self.sleep(_retry_delay(error) or min(60.0, 2.0**attempt + random.uniform(0.5, 1.5)))
                continue
            family, checker_code = parse_reply(response.text or "")
            return FamilyDraft(target.id, stamp(family, target, self.model), checker_code)
        raise RuntimeError("unreachable")
