"""Brute-force checkers for the committee-mixed family: enumerate every team and count."""

from itertools import combinations


def _teams(J, S, j, s):
    people = [("junior", i) for i in range(J)] + [("senior", i) for i in range(S)]
    for team in combinations(people, j + s):
        if sum(1 for kind, _ in team if kind == "junior") == j:
            yield team


def solve_root(J, S, j, s):
    return sum(1 for _ in _teams(J, S, j, s))


def solve_captain(J, S, j, s):
    count = 0
    for team in _teams(J, S, j, s):
        count += sum(1 for kind, _ in team if kind == "junior")
    return count
