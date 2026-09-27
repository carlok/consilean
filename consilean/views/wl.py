"""Weisfeiler–Lehman features over a formula graph.

The round update is the one in euclean's `pipeline/views/kernels.py`
(MIT, Carlo Perassi): hash a node label with its sorted, edge-labelled
neighbourhood, and pool every round. Pair similarity is the cosine of
those count vectors. euclean then builds a sparse matrix and an SVD;
this sprint only needs the pairwise kernel, so that part is not copied.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter


def wl_features(
    labels: list[str],
    adj: list[list[tuple[str, int]]],
    rounds: int = 3,
) -> Counter[str]:
    """Multiset of subtree labels from round 0 through `rounds`."""
    current = list(labels)
    pooled: Counter[str] = Counter(f"r0:{label}" for label in current)
    for round_index in range(1, rounds + 1):
        nxt: list[str] = []
        for index, label in enumerate(current):
            neigh = sorted(f"{edge}:{current[other]}" for edge, other in adj[index])
            nxt.append(_hash(label + "|" + ",".join(neigh)))
        current = nxt
        pooled.update(f"r{round_index}:{label}" for label in current)
    return pooled


def cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    dot = sum(value * right.get(key, 0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def _hash(text: str) -> str:
    return hashlib.blake2s(text.encode(), digest_size=8).hexdigest()
