"""Brute-force checkers for the candy-bags family: enumerate all valid distributions."""


def _distributions(candies_left, bags_left, mins):
    if bags_left == 1:
        if candies_left >= mins[0]:
            yield (candies_left,)
        return
    min_here = mins[0]
    min_rest = sum(mins[1:])
    for count in range(min_here, candies_left - min_rest + 1):
        for rest in _distributions(candies_left - count, bags_left - 1, mins[1:]):
            yield (count,) + rest


def solve_root(n, k):
    return sum(1 for _ in _distributions(n, k, [0] * k))


def solve_nonempty(n, k):
    return sum(1 for _ in _distributions(n, k, [1] * k))


def solve_minimum(n, k, m):
    return sum(1 for _ in _distributions(n, k, [m] + [0] * (k - 1)))
