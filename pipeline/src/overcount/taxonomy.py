"""Fixed vocabularies for problem tags, mistake tags, and solution step kinds (see PLAN.md §2a)."""

from typing import Literal, get_args

Difficulty = Literal["easy", "medium", "hard"]

Topic = Literal[
    "counting/basics",
    "counting/permutations",
    "counting/combinations",
    "counting/stars-bars",
    "counting/complement",
    "counting/inclusion-exclusion",
    "counting/symmetry-circular",
    "probability/basics",
    "probability/independence",
    "probability/expectation",
    "probability/conditional-bayes",
    "distributions/binomial",
    "distributions/hypergeometric",
    "distributions/geometric",
    "distributions/poisson",
]

Context = Literal["cards-poker", "dice", "balls-urns", "committees-seating"]

MistakeTag = Literal[
    "order-confusion",
    "overcount",
    "undercount",
    "add-vs-multiply",
    "missed-complement",
    "replacement-confusion",
    "wrong-distribution",
    "independence-assumed",
    "conditional-reversed",
    "off-by-one",
]

StepKind = Literal[
    "choose",
    "arrange",
    "combine",
    "cases",
    "inclusion-exclusion",
    "complement",
    "overcount",
    "condition",
    "distribution",
]

#: Counting techniques for "practice by method". A problem has one or more.
Method = Literal[
    "product-sum-rule",
    "permutations",
    "combinations",
    "multiset-permutations",
    "stars-and-bars",
    "inclusion-exclusion",
    "derangements",
    "complement",
    "symmetry-relative-order",
    "choose-then-order",
    "glue-block",
    "gap-method",
    "restricted-first",
    "divide-overcounting",
    "circular",
    "lattice-paths",
    "balls-into-boxes",
    "pigeonhole",
    "binomial-identities",
]

#: Display name and one-line description for each method, in the order they're listed.
METHOD_INFO: dict[str, tuple[str, str]] = {
    "product-sum-rule": (
        "Product and sum rules",
        "Multiply for steps that all happen, add for either/or cases.",
    ),
    "permutations": ("Permutations", "Ordered arrangements: n! and P(n, k)."),
    "combinations": ("Combinations", "Unordered selections: C(n, k)."),
    "multiset-permutations": ("Repeated items", "Arrangements with repeats: n! / (a! b! …)."),
    "stars-and-bars": (
        "Stars and bars",
        "Identical items into distinct boxes: empty allowed, at least one, minimums.",
    ),
    "inclusion-exclusion": ("Inclusion–exclusion", "Add the groups, subtract the overlaps."),
    "derangements": ("Derangements", "Nothing ends up in its own place: Σ (−1)^k / k!."),
    "complement": ("Complement", "Count everything, then subtract what you don't want."),
    "symmetry-relative-order": ("Symmetry", "Every relative order is equally likely, e.g. 11! / 3."),
    "choose-then-order": ("Choose, then order", "Pick who, then arrange them."),
    "glue-block": ("Glue into a block", "Items that must be together move as one."),
    "gap-method": ("Gap method", "Place the others first, then fill the gaps so items stay apart."),
    "restricted-first": ("Restricted first", "Place the fussy items first, then the rest."),
    "divide-overcounting": (
        "Divide out overcounting",
        "Count with labels, then divide by the orderings that don't matter.",
    ),
    "circular": ("Circular arrangements", "Around a table: fix one seat or divide by rotations."),
    "lattice-paths": ("Lattice paths", "Paths on a grid: choose which steps go right."),
    "balls-into-boxes": ("Balls into boxes", "Distinct or identical balls into distinct boxes."),
    "pigeonhole": ("Pigeonhole", "More items than boxes forces a repeat."),
    "binomial-identities": ("Binomial identities", "Count one thing two ways to prove an identity."),
}

TOPICS: tuple[str, ...] = get_args(Topic)
METHODS: tuple[str, ...] = get_args(Method)
CONTEXTS: tuple[str, ...] = get_args(Context)
MISTAKE_TAGS: tuple[str, ...] = get_args(MistakeTag)
STEP_KINDS: tuple[str, ...] = get_args(StepKind)

Kind = Literal["counting", "probability"]


def kind_of(primary_topic: str) -> Kind:
    """Counting or Probability, derived from the primary topic (distributions count as probability)."""
    return "counting" if primary_topic.startswith("counting/") else "probability"
