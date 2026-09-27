"""IDF-weighted overlap of type dependencies from receiver observations.

Faithful port of the Sprint 0 constants pilot, plus a named filter that
drops constants whose last component starts with `inst`.
"""

from __future__ import annotations

import collections
import itertools
import math

TWIN = {
    "LeanFrontier.MarkovTree.isSquare_neg_one_mod_markovNumber",
    "LeanFrontier.MarkovTree.exists_sq_modEq_neg_one_markovNumber",
}
IS_SQUARE = "LeanFrontier.MarkovTree.isSquare_neg_one_mod_markovNumber"
MOD_EQ = "LeanFrontier.MarkovTree.exists_sq_modEq_neg_one_markovNumber"


def is_instance_constant(constant: str) -> bool:
    """True when the last name component uses Lean's `inst` prefix.

    This is a name heuristic. It is not an environment `isInstance` query.
    """
    return constant.rsplit(".", 1)[-1].startswith("inst")


def drop_instance_constants(
    entrypoints: dict[str, frozenset[str]],
) -> dict[str, frozenset[str]]:
    """Drop `inst`-prefixed constants. Entrypoints left with nothing are omitted."""
    kept: dict[str, frozenset[str]] = {}
    for name, deps in entrypoints.items():
        remaining = frozenset(constant for constant in deps if not is_instance_constant(constant))
        if remaining:
            kept[name] = remaining
    return kept


def rank_constants(entrypoints: dict[str, frozenset[str]]) -> dict:
    """Rank every pair by IDF-weighted Jaccard overlap. Report the twin."""
    names = sorted(entrypoints)
    df: collections.Counter[str] = collections.Counter(
        constant for name in names for constant in entrypoints[name]
    )
    count = len(names)
    idf = {constant: math.log(count / freq) for constant, freq in df.items()}

    def weighted_jaccard(left: frozenset[str], right: frozenset[str]) -> float:
        inter = sum(idf[constant] for constant in left & right)
        union = sum(idf[constant] for constant in left | right)
        return inter / union if union else 0.0

    pairs = sorted(
        (
            (weighted_jaccard(entrypoints[left], entrypoints[right]), left, right)
            for left, right in itertools.combinations(names, 2)
        ),
        reverse=True,
    )
    twin_row = None
    if TWIN <= set(names):
        for index, (score, left, right) in enumerate(pairs, start=1):
            if {left, right} == TWIN:
                shared = entrypoints[IS_SQUARE] & entrypoints[MOD_EQ]
                twin_row = {
                    "rank": index,
                    "of": len(pairs),
                    "score": score,
                    "shared_constants": sorted(shared),
                    "only_is_square": sorted(entrypoints[IS_SQUARE] - shared),
                    "only_mod_eq": sorted(entrypoints[MOD_EQ] - shared),
                }
                break
    return {
        "entrypoints": count,
        "pairs": len(pairs),
        "drop_instances": False,
        "twin": twin_row,
        "top": [
            {"score": score, "left": left, "right": right} for score, left, right in pairs[:10]
        ],
    }
