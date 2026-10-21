"""Checkers for the candy-bags family. An outcome lists how many candies go in bags A, B, C, …"""

from itertools import product


def outcomes(n, k, m=0):
    # Every way to fill the bags with n candies, plus near misses (one candy too few or too
    # many), so the ❌ examples are mistakes a learner might really make.
    for bags in product(range(n + 2), repeat=k):
        if abs(sum(bags) - n) <= 1:
            yield bags


def _spread(n, k, low):
    # n candies over k bags, each at least `low`, as evenly as possible.
    base, extra = divmod(n - low * k, k)
    return [low + base + (1 if i < extra else 0) for i in range(k)]


def _bags(k):
    return [chr(ord("A") + i) for i in range(k)]


def _total(bags, n):
    total = sum(bags)
    return None if total == n else f"adds to {total}, not {n}"


def counts_root(bags, n, k):
    return sum(bags) == n


def example_root(n, k):
    yes = [0] + _spread(n, k - 1, 0)
    no = list(yes)
    no[-1] += 1
    return {"yes": yes, "no": no, "captions": _bags(k)}


def reason_root(bags, n, k):
    if _total(bags, n):
        return _total(bags, n)
    return f"adds to {n}; an empty bag is fine" if 0 in bags else f"adds to {n}"


def counts_nonempty(bags, n, k):
    return sum(bags) == n and min(bags) >= 1


def example_nonempty(n, k):
    return {"yes": _spread(n, k, 1), "no": [0] + _spread(n, k - 1, 1), "captions": _bags(k)}


def reason_nonempty(bags, n, k):
    if 0 in bags:
        return f"bag {_bags(k)[list(bags).index(0)]} is empty"
    return _total(bags, n) or f"adds to {n}, every bag has some"


def counts_minimum(bags, n, k, m):
    return sum(bags) == n and bags[0] >= m


def example_minimum(n, k, m):
    yes = [m] + _spread(n - m, k - 1, 0)
    no = [m - 1] + _spread(n - m + 1, k - 1, 0)
    return {"yes": yes, "no": no, "captions": ["gold"] + _bags(k)[1:]}


def highlight_minimum(bags, n, k, m):
    return [0]


def reason_minimum(bags, n, k, m):
    if bags[0] < m:
        return f"the gold bag has only {bags[0]}, needs {m}"
    return _total(bags, n) or f"adds to {n}, gold bag has {bags[0]}"
