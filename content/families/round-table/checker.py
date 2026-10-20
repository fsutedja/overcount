"""Brute-force checkers for the round-table family: list every ordering and count distinct ones."""

from itertools import permutations


def _rotations(order):
    return [order[i:] + order[:i] for i in range(len(order))]


def solve_root(n):
    seen = set()
    for order in permutations(range(n)):
        seen.add(min(_rotations(order)))
    return len(seen)


def solve_mirror(n):
    seen = set()
    for order in permutations(range(n)):
        seen.add(min(_rotations(order) + _rotations(order[::-1])))
    return len(seen)
