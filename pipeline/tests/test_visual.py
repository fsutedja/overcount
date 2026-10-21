from typing import Any

import pytest

from overcount.visual import example_errors, normalize, outcome_text, shape_errors


@pytest.mark.parametrize(
    ("kind", "outcome", "text"),
    [
        ("dice", [6, 6, 1, 3, 2], "6, 6, 1, 3, 2"),
        ("coins", ["H", "T"], "H, T"),
        ("sequence", ["J1", "T1"], "J1, T1"),
        ("circle", ["A", "B", "C"], "A → B → C → (back to A)"),
        ("subset", ["J1", "S2"], "{J1, S2}"),
        ("boxes", [2, 0, 3], "2 | 0 | 3"),
        ("stars-bars", [2, 0, 3], "★★ | – | ★★★"),
        ("cards", ["AH", "10S"], "A♥ 10♠"),
        ("path", ["R", "U", "R"], "R U R"),
        ("matching", [2, 1, 3], "1→2, 2→1, 3→3"),
    ],
)
def test_text_forms(kind: str, outcome: list[Any], text: str) -> None:
    assert shape_errors(kind, outcome) == []
    assert outcome_text(kind, outcome) == text


@pytest.mark.parametrize(
    ("kind", "outcome", "message"),
    [
        ("dice", [7], "1–6"),
        ("dice", list(range(1, 7)) * 3, "at most"),
        ("cards", ["1H"], "cards like"),
        ("matching", [1, 1], "each spot"),
        ("circle", ["A", "A"], "repeat"),
        ("doodle", [1], "unknown"),
        ("coins", [], "non-empty"),
    ],
)
def test_shape_errors(kind: str, outcome: list[Any], message: str) -> None:
    assert any(message in e for e in shape_errors(kind, outcome))


def test_example_errors() -> None:
    assert example_errors("dice", {"yes": [6], "no": [1], "highlight": [0]}) == []
    assert example_errors("dice", {"yes": [6]})
    assert any("positions" in e for e in example_errors("dice", {"yes": [6], "no": [1], "highlight": [3]}))
    assert any("pool" in e for e in example_errors("subset", {"yes": ["A"], "no": ["B"]}))
    assert any("captions" in e for e in example_errors("dice", {"yes": [6], "no": [1], "captions": []}))


def test_unordered_types_compare_sorted() -> None:
    assert normalize("cards", ("KH", "2S")) == normalize("cards", ["2S", "KH"])
    assert normalize("dice", (6, 1)) != normalize("dice", [1, 6])
