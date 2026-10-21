"""Checkers for the committee-mixed family. Juniors are J1, J2, …; seniors are S1, S2, …"""

from itertools import combinations


def _people(J, S):
    return [f"J{i}" for i in range(1, J + 1)] + [f"S{i}" for i in range(1, S + 1)]


def _juniors(team):
    return sum(1 for person in team if person[0] == "J")


def outcomes_root(J, S, j, s):
    # Any j + s people; only teams with exactly j juniors count.
    return combinations(_people(J, S), j + s)


def counts_root(team, J, S, j, s):
    return _juniors(team) == j


def example_root(J, S, j, s):
    yes = [f"J{i}" for i in range(1, j + 1)] + [f"S{i}" for i in range(1, s + 1)]
    no = [f"J{i}" for i in range(1, j + 2)] + [f"S{i}" for i in range(1, s)]
    return {"yes": yes, "no": no, "pool": _people(J, S)}


def outcomes_captain(J, S, j, s):
    # A team written captain first, then the other members in order.
    for team in combinations(_people(J, S), j + s):
        for captain in team:
            yield [captain] + [p for p in team if p != captain]


def counts_captain(order, J, S, j, s):
    return _juniors(order) == j and order[0][0] == "J"


def example_captain(J, S, j, s):
    team = [f"J{i}" for i in range(1, j + 1)] + [f"S{i}" for i in range(1, s + 1)]
    senior_first = ["S1"] + [p for p in team if p != "S1"]
    captions = ["captain"] + ["member"] * (len(team) - 1)
    return {"yes": team, "no": senior_first, "highlight": [0], "captions": captions}
