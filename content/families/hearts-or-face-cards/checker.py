"""Checkers for the hearts-or-face-cards family. An outcome is a hand of k cards, like ["KH", "7S"]."""

from itertools import combinations

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
DECK = [rank + suit for suit in "HDCS" for rank in RANKS]


def outcomes(k):
    return combinations(DECK, k)


def _all(hand, test):
    return all(test(card) for card in hand)


def _heart(card):
    return card[-1] == "H"


def _red(card):
    return card[-1] in "HD"


def _face(card):
    return card[:-1] in ("J", "Q", "K")


def _describe(hand, suit_test, suit_name):
    suited, face = _all(hand, suit_test), _all(hand, _face)
    if suited and face:
        return f"all {suit_name} and all face cards"
    if suited:
        return f"all {suit_name}"
    if face:
        return "all face cards"
    return f"not all {suit_name}, not all face cards"


def counts_root(hand, k):
    return _all(hand, _heart) or _all(hand, _face)


def example_root(k):
    yes = ["KC", "QS", "JD", "KS"][:k]
    no = ["KC", "QS", "JD", "KS"][: k - 1] + ["7S"]
    return {"yes": yes, "no": no}


def reason_root(hand, k):
    return _describe(hand, _heart, "hearts")


def counts_red(hand, k):
    return _all(hand, _red) or _all(hand, _face)


def example_red(k):
    yes = ["2H", "9D", "5H", "AD"][:k]
    no = ["2H", "9D", "5H", "AD"][: k - 1] + ["7S"]
    return {"yes": yes, "no": no}


def reason_red(hand, k):
    return _describe(hand, _red, "red cards")


def counts_exclusive(hand, k):
    return _all(hand, _heart) != _all(hand, _face)


def example_exclusive(k):
    yes = ["2H", "9H", "5H"][:k]
    no = ["KH", "QH", "JH"][:k]
    return {"yes": yes, "no": no}


def reason_exclusive(hand, k):
    text = _describe(hand, _heart, "hearts")
    return text + ": both, so excluded" if text.startswith("all hearts and") else text
