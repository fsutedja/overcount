"""Checkers for the club-president family. An outcome is [president, advisor].

Juniors are J1, J2, …, seniors S1, S2, …, teachers T1, T2, …; "—" is an empty advisor seat.
"""

from itertools import product


def _students(J, S):
    return [f"J{i}" for i in range(1, J + 1)] + [f"S{i}" for i in range(1, S + 1)]


def _teachers(t):
    return [f"T{i}" for i in range(1, t + 1)]


def _reason(pair):
    president, advisor = pair
    if president == "—":
        return "the club needs a president"
    if president[0] == "T":
        return f"{president} is a teacher; the president is a student"
    if advisor[0] in "JS":
        return f"{advisor} is a student; the advisor is a teacher"
    if advisor == "—":
        return "a student president, no advisor"
    return "a student president, a teacher advisor"


def outcomes_root(J, S, t):
    everyone = _students(J, S) + _teachers(t)
    return product(everyone, everyone)


def counts_root(pair, J, S, t):
    return pair[0][0] in "JS" and pair[1][0] == "T"


def example_root(J, S, t):
    return {"yes": ["J1", "T1"], "no": ["T1", "J1"], "captions": ["president", "advisor"]}


def reason_root(pair, J, S, t):
    return _reason(pair)


def outcomes_optional_advisor(J, S, t):
    everyone = _students(J, S) + _teachers(t)
    return product(everyone, everyone + ["—"])


def counts_optional_advisor(pair, J, S, t):
    return pair[0][0] in "JS" and pair[1][0] in "T—"


def example_optional_advisor(J, S, t):
    return {"yes": ["S1", "—"], "no": ["T1", "—"], "captions": ["president", "advisor"]}


def reason_optional_advisor(pair, J, S, t):
    return _reason(pair)
