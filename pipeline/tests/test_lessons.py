"""Every lesson formula (content/methods.yaml) is checked against a brute-force count."""

import random
from itertools import combinations, permutations, product
from pathlib import Path

import pytest
import sympy as sp

from overcount.expr import evaluate, parse
from overcount.lessons import Lessons, lessons_json, load_lessons

LESSONS = Path(__file__).resolve().parents[2] / "content" / "methods.yaml"


def _distinct_rows(items: list[str]) -> int:
    return len(set(permutations(items)))


def _shares(n: int, k: int, low: int = 0) -> int:
    return sum(1 for split in product(range(n + 1), repeat=k) if sum(split) == n and min(split) >= low)


def _derangements(n: int) -> int:
    return sum(1 for p in permutations(range(n)) if all(p[i] != i for i in range(n)))


def _no_two_adjacent(n: int, k: int) -> int:
    return sum(1 for spots in combinations(range(n), k) if all(b - a > 1 for a, b in zip(spots, spots[1:], strict=False)))


def _rows_apart(n: int, k: int) -> int:
    # Items 0..k-1 are the ones that must not be next to each other.
    return sum(
        1 for p in permutations(range(n)) if all(not (p[i] < k and p[i + 1] < k) for i in range(n - 1))
    )


def _rows_together(n: int, k: int) -> int:
    return sum(
        1
        for p in permutations(range(n))
        if max(p.index(i) for i in range(k)) - min(p.index(i) for i in range(k)) == k - 1
    )


def _seatings(n: int, flips: bool) -> int:
    seen = set()
    for order in permutations(range(n)):
        turns = [order[i:] + order[:i] for i in range(n)]
        if flips:
            turns += [t[::-1] for t in turns]
        seen.add(min(turns))
    return len(seen)


def _partitions(people: int, size: int) -> int:
    """Ways to split `people` into unnamed groups of `size`."""
    seen = set()
    for order in permutations(range(people)):
        groups = frozenset(frozenset(order[i : i + size]) for i in range(0, people, size))
        seen.add(groups)
    return len(seen)


def _paths(a: int, b: int, through: tuple[int, int] | None = None) -> int:
    count = 0
    for steps in set(permutations("R" * a + "U" * b)):
        x = y = 0
        points = {(0, 0)}
        for s in steps:
            x, y = (x + 1, y) if s == "R" else (x, y + 1)
            points.add((x, y))
        count += through is None or through in points
    return count


def _onto(n: int, k: int) -> int:
    return sum(1 for f in product(range(k), repeat=n) if len(set(f)) == k)


def _fewest_forcing(k: int, r: int) -> int:
    """Smallest number of items such that every way into k boxes puts r in one box."""
    items = 1
    while any(max(f.count(b) for b in range(k)) < r for f in product(range(k), repeat=items)):
        items += 1
    return items


def _union_two(a: int, b: int, x: int) -> int:
    first, second = set(range(a)), set(range(a - x, a - x + b))
    return len(first | second)


def _union_three(seed: int) -> tuple[dict[str, int], int]:
    rng = random.Random(seed)
    sets = [set(rng.sample(range(15), rng.randint(3, 9))) for _ in range(3)]
    a, b, c = (len(s) for s in sets)
    x, y, z = len(sets[0] & sets[1]), len(sets[0] & sets[2]), len(sets[1] & sets[2])
    t = len(sets[0] & sets[1] & sets[2])
    return {"a": a, "b": b, "c": c, "x": x, "y": y, "z": z, "t": t}, len(sets[0] | sets[1] | sets[2])


#: formula "method/id" → list of (variables, brute-force count).
CASES: dict[str, list[tuple[dict[str, int], int]]] = {
    "product-sum-rule/product": [({"a": a, "b": b}, len(list(product(range(a), range(b))))) for a, b in [(4, 3), (2, 5)]],
    "product-sum-rule/sum": [({"a": a, "b": b}, len({("A", i) for i in range(a)} | {("B", i) for i in range(b)})) for a, b in [(4, 3), (1, 6)]],
    "permutations/all": [({"n": n}, len(list(permutations(range(n))))) for n in (3, 5)],
    "permutations/some": [({"n": n, "k": k}, len(list(permutations(range(n), k)))) for n, k in [(5, 2), (6, 3)]],
    "combinations/choose": [({"n": n, "k": k}, len(list(combinations(range(n), k)))) for n, k in [(5, 2), (8, 3)]],
    "combinations/from-ordered": [({"n": n, "k": k}, len(list(combinations(range(n), k)))) for n, k in [(5, 2), (7, 4)]],
    "multiset-permutations/two-kinds": [({"a": a, "b": b}, _distinct_rows(["x"] * a + ["y"] * b)) for a, b in [(2, 3), (4, 1)]],
    "multiset-permutations/three-kinds": [({"a": 1, "b": 2, "c": 3}, _distinct_rows(list("BNNAAA")))],
    "stars-and-bars/empty-allowed": [({"n": n, "k": k}, _shares(n, k)) for n, k in [(7, 3), (4, 4)]],
    "stars-and-bars/at-least-one": [({"n": n, "k": k}, _shares(n, k, 1)) for n, k in [(7, 3), (6, 4)]],
    "stars-and-bars/minimums": [({"n": 9, "k": 3, "m": 2}, sum(1 for s in product(range(10), repeat=3) if sum(s) == 9 and s[0] >= 2))],
    "inclusion-exclusion/two": [({"a": a, "b": b, "x": x}, _union_two(a, b, x)) for a, b, x in [(18, 12, 5), (4, 4, 0)]],
    "inclusion-exclusion/three": [_union_three(seed) for seed in (1, 2, 3)],
    "derangements/inclusion-exclusion": [({"n": n}, _derangements(n)) for n in (3, 4, 5)],
    "derangements/short": [({"n": n}, _derangements(n)) for n in (3, 4, 5)],
    "complement/subtract": [({"t": 36, "b": 25}, sum(1 for d in product(range(1, 7), repeat=2) if 6 in d))],
    "complement/dice": [({"n": n}, sum(1 for d in product(range(1, 7), repeat=n) if 6 in d)) for n in (2, 4)],
    "symmetry-relative-order/one-order": [({"n": n, "r": r}, sum(1 for p in permutations(range(n)) if [i for i in p if i < r] == list(range(r)))) for n, r in [(5, 3), (6, 2)]],
    "symmetry-relative-order/a-before-b": [({"n": n}, sum(1 for p in permutations(range(n)) if p.index(0) < p.index(1))) for n in (4, 5)],
    "choose-then-order/row": [({"n": n, "k": k}, len(list(permutations(range(n), k)))) for n, k in [(6, 3), (5, 5)]],
    "choose-then-order/captain": [({"n": n, "k": k}, sum(len(t) for t in combinations(range(n), k))) for n, k in [(9, 4), (5, 2)]],
    "glue-block/block": [({"n": n, "k": k}, _rows_together(n, k)) for n, k in [(6, 2), (5, 3)]],
    "gap-method/distinct": [({"n": n, "k": k}, _rows_apart(n, k)) for n, k in [(7, 3), (5, 2)]],
    "gap-method/positions": [({"n": n, "k": k}, _no_two_adjacent(n, k)) for n, k in [(7, 3), (6, 2)]],
    "restricted-first/not-at-ends": [({"n": n}, sum(1 for p in permutations(range(n)) if p[0] != 0 and p[-1] != 0)) for n in (4, 5)],
    "divide-overcounting/pairs": [({"m": m}, _partitions(2 * m, 2)) for m in (2, 3)],
    "divide-overcounting/groups": [({"a": a, "g": g}, _partitions(a * g, a)) for a, g in [(2, 3), (3, 2)]],
    "circular/table": [({"n": n}, _seatings(n, flips=False)) for n in (4, 5)],
    "circular/bracelet": [({"n": n}, _seatings(n, flips=True)) for n in (4, 5)],
    "lattice-paths/corner": [({"a": a, "b": b}, _paths(a, b)) for a, b in [(4, 3), (2, 2)]],
    "lattice-paths/through": [({"a": 4, "b": 3, "c": 2, "d": 1}, _paths(4, 3, (2, 1)))],
    "balls-into-boxes/any": [({"n": n, "k": k}, len(list(product(range(k), repeat=n)))) for n, k in [(4, 3), (3, 2)]],
    "balls-into-boxes/onto": [({"n": n, "k": k}, _onto(n, k)) for n, k in [(4, 3), (5, 2)]],
    "balls-into-boxes/identical": [({"n": n, "k": k}, _shares(n, k)) for n, k in [(4, 3), (5, 2)]],
    "pigeonhole/two": [({"k": k}, _fewest_forcing(k, 2)) for k in (2, 3, 4)],
    "pigeonhole/r": [({"k": k, "r": r}, _fewest_forcing(k, r)) for k, r in [(2, 3), (3, 3)]],
    "binomial-identities/pascal": [({"n": n, "k": k}, len(list(combinations(range(n), k)))) for n, k in [(6, 2), (7, 4)]],
    "binomial-identities/row-sum": [({"n": n}, sum(1 for _ in product((0, 1), repeat=n))) for n in (3, 5)],
    "binomial-identities/vandermonde": [({"a": a, "b": b, "k": k}, len(list(combinations(range(a + b), k)))) for a, b, k in [(4, 3, 3), (2, 5, 4)]],
}  # fmt: skip


def lessons() -> Lessons:
    return load_lessons(LESSONS)


def all_formulas() -> list[tuple[str, str, str | None]]:
    return [
        (f"{method}/{formula.id}", formula.expr, formula.equals)
        for method, lesson in lessons().methods.items()
        for formula in lesson.formulas
    ]


def test_every_formula_has_a_brute_force_check() -> None:
    assert sorted(key for key, _, _ in all_formulas()) == sorted(CASES)


@pytest.mark.parametrize(
    ("key", "expr", "equals"), all_formulas(), ids=lambda v: v if isinstance(v, str) else ""
)
def test_formula_matches_brute_force(key: str, expr: str, equals: str | None) -> None:
    for variables, expected in CASES[key]:
        values = {name: sp.Integer(v) for name, v in variables.items()}
        assert evaluate(parse(expr), values) == expected, (key, variables)
        if equals:
            assert evaluate(parse(equals), values) == expected, (key, variables, "right-hand side")


def test_lessons_publish_rendered_math() -> None:
    data = lessons_json(lessons())
    assert list(data["methods"])[0] == "product-sum-rule"
    stars = data["methods"]["stars-and-bars"]
    assert stars["name"] == "Stars and bars"
    assert stars["formulas"][0]["latex"] == r"\binom{n + k - 1}{k - 1}"


@pytest.mark.parametrize(
    "text",
    ["uses 2^n here", "a sum k=0..n", "an index x_1", "unbalanced $n"],
)
def test_lesson_text_must_render_its_math(text: str) -> None:
    raw = {"methods": {m: lessons().methods[m].model_dump() for m in lessons().methods}}
    raw["methods"]["pigeonhole"]["trap"] = text
    with pytest.raises(ValueError):
        Lessons.model_validate(raw)
