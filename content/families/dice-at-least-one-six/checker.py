"""Checkers for the dice-at-least-one-six family. An outcome is the list of n rolls, in order."""

from itertools import product

COUNT_WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven"]


def outcomes(n):
    return product(range(1, 7), repeat=n)


def _filler(n):
    # Rolls without a 6, e.g. 1, 2, 3, 4, 5, 1, …
    return [i % 5 + 1 for i in range(n)]


def _sixes(roll):
    count = list(roll).count(6)
    return COUNT_WORDS[count] + (" 6" if count == 1 else " 6s")


def highlight(roll, n):
    return [i for i, face in enumerate(roll) if face == 6]


def counts_root(roll, n):
    return 6 in roll


def example_root(n):
    yes = _filler(n)
    yes[1] = 6
    return {"yes": yes, "no": _filler(n)}


def reason_root(roll, n):
    return "it has a 6" if 6 in roll else "no 6 at all"


def counts_two_or_more(roll, n):
    return list(roll).count(6) >= 2


def example_two_or_more(n):
    yes, no = _filler(n), _filler(n)
    yes[0] = yes[1] = 6
    no[0] = 6
    return {"yes": yes, "no": no}


def reason_two_or_more(roll, n):
    return ("only " if list(roll).count(6) == 1 else "") + _sixes(roll)


def counts_no_ones(roll, n):
    return 1 not in roll and 6 in roll


def example_no_ones(n):
    yes = [i % 4 + 2 for i in range(n)]
    yes[0] = 6
    no = list(yes)
    no[1] = 1
    return {"yes": yes, "no": no}


def reason_no_ones(roll, n):
    if 1 in roll:
        return "it has a 1"
    return "no 1s and a 6" if 6 in roll else "no 6 at all"
