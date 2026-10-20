"""Brute-force checkers for the hearts-or-face-cards family: enumerate combinations of cards."""

from itertools import combinations


def _deck():
    cards = []
    for suit in ["H", "D", "C", "S"]:
        for rank in range(1, 14):
            cards.append((suit, rank >= 11))
    return cards


def solve_root(k):
    deck = _deck()
    count = 0
    for hand in combinations(deck, k):
        all_hearts = all(suit == "H" for suit, _ in hand)
        all_face = all(is_face for _, is_face in hand)
        if all_hearts or all_face:
            count += 1
    return count


def solve_red(k):
    deck = _deck()
    count = 0
    for hand in combinations(deck, k):
        all_red = all(suit in ("H", "D") for suit, _ in hand)
        all_face = all(is_face for _, is_face in hand)
        if all_red or all_face:
            count += 1
    return count


def solve_exclusive(k):
    deck = _deck()
    count = 0
    for hand in combinations(deck, k):
        all_hearts = all(suit == "H" for suit, _ in hand)
        all_face = all(is_face for _, is_face in hand)
        if all_hearts ^ all_face:
            count += 1
    return count
