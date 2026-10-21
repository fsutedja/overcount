"""Checkers for the round-table family.

An outcome is the order of people (or beads) going clockwise, starting from the top seat. Every
ordering is a candidate; only one ordering per seating counts, the one that starts with A.
"""

from itertools import permutations

LETTERS = "ABCDEFGH"


def outcomes(n):
    return permutations(LETTERS[:n])


def counts_root(order, n):
    return order[0] == "A"


def example_root(n):
    yes = list(LETTERS[:n])
    return {"yes": yes, "no": yes[1:] + yes[:1], "highlight": [0]}


def counts_mirror(order, n):
    # Starts with A, and of the two directions, the one where B comes before … is kept.
    return order[0] == "A" and order[1] < order[-1]


def example_mirror(n):
    yes = list(LETTERS[:n])
    return {"yes": yes, "no": yes[:1] + yes[1:][::-1], "highlight": [0]}
