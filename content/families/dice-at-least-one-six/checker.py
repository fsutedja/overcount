"""Brute-force checkers for the dice-at-least-one-six family."""

from itertools import product


def solve_root(n):
    count = 0
    for roll in product(range(1, 7), repeat=n):
        if 6 in roll:
            count += 1
    return count


def solve_two_or_more(n):
    count = 0
    for roll in product(range(1, 7), repeat=n):
        if roll.count(6) >= 2:
            count += 1
    return count


def solve_no_ones(n):
    count = 0
    for roll in product(range(1, 7), repeat=n):
        if 1 not in roll and 6 in roll:
            count += 1
    return count
