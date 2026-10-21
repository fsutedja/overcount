import copy
import json
from pathlib import Path
from typing import Any

import pytest
import sympy as sp
from pydantic import ValidationError

from overcount.cli import REPO_ROOT
from overcount.instances import build_instances
from overcount.publish import build_bank, stale_files
from overcount.schema import Family

CONTENT = REPO_ROOT / "content"


def golden(family_id: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((CONTENT / "families" / family_id / "family.json").read_text())
    return data


def test_golden_families_validate() -> None:
    for path in (CONTENT / "families").glob("*/family.json"):
        Family.model_validate_json(path.read_text())


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda p: p["variables"].update({"C": {"min": 1, "max": 2, "default": 1}}), "reserved"),
        (lambda p: p.update({"statement": "Pick {{x}} people."}), "unknown placeholders"),
        (lambda p: p["answer"]["skeleton"]["slots"].pop("d"), "skeleton uses slots"),
        (lambda p: p["answer"]["skeleton"]["parts"].append({"op": "*"}), "end with a group"),
        (lambda p: p.pop("checker"), "checker or a simulator"),
        (lambda p: p["answer"]["common_wrong"][0].update({"mistake_tag": "made-up"}), "mistake_tag"),
        (lambda p: p["tags"].update({"topics": []}), "topics"),
        (lambda p: p["variables"]["J"].update({"default": 99}), "outside"),
    ],
)
def test_schema_rejects_broken_problems(change: Any, message: str) -> None:
    family = copy.deepcopy(golden("committee-mixed"))
    change(family["problems"][0])
    with pytest.raises(ValidationError, match=message):
        Family.model_validate(family)


def test_variants_must_point_at_the_root() -> None:
    family = copy.deepcopy(golden("committee-mixed"))
    family["problems"][1]["variant_of"] = "something-else"
    with pytest.raises(ValidationError, match="variant_of"):
        Family.model_validate(family)


def test_instances_start_with_the_default_and_respect_constraints() -> None:
    problem = Family.model_validate(golden("committee-mixed")).problems[0]
    instances = build_instances(problem)
    assert instances[0].key == "J=8,S=6,j=3,s=2"
    assert instances[0].values["answer"] == {"type": "rational", "exact": "840"}
    assert len(instances) == 100
    assert len({i.key for i in instances}) == 100
    for instance in instances:
        values = {k: sp.Integer(v) for k, v in instance.vars.items()}
        assert values["j"] < values["J"] and values["s"] < values["S"]
        expected = sp.binomial(values["J"], values["j"]) * sp.binomial(values["S"], values["s"])
        assert instance.values["answer"] == {"type": "rational", "exact": str(expected)}


def test_instances_are_deterministic() -> None:
    problem = Family.model_validate(golden("club-president")).problems[0]
    assert [i.key for i in build_instances(problem)] == [i.key for i in build_instances(problem)]


def test_build_matches_the_committed_bank() -> None:
    bank = build_bank(CONTENT)
    assert stale_files(bank, REPO_ROOT / "web" / "public" / "bank") == []


def test_bank_skeleton_groups_keep_brackets(tmp_path: Path) -> None:
    bank = build_bank(CONTENT)
    family = json.loads(bank.files["families/club-president.json"])
    group = family["problems"][0]["answer"]["skeleton"]["parts"][0]["group"]
    assert group == {"label": "president", "display": "([a] + [b])", "latex": r"\left([a] + [b]\right)"}


def card_problem(**changes: Any) -> dict[str, Any]:
    family = copy.deepcopy(golden("hearts-or-face-cards"))
    family["problems"] = family["problems"][:1]
    family["problems"][0].update(changes)
    return family


def test_card_problems_must_declare_their_deck() -> None:
    family = card_problem()
    family["problems"][0].pop("deck")
    with pytest.raises(ValidationError, match="must set"):
        Family.model_validate(family)


def test_custom_decks_are_only_for_hard_problems() -> None:
    with pytest.raises(ValidationError, match="only allowed for hard"):
        Family.model_validate(card_problem(deck="custom", difficulty="medium"))
    Family.model_validate(card_problem(deck="custom", difficulty="hard"))


def test_deck_is_only_for_card_problems() -> None:
    family = copy.deepcopy(golden("committee-mixed"))
    family["problems"][0]["deck"] = "standard"
    with pytest.raises(ValidationError, match="only for card problems"):
        Family.model_validate(family)


def test_sum_index_may_not_reuse_a_variable() -> None:
    family = copy.deepcopy(golden("round-table"))
    family["problems"][0]["answer"]["expr"] = "Sum(1, n, 1, n)"
    with pytest.raises(ValidationError, match="reuses a variable"):
        Family.model_validate(family)
