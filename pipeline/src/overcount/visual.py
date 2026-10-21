"""Visual types for the "one outcome" diagram: what an outcome looks like, and its text form.

An outcome is plain JSON data (lists of numbers and short strings) produced by a family's
checker. Each visual type fixes the outcome's shape, so the web can draw it with one shared
component (web/src/components/OutcomeVisual.tsx) instead of free-form SVG.

`outcome_text` is mirrored in web/src/lib/outcome.ts; the bank cross-check keeps them equal.
"""

from collections.abc import Callable
from typing import Any, Literal, get_args

VisualType = Literal[
    "dice", "coins", "sequence", "circle", "subset", "boxes", "stars-bars", "cards", "path", "matching"
]  # fmt: skip
VISUAL_TYPES: tuple[str, ...] = get_args(VisualType)

#: More pieces than this and the diagram stops being "small".
MAX_PIECES = 12
#: A subset's pool can be a little bigger: chosen pieces are highlighted inside it.
MAX_POOL = 20
MAX_LABEL = 4
MAX_CAPTION = 10

#: Types where order doesn't matter: outcomes are compared as sorted lists.
UNORDERED: frozenset[str] = frozenset({"subset", "cards"})

RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SUITS = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}


def _is_label(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= MAX_LABEL


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _cards_ok(value: Any) -> bool:
    return isinstance(value, str) and value[-1:] in SUITS and value[:-1] in RANKS


def shape_errors(kind: str, outcome: Any) -> list[str]:
    """What's wrong with an outcome for this visual type (empty when it's fine)."""
    if kind not in VISUAL_TYPES:
        return [f"unknown visual type {kind!r}"]
    if not isinstance(outcome, list) or not outcome:
        return [f"a {kind} outcome must be a non-empty list, got {outcome!r}"]
    if len(outcome) > MAX_PIECES:
        return [f"a {kind} outcome has {len(outcome)} pieces; at most {MAX_PIECES} fit in the diagram"]
    checks: dict[str, tuple[Callable[[Any], bool], str]] = {
        "dice": (lambda v: isinstance(v, int) and 1 <= v <= 6, "die faces 1–6"),
        "coins": (lambda v: v in ("H", "T"), '"H" or "T"'),
        "sequence": (_is_label, f"labels of 1–{MAX_LABEL} characters"),
        "circle": (_is_label, f"labels of 1–{MAX_LABEL} characters"),
        "subset": (_is_label, f"labels of 1–{MAX_LABEL} characters"),
        "boxes": (_is_count, "counts ≥ 0"),
        "stars-bars": (_is_count, "counts ≥ 0"),
        "cards": (_cards_ok, 'cards like "AH", "10S", "KD"'),
        "path": (lambda v: v in ("R", "U"), '"R" or "U"'),
        "matching": (_is_count, "spot numbers ≥ 1"),
    }
    item_ok, expected = checks[kind]
    bad = [v for v in outcome if not item_ok(v)]
    if bad:
        return [f"{kind} outcome items must be {expected}; got {bad[0]!r}"]
    if kind == "matching" and sorted(outcome) != list(range(1, len(outcome) + 1)):
        return [f"a matching outcome must use each spot 1..{len(outcome)} once, got {outcome}"]
    if kind in ("subset", "cards", "circle") and len(set(outcome)) != len(outcome):
        return [f"a {kind} outcome can't repeat an item, got {outcome}"]
    if kind in ("stars-bars", "boxes") and sum(outcome) > MAX_PIECES * 2:
        return [f"a {kind} outcome holds {sum(outcome)} items; keep examples small"]
    return []


def example_errors(kind: str, example: Any) -> list[str]:
    """Checks what a checker's example_* function returned (outcomes, highlight, pool, captions)."""
    if not isinstance(example, dict) or not {"yes", "no"} <= set(example):
        return ['example_* must return a dict with "yes" and "no" outcomes']
    extra = set(example) - {"yes", "no", "highlight", "pool", "captions"}
    if extra:
        return [f"example_* returned unknown keys {sorted(extra)}"]
    errors = [f"yes: {e}" for e in shape_errors(kind, example["yes"])]
    errors += [f"no: {e}" for e in shape_errors(kind, example["no"])]
    if errors:
        return errors
    yes = example["yes"]
    highlight = example.get("highlight", [])
    if not isinstance(highlight, list) or not all(_is_count(i) and i < len(yes) for i in highlight):
        errors.append(f"highlight must be positions 0..{len(yes) - 1} in the yes outcome, got {highlight!r}")
    if kind == "subset":
        pool = example.get("pool")
        if not isinstance(pool, list) or not all(_is_label(v) for v in pool) or len(pool) > MAX_POOL:
            errors.append(f"a subset example needs a pool: up to {MAX_POOL} short labels to choose from")
        elif not set(yes) | set(example["no"]) <= set(pool):
            errors.append("subset outcomes must be chosen from the pool")
    elif "pool" in example:
        errors.append("pool is only for subset visuals")
    captions = example.get("captions")
    if captions is not None and (
        not isinstance(captions, list)
        or len(captions) != len(yes)
        or not all(isinstance(c, str) and 1 <= len(c) <= MAX_CAPTION for c in captions)
    ):
        errors.append(f"captions must be one label (≤ {MAX_CAPTION} characters) per piece of the yes outcome")
    return errors


def normalize(kind: str, outcome: Any) -> Any:
    """A comparable form: tuples become lists, and unordered types are sorted."""
    if isinstance(outcome, (list, tuple)):
        items = [normalize(kind, item) for item in outcome]
        return sorted(items, key=repr) if kind in UNORDERED else items
    return outcome


def _card(card: str) -> str:
    return card[:-1] + SUITS[card[-1]]


def outcome_text(kind: str, outcome: list[Any]) -> str:
    """The outcome written out for reading, e.g. "6, 6, 1, 3, 2" or "★★ | ★ | ★★★"."""
    match kind:
        case "circle":
            return " → ".join(outcome) + f" → (back to {outcome[0]})"
        case "subset":
            return "{" + ", ".join(outcome) + "}"
        case "boxes":
            return " | ".join(str(v) for v in outcome)
        case "stars-bars":
            return " | ".join("★" * v if v else "–" for v in outcome)
        case "cards":
            return " ".join(_card(c) for c in outcome)
        case "path":
            return " ".join(outcome)
        case "matching":
            return ", ".join(f"{i}→{spot}" for i, spot in enumerate(outcome, start=1))
        case _:
            return ", ".join(str(v) for v in outcome)
