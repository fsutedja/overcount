"""Checkers for the candy-bags family. An outcome lists how many candies go in each bag."""

from itertools import product


def outcomes(n, k, m=0):
    # Every way to put 0..n candies in each bag; only those adding up to n count.
    return product(range(n + 1), repeat=k)


def _spread(n, k, low):
    # n candies over k bags, each at least `low`, as evenly as possible.
    base, extra = divmod(n - low * k, k)
    return [low + base + (1 if i < extra else 0) for i in range(k)]


def counts_root(bags, n, k):
    return sum(bags) == n


def example_root(n, k):
    yes = [0] + _spread(n, k - 1, 0)
    no = list(yes)
    no[-1] += 1
    return {"yes": yes, "no": no}


def counts_nonempty(bags, n, k):
    return sum(bags) == n and min(bags) >= 1


def example_nonempty(n, k):
    yes = _spread(n, k, 1)
    no = [0] + _spread(n, k - 1, 1)
    return {"yes": yes, "no": no}


def counts_minimum(bags, n, k, m):
    return sum(bags) == n and bags[0] >= m


def example_minimum(n, k, m):
    yes = [m] + _spread(n - m, k - 1, 0)
    no = [m - 1] + _spread(n - m + 1, k - 1, 0)
    return {"yes": yes, "no": no, "highlight": [0]}
