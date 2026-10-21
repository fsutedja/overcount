"""What to generate (targets), what a generator returns (drafts), and where drafts go (staging/)."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml
from pydantic import BaseModel, ConfigDict, Field

from ..schema import Slug
from ..taxonomy import Context, Difficulty, Method, Topic


class Target(BaseModel):
    """One family to generate, from content/targets.yaml."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    #: Becomes the family_id and the root problem's id.
    id: Slug
    topic: Topic
    context: Context
    difficulty: Difficulty
    #: Counting methods every problem in the family drills.
    methods: list[Method] = Field(min_length=1)
    variants: int = Field(default=2, ge=0, le=3)
    #: When regenerating a family: existing variant ids → twists, kept so saved progress still matches.
    keep_variants: dict[Slug, str] = Field(default_factory=dict)
    #: Optional idea or classic problem to adapt; the wording and numbers must be original.
    inspiration: str | None = None
    notes: str | None = None


class TargetsFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    targets: list[Target]


def load_targets(path: Path) -> list[Target]:
    targets = TargetsFile.model_validate(yaml.safe_load(path.read_text())).targets
    ids = [t.id for t in targets]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"duplicate target ids in {path.name}: {sorted(duplicates)}")
    return targets


@dataclass(frozen=True)
class FamilyDraft:
    """A generator's output: family.json content and checker.py source, not yet verified."""

    target_id: str
    family: dict[str, Any]
    checker_code: str


@dataclass(frozen=True)
class Feedback:
    """Why the previous draft was rejected, sent back so the model can fix it."""

    problems: list[str]
    previous: FamilyDraft | None = None


class Generator(Protocol):
    name: str
    model: str
    prompt_version: str

    def generate(self, target: Target, feedback: Feedback | None = None) -> FamilyDraft: ...


_SAFE_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def write_draft(draft: FamilyDraft, staging_dir: Path) -> Path:
    """Writes a draft to staging/<target id>/. The folder name always comes from our own target id,
    never from model output, so a reply can't write outside staging/."""
    if not _SAFE_SLUG.match(draft.target_id):
        raise ValueError(f"unsafe target id {draft.target_id!r}")
    folder = staging_dir / draft.target_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "family.json").write_text(json.dumps(draft.family, indent=2, ensure_ascii=False) + "\n")
    (folder / "checker.py").write_text(draft.checker_code.rstrip() + "\n")
    return folder
