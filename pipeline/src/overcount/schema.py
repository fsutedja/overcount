"""Authoring schema for problem families (content/families/<slug>/family.json).

These models are the source of truth for what a problem template may contain. `publish.py`
turns a validated family into the web bank format.
"""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .expr import parse
from .taxonomy import Context, Difficulty, Method, MistakeTag, StepKind, Topic
from .visual import VisualType

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
    #: Shown inside the empty box, so it must stay short (the prompt asks for at most 12 characters).
    hint: Annotated[str, Field(min_length=1, max_length=14)]
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
    #: Counting techniques the problem drills, for "practice by method".
    methods: list[Method] = Field(min_length=1)


FunctionName = Annotated[str, Field(pattern=r"^[a-z_][a-z0-9_]*$")]


class Checker(Model):
    """Function names in the family's checker.py (PLAN.md §3, checker convention).

    - outcomes(**vars): every candidate outcome a beginner might write down.
    - counts(outcome, **vars): True if the outcome counts.
    - example(**vars): {"yes": outcome, "no": outcome, "highlight"?, "pool"?, "captions"?}.

    The answer is checked by counting candidates that pass `counts` (a fraction of all of them
    for probabilities). With unequal chances, leave `outcomes` out and add a simulator instead.
    """

    outcomes: FunctionName | None = None
    counts: FunctionName
    example: FunctionName


class Visual(Model):
    type: VisualType


class Example(Model):
    #: Why the yes outcome counts / the no outcome doesn't, e.g. "two 6s", "only one 6".
    yes_reason: Annotated[str, Field(min_length=1, max_length=60)]
    no_reason: Annotated[str, Field(min_length=1, max_length=60)]


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
    #: What one outcome looks like: a ✅ and a ❌ outcome (from the checker) with reasons, drawn
    #: as a small diagram of this type.
    example: Example
    visual: Visual
    checker: Checker
    #: For answers the outcome count can't give (unequal chances, expectations).
    simulator: FunctionName | None = None
    #: Card problems only. "standard" = the usual 52-card deck (13 ranks, 4 suits); "custom" = a
    #: deck the statement describes, allowed only for hard problems (PLAN.md, card problems).
    deck: Literal["standard", "custom"] | None = None

    @model_validator(mode="after")
    def names_are_consistent(self) -> "Problem":
        reserved = RESERVED_NAMES & set(self.variables)
        if reserved:
            raise ValueError(f"variable names {sorted(reserved)} are reserved by the expression grammar")
        texts = [self.statement, self.answer.prompt]
        texts += [m.feedback for m in self.answer.common_wrong + list(self.answer.skeleton.slot_mistakes)]
        texts += [step.title for step in self.solution] + [step.explanation for step in self.solution]
        texts += [self.example.yes_reason, self.example.no_reason]
        unknown = {name for text in texts for name in PLACEHOLDER.findall(text)} - set(self.variables)
        if unknown:
            raise ValueError(f"text uses unknown placeholders {sorted(unknown)}")
        # Any braces left after removing valid placeholders would show up raw on the page.
        malformed = [
            text for text in texts if "{" in PLACEHOLDER.sub("", text) or "}" in PLACEHOLDER.sub("", text)
        ]
        if malformed:
            raise ValueError(f"malformed placeholder (use {{{{x}}}} exactly) in: {malformed[0]!r}")
        if self.simulator is None and self.checker.outcomes is None:
            raise ValueError("checker.outcomes is needed to verify the answer (or add a simulator)")
        if self.simulator is None and self.answer.type == "expectation":
            raise ValueError("expectations can't be counted from outcomes; add a simulator")
        if (self.variant_of is None) != (self.twist is None):
            raise ValueError("variants need both variant_of and twist; root problems need neither")
        expressions = [
            self.answer.expr,
            *(s.expr for s in self.solution),
            *(m.expr for m in self.answer.common_wrong),
        ]
        expressions += [part.expr for part in self.answer.skeleton.parts if isinstance(part, SkeletonGroup)]
        expressions += [slot.answer for slot in self.answer.skeleton.slots.values()]
        for source in expressions:
            clash = parse(source).sum_indices & set(self.variables)
            if clash:
                raise ValueError(
                    f"Σ index {sorted(clash)} in {source!r} reuses a variable name; pick another letter"
                )
        is_cards = "cards-poker" in self.tags.contexts
        if is_cards and self.deck is None:
            raise ValueError('card problems must set "deck" to "standard" or "custom"')
        if not is_cards and self.deck is not None:
            raise ValueError('"deck" is only for card problems (context cards-poker)')
        if self.deck == "custom" and self.difficulty != "hard":
            raise ValueError("a custom deck is only allowed for hard problems; use the standard 52-card deck")
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
