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
        (lambda p: p["checker"].pop("reason"), "reason"),
        (lambda p: p.pop("visual"), "visual"),
        (lambda p: p["visual"].update({"type": "doodle"}), "visual.type"),
        (lambda p: p["visual"].update({"legend": "x" * 71}), "legend"),
        (lambda p: p["checker"].pop("outcomes"), "add a simulator"),
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
    assert group == {"label": "president", "latex": r"\left([a] + [b]\right)"}


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


def test_roadmap_gives_every_topic_and_method_one_home() -> None:
    from overcount.roadmap import Roadmap, load_roadmap

    roadmap = load_roadmap(CONTENT / "roadmap.yaml")
    assert sum(len(n.methods) for n in roadmap.nodes) == 19
    data = roadmap.model_dump()
    data["nodes"][1]["methods"].append("permutations")  # already in counting-basics
    with pytest.raises(ValidationError, match="exactly one"):
        Roadmap.model_validate(data)
    data["nodes"][1]["methods"].pop()
    data["nodes"][0]["methods"].remove("circular")
    with pytest.raises(ValidationError, match="missing"):
        Roadmap.model_validate(data)


def derangement_family(**slot_answers: str) -> dict[str, Any]:
    """Round-table, rewritten as "nobody in their own seat" with the unsimplified Σ skeleton."""
    family = copy.deepcopy(golden("round-table"))
    family["problems"] = family["problems"][:1]
    problem = family["problems"][0]
    answers = {"e": "k", "a": "n", "b": "k", "c": "n-k", "lo": "0", "hi": "n"} | slot_answers
    problem["answer"].update(
        {
            "expr": "n!*Sum((-1)^k/k!, k, 0, n)",
            "common_wrong": [],
            "skeleton": {
                "parts": [
                    {"group": "inclusion–exclusion", "expr": "Sum((-1)^[e]*C([a],[b])*([c])!, k, [lo], [hi])"}
                ],
                "slots": {slot: {"answer": answer} for slot, answer in answers.items()},
            },
        }
    )
    problem["solution"][-1]["expr"] = "n!*Sum((-1)^k/k!, k, 0, n)"
    return family


def test_slots_inside_a_sum_can_hold_expressions_in_the_index() -> None:
    problem = Family.model_validate(derangement_family()).problems[0]
    first = build_instances(problem)[0]
    assert first.values["answer"] == {"type": "rational", "exact": "265"}  # n = 6
    assert first.values["slot.c"] == {"type": "indexed", "latex": "6 - k", "index": "k"}
    assert first.values["slot.e"] == {"type": "indexed", "latex": "k", "index": "k"}
    assert first.values["slot.lo"] == {"type": "rational", "exact": "0"}


def test_only_slots_inside_a_sum_may_use_its_index() -> None:
    with pytest.raises(ValidationError, match="unknown names"):
        Family.model_validate(derangement_family(hi="n+k"))


def test_a_skeleton_that_does_not_equal_the_answer_is_rejected() -> None:
    problem = Family.model_validate(derangement_family(c="n-k+1")).problems[0]
    with pytest.raises(ValueError, match="skeleton filled with its slot answers"):
        build_instances(problem)


def test_help_check_works_out_the_smallest_case() -> None:
    from overcount.help_check import help_check

    folder = REPO_ROOT / "content" / "families" / "round-table"
    problem = Family.model_validate_json((folder / "family.json").read_text()).problems[0]
    check = help_check(problem, build_instances(problem), folder / "checker.py")
    assert check["vars"] == {"n": "4"}
    assert (check["filled"], check["worked"]) == (r"{4}! \div {4}", r"24 \div 4")
    assert check["answer"] == {"type": "rational", "exact": "6"}
    assert len(check["outcomes"]) == 6 and check["outcomes"][0].startswith("A → B → C → D")


def test_help_check_lists_the_terms_of_a_sum() -> None:
    from overcount.help_check import help_check

    problem = Family.model_validate(derangement_family()).problems[0]
    folder = REPO_ROOT / "content" / "families" / "round-table"
    check = help_check(problem, build_instances(problem), folder / "checker.py")
    assert check["vars"] == {"n": "4"}
    assert check["worked"] == "24 - 24 + 12 - 4 + 1"  # = 9 derangements of 4
    assert "outcomes" not in check  # 9 is more than we list


def test_roadmap_after_must_point_to_earlier_stops() -> None:
    import yaml

    from overcount.roadmap import Roadmap

    data = yaml.safe_load((REPO_ROOT / "content" / "roadmap.yaml").read_text())
    data["nodes"][0]["after"] = ["combinations"]
    with pytest.raises(ValidationError, match="earlier stops"):
        Roadmap.model_validate(data)


@pytest.mark.parametrize(
    ("groups", "visual_type", "message"),
    [
        ([{"label": "hearts", "suits": ["X"]}], "cards", "unknown suits"),
        ([{"label": "nothing"}], "cards", "needs suits, ranks"),
        ([{"label": "hearts", "suits": ["H"]}], "dice", "only for the cards visual"),
    ],
)
def test_deck_groups_are_checked(groups: list[dict[str, Any]], visual_type: str, message: str) -> None:
    from overcount.schema import Visual

    with pytest.raises(ValidationError, match=message):
        Visual.model_validate({"type": visual_type, "deck_groups": groups})
