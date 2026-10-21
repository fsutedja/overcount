"""Checkers for the dice-at-least-one-six family. An outcome is the list of n rolls, in order."""

from itertools import product


def outcomes(n):
    return product(range(1, 7), repeat=n)


def _filler(n):
    # Rolls without a 6, e.g. 1, 2, 3, 4, 5, 1, …
    return [i % 5 + 1 for i in range(n)]


def counts_root(roll, n):
    return 6 in roll


def example_root(n):
    yes = _filler(n)
    yes[1] = 6
    return {"yes": yes, "no": _filler(n), "highlight": [1]}


def counts_two_or_more(roll, n):
    return list(roll).count(6) >= 2


def example_two_or_more(n):
    yes, no = _filler(n), _filler(n)
    yes[0] = yes[1] = 6
    no[0] = 6
    return {"yes": yes, "no": no, "highlight": [0, 1]}


def counts_no_ones(roll, n):
    return 1 not in roll and 6 in roll


def example_no_ones(n):
    yes = [i % 4 + 2 for i in range(n)]
    yes[0] = 6
    no = list(yes)
    no[1] = 1
    return {"yes": yes, "no": no, "highlight": [0]}
