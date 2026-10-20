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

TOPICS: tuple[str, ...] = get_args(Topic)
CONTEXTS: tuple[str, ...] = get_args(Context)
MISTAKE_TAGS: tuple[str, ...] = get_args(MistakeTag)
STEP_KINDS: tuple[str, ...] = get_args(StepKind)
