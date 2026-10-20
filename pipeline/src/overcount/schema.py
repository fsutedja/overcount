"""Authoring schema for problem families (content/families/<slug>/family.json).

These models are the source of truth for what a problem template may contain. `publish.py`
turns a validated family into the web bank format.
"""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .taxonomy import Context, Difficulty, MistakeTag, StepKind, Topic

PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")
SLOT_MARKER = re.compile(r"\[(\w+)\]")
#: Names that mean something in the expression grammar and can't be variables.
RESERVED_NAMES = {"C", "P", "e"}

Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
VariableName = Annotated[str, Field(pattern=r"^[A-Za-z][0-9]?$")]
NonEmpty = Annotated[str, Field(min_length=1)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class IntRange(Model):
    min: int
    max: int
    default: int

    @model_validator(mode="after")
    def default_in_range(self) -> "IntRange":
        if not self.min <= self.default <= self.max:
            raise ValueError(f"default {self.default} is outside {self.min}..{self.max}")
        return self


class ValueSet(Model):
    """A variable that takes one of a few listed values, e.g. probabilities ["1/6", "1/2"]."""

    values: list[NonEmpty] = Field(min_length=1)
    default: NonEmpty

    @model_validator(mode="after")
    def default_listed(self) -> "ValueSet":
        if self.default not in self.values:
            raise ValueError(f"default {self.default!r} is not one of {self.values}")
        return self


Variable = IntRange | ValueSet


class Mistake(Model):
    """A predictable wrong answer, recognised by value, with feedback that names the mistake."""

    expr: NonEmpty
    feedback: NonEmpty
    mistake_tag: MistakeTag


class SlotMistake(Mistake):
    slot: NonEmpty


class SkeletonGroup(Model):
    """A labelled part of the Help skeleton, e.g. {"group": "juniors", "expr": "C([a],[b])"}."""

    group: NonEmpty
    expr: NonEmpty


class SkeletonOp(Model):
    op: Literal["*", "+", "-", "/"]


class Slot(Model):
    hint: NonEmpty
    #: Expression in the problem's variables giving this slot's value, e.g. "J".
    answer: NonEmpty


class Skeleton(Model):
    parts: list[SkeletonGroup | SkeletonOp] = Field(min_length=1)
    slots: dict[str, Slot] = Field(min_length=1)
    slot_mistakes: list[SlotMistake] = []

    @model_validator(mode="after")
    def parts_and_slots_line_up(self) -> "Skeleton":
        for index, part in enumerate(self.parts):
            expect_group = index % 2 == 0
            if expect_group != isinstance(part, SkeletonGroup):
                raise ValueError(
                    "skeleton parts must alternate group, op, group, … and start and end with a group"
                )
        if isinstance(self.parts[-1], SkeletonOp):
            raise ValueError("skeleton parts must end with a group")
        used = [
            m
            for part in self.parts
            if isinstance(part, SkeletonGroup)
            for m in SLOT_MARKER.findall(part.expr)
        ]
        if len(used) != len(set(used)):
            raise ValueError(f"each slot may appear only once in the skeleton, got {used}")
        if set(used) != set(self.slots):
            raise ValueError(f"skeleton uses slots {sorted(used)} but defines {sorted(self.slots)}")
        unknown = {m.slot for m in self.slot_mistakes} - set(self.slots)
        if unknown:
            raise ValueError(f"slot_mistakes refer to unknown slots {sorted(unknown)}")
        return self


class Answer(Model):
    prompt: NonEmpty
    expr: NonEmpty
    #: What the answer measures; used to sanity-check every instance's value.
    type: Literal["count", "probability", "expectation"] = "count"
    common_wrong: list[Mistake] = []
    skeleton: Skeleton


class SolutionStep(Model):
    kind: StepKind
    title: NonEmpty
    expr: NonEmpty
    explanation: NonEmpty


class Tags(Model):
    #: The first topic is the primary one: it places the problem on the roadmap.
    topics: list[Topic] = Field(min_length=1)
    contexts: list[Context] = Field(min_length=1)


class Origin(Model):
    kind: Literal["authored", "generated"]
    generator: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    inspired_by: str | None = None


class Problem(Model):
    id: Slug
    variant_of: Slug | None = None
    #: Short description of how a variant differs, shown as a chip, e.g. "at least one senior".
    twist: str | None = None
    schema_version: Literal[1] = 1
    origin: Origin
    title: NonEmpty
    statement: NonEmpty
    variables: dict[VariableName, Variable] = Field(min_length=1)
    #: sympy relationals over the variables, e.g. "j < J".
    constraints: list[str] = []
    difficulty: Difficulty
    tags: Tags
    answer: Answer
    solution: list[SolutionStep] = Field(min_length=1)
    #: Function names in the family's checker.py. A problem needs at least one way to be verified.
    checker: str | None = None
    simulator: str | None = None

    @model_validator(mode="after")
    def names_are_consistent(self) -> "Problem":
        reserved = RESERVED_NAMES & set(self.variables)
        if reserved:
            raise ValueError(f"variable names {sorted(reserved)} are reserved by the expression grammar")
        texts = [self.statement, self.answer.prompt]
        texts += [m.feedback for m in self.answer.common_wrong + list(self.answer.skeleton.slot_mistakes)]
        texts += [step.title for step in self.solution] + [step.explanation for step in self.solution]
        unknown = {name for text in texts for name in PLACEHOLDER.findall(text)} - set(self.variables)
        if unknown:
            raise ValueError(f"text uses unknown placeholders {sorted(unknown)}")
        if self.checker is None and self.simulator is None:
            raise ValueError("a problem needs a checker or a simulator so it can be verified")
        if (self.variant_of is None) != (self.twist is None):
            raise ValueError("variants need both variant_of and twist; root problems need neither")
        return self


class Family(Model):
    family_id: Slug
    problems: list[Problem] = Field(min_length=1)

    @model_validator(mode="after")
    def root_and_variants(self) -> "Family":
        root, *variants = self.problems
        if root.id != self.family_id or root.variant_of is not None:
            raise ValueError("the first problem must be the root, with id equal to family_id")
        for variant in variants:
            if variant.variant_of != self.family_id:
                raise ValueError(f"variant {variant.id} must have variant_of = {self.family_id!r}")
        ids = [p.id for p in self.problems]
        if len(ids) != len(set(ids)):
            raise ValueError(f"problem ids must be unique within a family, got {ids}")
        return self
