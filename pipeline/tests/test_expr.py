import pytest
import sympy as sp

from overcount.expr import ExprError, display_text, evaluate, parse, stored_value, to_latex

TEAM = {"J": sp.Integer(8), "S": sp.Integer(6), "j": sp.Integer(3), "s": sp.Integer(2)}


@pytest.mark.parametrize(
    ("source", "values", "expected"),
    [
        ("C(J,j)*C(S,s)", TEAM, sp.Integer(840)),
        ("P(J,j)", TEAM, sp.Integer(336)),
        ("(n-1)!", {"n": sp.Integer(5)}, sp.Integer(24)),
        ("n!/n", {"n": sp.Integer(5)}, sp.Integer(24)),
        ("C(13,1)*C(4,3)*C(12,1)*C(4,2)/C(52,5)", {}, sp.Rational(6, 4165)),
        ("(1/6)^3*(5/6)^2", {}, sp.Rational(25, 7776)),
        ("-2+5", {}, sp.Integer(3)),
    ],
)
def test_evaluates_exactly(source: str, values: dict[str, sp.Expr], expected: sp.Expr) -> None:
    assert evaluate(parse(source), values) == expected


def test_e_stays_exact_until_stored() -> None:
    value = evaluate(parse("e^(-2)*2^3/3!"), {})
    assert value == 4 * sp.exp(-2) / 3
    assert stored_value(value) == {"type": "real", "approx": pytest.approx(0.18044704431548358)}


def test_stored_values() -> None:
    assert stored_value(sp.Integer(840)) == {"type": "rational", "exact": "840"}
    assert stored_value(sp.Rational(14, 60)) == {"type": "rational", "exact": "7/30"}


def test_reports_variables_and_slots() -> None:
    expr = parse("C([a],[b])*C(S,s)")
    assert expr.variables == {"S", "s"}
    assert expr.slots == {"a", "b"}
    assert evaluate(expr, {"a": sp.Integer(8), "b": sp.Integer(3), **TEAM}) == 840


@pytest.mark.parametrize(
    ("source", "latex"),
    [
        ("C(J,j)*C(S,s)", r"\binom{ {{J}} }{ {{j}} } \times \binom{ {{S}} }{ {{s}} }"),
        ("C([a],[b])", r"\binom{[a]}{[b]}"),
        ("([a]+[b])*[c]", r"\left([a] + [b]\right) \times [c]"),
        ("(n-1)!", r"\left( {{n}} - 1\right)!"),
        ("n!/n", r"\frac{ {{n}} !}{ {{n}} }"),
        ("(1/6)^3", r"\left(\frac{1}{6}\right)^{3}"),
        ("e^(-2)*2^3/3!", r"\frac{e^{-2} \times 2^{3}}{3!}"),
        ("P(J,j)", r"\operatorname{P}\left( {{J}} , {{j}} \right)"),
        ("a-(b-c)", r"{{a}} - \left( {{b}} - {{c}} \right)"),
    ],
)
def test_latex_follows_the_authored_structure(source: str, latex: str) -> None:
    assert to_latex(parse(source)) == latex


def test_latex_with_plain_names() -> None:
    assert to_latex(parse("C(J,j)"), variables="names") == r"\binom{J}{j}"


@pytest.mark.parametrize(
    "source",
    [
        "import os",
        "__import__('os')",
        "C(1)",
        "f(2)",
        "1.5",
        "a.b",
        "[1,2]",
        "lambda: 1",
        "2 if 1 else 3",
        "a==b",
    ],
)
def test_rejects_anything_outside_the_grammar(source: str) -> None:
    with pytest.raises(ExprError):
        parse(source)


def test_undefined_values_are_rejected() -> None:
    with pytest.raises(ExprError):
        evaluate(parse("1/(n-n)"), {"n": sp.Integer(3)})


def test_display_text() -> None:
    assert display_text("C([a],[b])") == "C([a], [b])"
    assert display_text("[a]*[b]") == "[a] × [b]"


def test_group_latex_keeps_brackets_on_sums() -> None:
    from overcount.expr import to_group_latex

    assert to_group_latex(parse("([a]+[b])")) == r"\left([a] + [b]\right)"
    assert to_group_latex(parse("C([a],[b])")) == r"\binom{[a]}{[b]}"
