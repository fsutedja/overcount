"""Method lessons ("How it works"): content/methods.yaml → web/public/bank/methods.json.

Each counting method gets one lesson: a summary, how it works, formulas (with when each
applies), a worked example and a common trap. Text marks math with $…$; formulas use the
expression grammar and are published as LaTeX. Every formula is checked by brute force in
tests/test_lessons.py.
"""

import re
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .expr import parse, to_latex
from .taxonomy import METHOD_INFO, METHODS, Method

NonEmpty = Annotated[str, Field(min_length=1)]
_MATH = re.compile(r"\$[^$]*\$")
#: Code notation that must not appear in text outside $…$ (it should be rendered as math).
_CODE = re.compile(r"\^|_|\.\.|\\")


def _plain_text(text: str) -> str:
    if text.count("$") % 2:
        raise ValueError(f"unbalanced $ in {text!r}")
    outside = _MATH.sub("", text)
    if _CODE.search(outside):
        raise ValueError(f"write math inside $…$, not as code notation: {text!r}")
    return text


class Formula(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
    expr: NonEmpty
    #: Makes the formula an identity: expr = equals.
    equals: NonEmpty | None = None
    when: NonEmpty

    @field_validator("expr", "equals")
    @classmethod
    def parses(cls, source: str | None) -> str | None:
        if source is not None:
            parse(source)
        return source

    @field_validator("when")
    @classmethod
    def when_is_text(cls, text: str) -> str:
        return _plain_text(text)


class Lesson(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    summary: NonEmpty
    how: list[NonEmpty] = Field(min_length=1, max_length=4)
    formulas: list[Formula] = Field(min_length=1)
    example: NonEmpty
    trap: NonEmpty

    @field_validator("summary", "example", "trap")
    @classmethod
    def text(cls, value: str) -> str:
        return _plain_text(value)

    @field_validator("how")
    @classmethod
    def paragraphs(cls, values: list[str]) -> list[str]:
        return [_plain_text(v) for v in values]

    @model_validator(mode="after")
    def unique_formula_ids(self) -> "Lesson":
        ids = [f.id for f in self.formulas]
        if len(ids) != len(set(ids)):
            raise ValueError(f"formula ids repeat: {ids}")
        return self


class Lessons(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    methods: dict[Method, Lesson]

    @model_validator(mode="after")
    def one_per_method(self) -> "Lessons":
        missing = sorted(set(METHODS) - set(self.methods))
        if missing:
            raise ValueError(f"every method needs a lesson; missing: {missing}")
        return self


def load_lessons(path: Path) -> Lessons:
    return Lessons.model_validate(yaml.safe_load(path.read_text()))


def _formula_latex(formula: Formula) -> str:
    latex = to_latex(parse(formula.expr), variables="names")
    if formula.equals:
        latex += " = " + to_latex(parse(formula.equals), variables="names")
    return latex


def lessons_json(lessons: Lessons) -> dict[str, Any]:
    """The lessons as published in methods.json, in taxonomy order."""
    return {
        "schema_version": 1,
        "methods": {
            method: {
                "name": METHOD_INFO[method][0],
                "summary": lesson.summary,
                "how": list(lesson.how),
                "formulas": [
                    {"id": f.id, "latex": _formula_latex(f), "when": f.when} for f in lesson.formulas
                ],
                "example": lesson.example,
                "trap": lesson.trap,
            }
            for method in METHODS
            for lesson in [lessons.methods[method]]  # type: ignore[index]
        },
    }
