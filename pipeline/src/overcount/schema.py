"""Authoring schema for problem families (content/families/<slug>/family.json).

These models are the source of truth for what a problem template may contain. `publish.py`
turns a validated family into the web bank format.
"""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .expr import parse, slot_indices, unblanked_numbers
from .lessons import plain_text
from .taxonomy import Context, Difficulty, Method, MistakeTag, StepKind, Topic
from .visual import RANKS, SUITS, VisualType

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
    #: Blanks are empty boxes: a hint inside the box would give the answer away. The group's label
    #: underneath says what that part counts.
    #: Expression in the problem's variables giving this slot's value, e.g. "J".
    answer: NonEmpty


class Skeleton(Model):
    parts: list[SkeletonGroup | SkeletonOp] = Field(min_length=1)
    slots: dict[str, Slot] = Field(min_length=1)
    slot_mistakes: list[SlotMistake] = []

    @property
    def source(self) -> str:
        """The whole skeleton as one expression, joined the same way the web app grades it."""
        ops = {"*": "*", "+": "+", "-": "-", "/": "/"}
        return " ".join(part.expr if isinstance(part, SkeletonGroup) else ops[part.op] for part in self.parts)

    @property
    def slot_indices(self) -> dict[str, str]:
        """Slots inside a Σ body → its index letter (their answers may use it, e.g. `n-k`)."""
        found: dict[str, str] = {}
        for part in self.parts:
            if isinstance(part, SkeletonGroup):
                found |= slot_indices(parse(part.expr))
        return found

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
        for part in self.parts:
            if isinstance(part, SkeletonGroup):
                fixed = unblanked_numbers(parse(part.expr))
                if fixed:
                    raise ValueError(f"skeleton group {part.group!r} ({part.expr}): {'; '.join(fixed)}")
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


class HelpStep(Model):
    """One numbered "why" step of Help, revealed one at a time before the skeleton.

    Written with letters (n, k), not this problem's numbers, so it teaches the idea and leaves
    the arithmetic to the learner. Text marks math with $…$."""

    kind: StepKind
    title: NonEmpty
    text: NonEmpty
    #: Optional formula in letters, e.g. "C(n, k)*(n-k)!", shown under the text.
    expr: NonEmpty | None = None

    @field_validator("title", "text")
    @classmethod
    def readable(cls, value: str) -> str:
        if PLACEHOLDER.search(value):
            raise ValueError("Help steps use letters (n, k), not {{x}} placeholders")
        return plain_text(value)

    @field_validator("expr")
    @classmethod
    def parses(cls, source: str | None) -> str | None:
        if source is not None:
            parse(source)
        return source


class SolutionStep(Model):
    """One step of "Show solution": the computation with this problem's numbers. The reasoning
    lives in help_steps, so an explanation is optional (and not shown)."""

    kind: StepKind
    title: NonEmpty
    expr: NonEmpty
    explanation: NonEmpty | None = None


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
    - example(**vars): {"yes": outcome, "no": outcome, "pool"?, "captions"?}, hand-picked.
    - reason(outcome, **vars): a one-line reason for any outcome ("two 6s", "only one 6").
    - highlight(outcome, **vars): optional; positions to highlight (e.g. where the 6s are).

    The answer is checked by counting candidates that pass `counts` (a fraction of all of them
    for probabilities). With unequal chances, leave `outcomes` out and add a simulator instead.
    """

    outcomes: FunctionName | None = None
    counts: FunctionName
    example: FunctionName
    reason: FunctionName
    highlight: FunctionName | None = None


class DeckGroup(Model):
    """A set of cards shaded on the card-deck grid (DESIGN.md, D11), e.g. hearts or face cards.

    A card is in the group if its suit is in `suits` (when given) and its rank in `ranks`
    (when given)."""

    label: Annotated[str, Field(min_length=1, max_length=20)]
    suits: list[str] = []
    ranks: list[str] = []

    @model_validator(mode="after")
    def known_cards(self) -> "DeckGroup":
        if not self.suits and not self.ranks:
            raise ValueError("a deck group needs suits, ranks, or both")
        bad = [s for s in self.suits if s not in SUITS] + [r for r in self.ranks if r not in RANKS]
        if bad:
            raise ValueError(f"unknown suits or ranks {bad}; use H D C S and A 2 … 10 J Q K")
        return self


class Visual(Model):
    type: VisualType
    #: One short line explaining the pieces, e.g. "● = a cookie, | = a divider between kids".
    legend: Annotated[str, Field(min_length=1, max_length=70)] | None = None
    #: Card problems only: up to two groups to shade on the 13×4 deck grid (D11).
    deck_groups: list[DeckGroup] = Field(default_factory=list, max_length=2)

    @model_validator(mode="after")
    def groups_only_for_cards(self) -> "Visual":
        if self.deck_groups and self.type != "cards":
            raise ValueError("deck_groups are only for the cards visual")
        return self


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
    #: Help: numbered "why" steps that build up to the skeleton (CLAUDE.md, Product).
    help_steps: list[HelpStep] = Field(min_length=2, max_length=5)
    solution: list[SolutionStep] = Field(min_length=1)
    #: How one outcome is drawn. The ✅/❌ outcomes and their reasons come from the checker.
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
        texts += [step.title for step in self.solution]
        texts += [step.explanation for step in self.solution if step.explanation]
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
        indices = self.answer.skeleton.slot_indices
        for slot, spec in self.answer.skeleton.slots.items():
            allowed = set(self.variables) | ({indices[slot]} if slot in indices else set())
            unknown = parse(spec.answer).variables - allowed
            if unknown:
                where = f" (only the Σ index {indices[slot]!r} may be added)" if slot in indices else ""
                raise ValueError(
                    f"slot {slot!r} answer {spec.answer!r} uses unknown names {sorted(unknown)}{where}"
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
