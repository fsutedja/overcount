"""Brute-force checkers for the club-president family: list every (president, advisor) pair."""

from itertools import product


def solve_root(J, S, t):
    members = [("junior", i) for i in range(J)] + [("senior", i) for i in range(S)]
    teachers = list(range(t))
    return sum(1 for _ in product(members, teachers))


def solve_optional_advisor(J, S, t):
    members = [("junior", i) for i in range(J)] + [("senior", i) for i in range(S)]
    advisors = list(range(t)) + [None]
    return sum(1 for _ in product(members, advisors))
