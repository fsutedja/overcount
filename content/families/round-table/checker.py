"""Checkers for the round-table family.

An outcome is the order of people (or beads) going clockwise, starting from the top seat. Every
ordering is a candidate; only one ordering per seating counts, the one that starts with A.
"""

from itertools import permutations

LETTERS = "ABCDEFGH"


def outcomes(n):
    return permutations(LETTERS[:n])


def _from_a(order):
    order = list(order)
    i = order.index("A")
    return order[i:] + order[:i]


def highlight(order, n):
    return [list(order).index("A")]


def counts_root(order, n):
    return order[0] == "A"


def example_root(n):
    yes = list(LETTERS[:n])
    return {"yes": yes, "no": yes[1:] + yes[:1]}


def reason_root(order, n):
    if order[0] == "A":
        return "one seating, read clockwise from A"
    return f"same as {''.join(_from_a(order))}, turned"


def counts_mirror(order, n):
    # Starts with A, and of the two directions, the one where B comes before … is kept.
    return order[0] == "A" and order[1] < order[-1]


def example_mirror(n):
    yes = list(LETTERS[:n])
    return {"yes": yes, "no": yes[:1] + yes[1:][::-1]}


def reason_mirror(order, n):
    if counts_mirror(order, n):
        return "one bracelet, read clockwise from A"
    turned = _from_a(order)
    flipped = turned[1] > turned[-1]
    if flipped:
        turned = turned[:1] + turned[1:][::-1]
    how = "flipped over" if order[0] == "A" else ("turned and flipped" if flipped else "turned")
    return f"same as {''.join(turned)}, {how}"
