"""TF-IDF similarity of public declarations versus import-graph distance.

Faithful port of the Sprint 0 text pilot. The tokenization and the
similarity cutoff are part of that baseline, not a preregistered H1 score.
"""

from __future__ import annotations

import collections
import itertools
import math
import re

from consilean.ingest.declarations import Declaration
from consilean.ingest.graph import undirected_distances

STOP = set(
    "the a an of to and is in for that its it be by as are on at with this from or any every".split()
    + "theorem lemma def proof using hence thus then".split()
)
SYM = {
    "²": " sq ",
    "³": " cube ",
    "≡": " modeq ",
    "∣": " dvd ",
    "√": " sqrt ",
    "−": " minus ",
    "-1": " negone ",
    "ℤ": " int ",
    "ℕ": " nat ",
    "ℝ": " real ",
    "ℚ": " rat ",
    "∑": " sum ",
    "∏": " prod ",
    "→": " ",
    "↔": " iff ",
}
TWIN_NAMES = {
    "isSquare_neg_one_mod_markovNumber",
    "exists_sq_modEq_neg_one_markovNumber",
}
SIMILARITY_CUTOFF = 0.25


def split_ident(tok: str) -> list[str]:
    parts = re.split(r"[._']", tok)
    out: list[str] = []
    for part in parts:
        out += re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", part)
    return [word.lower() for word in out if word]


def tokens(text: str) -> list[str]:
    for key, value in SYM.items():
        text = text.replace(key, value)
    raw = re.findall(r"[A-Za-z_][A-Za-z0-9_.']*|\d+", text)
    toks: list[str] = []
    for item in raw:
        toks += split_ident(item)
    return [tok for tok in toks if tok not in STOP and len(tok) > 1]


def declaration_text(decl: Declaration) -> str:
    """The string the pilot tokenizes: name, raw docstring, raw signature."""
    return f"{decl.name} {decl.raw_doc} {decl.raw_sig}"


def rank_text(
    decls: list[Declaration],
    distances: dict[str, dict[str, int]],
) -> dict:
    """Cross-module pairs above the pilot cutoff, and where the twin sits."""
    token_lists = [tokens(declaration_text(decl)) for decl in decls]
    df: collections.Counter[str] = collections.Counter()
    for toks in token_lists:
        df.update(set(toks))
    count = len(decls)
    vecs: list[dict[str, float]] = []
    for toks in token_lists:
        tf = collections.Counter(toks)
        weights = {word: (1 + math.log(freq)) * math.log(count / df[word]) for word, freq in tf.items()}
        norm = math.sqrt(sum(value * value for value in weights.values())) or 1.0
        vecs.append({word: value / norm for word, value in weights.items()})

    def cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if len(left) > len(right):
            left, right = right, left
        return sum(value * right.get(word, 0.0) for word, value in left.items())

    pairs: list[tuple[float, float, int, int]] = []
    for i, j in itertools.combinations(range(count), 2):
        left_mod, right_mod = decls[i].module, decls[j].module
        if left_mod == right_mod:
            continue
        score = cosine(vecs[i], vecs[j])
        if score > SIMILARITY_CUTOFF:
            distance = distances[left_mod].get(right_mod, math.inf)
            pairs.append((score, distance, i, j))
    pairs.sort(reverse=True)

    def rows(selected: list[tuple[float, float, int, int]], limit: int) -> list[dict]:
        out = []
        for score, distance, i, j in selected[:limit]:
            out.append(_pair_row(score, distance, decls[i], decls[j]))
        return out

    twin = [
        pair
        for pair in pairs
        if {decls[pair[2]].name, decls[pair[3]].name} == TWIN_NAMES
    ]
    twin_row = None
    if twin:
        score, distance, i, j = twin[0]
        twin_row = _pair_row(score, distance, decls[i], decls[j])
        twin_row["rank"] = pairs.index(twin[0]) + 1
        twin_row["of"] = len(pairs)

    return {
        "public_declarations": count,
        "pairs_above_cutoff": len(pairs),
        "cutoff": SIMILARITY_CUTOFF,
        "twin": twin_row,
        "top_similar": rows(pairs, 15),
        "top_no_import_path": rows([pair for pair in pairs if pair[1] == math.inf], 15),
        "top_distance_at_least_4": rows(
            [pair for pair in pairs if 4 <= pair[1] < math.inf],
            10,
        ),
    }


def distances_for(graph: dict[str, list[str]]) -> dict[str, dict[str, int]]:
    return undirected_distances(graph)


def _pair_row(score: float, distance: float, left: Declaration, right: Declaration) -> dict:
    return {
        "score": score,
        "distance": None if math.isinf(distance) else distance,
        "left": f"{left.module}.{left.name}",
        "right": f"{right.module}.{right.name}",
    }
