"""Digest and normal-form lookup. Cosine is stored and is not a gate."""

from __future__ import annotations

import hashlib
from collections import defaultdict

from consilean.ingest.declarations import Declaration
from consilean.views.syntax import formula_graph, normal_form, parse_statement
from consilean.views.wl import cosine, wl_features


def digest(signature: str) -> str:
    text = " ".join(signature.split())
    return hashlib.sha256(text.encode()).hexdigest()


class Index:
    """Exact-digest and normal-form postings for one or more corpora."""

    def __init__(self) -> None:
        self.by_digest: dict[str, list[dict]] = defaultdict(list)
        self.by_normal: dict[str, list[dict]] = defaultdict(list)
        self._features: dict[tuple[str, str, str], object] = {}
        self._queries: dict[str, object] = {}

    def add(self, corpus: str, declarations: list[Declaration]) -> None:
        for decl in declarations:
            ref = {
                "corpus": corpus,
                "module": decl.module,
                "name": decl.name,
                "raw_sig": decl.raw_sig,
            }
            self.by_digest[digest(decl.raw_sig)].append(ref)
            form = normal_form(decl.raw_sig)
            if form is not None:
                self.by_normal[form].append(ref)

    def matches(self, signature: str) -> list[dict]:
        """Every posting that matches by digest or normal form."""
        found: list[dict] = []
        seen: set[tuple[str, str, str, str]] = set()
        query_digest = digest(signature)
        for ref in self.by_digest.get(query_digest, []):
            row = _row(ref, "exact_digest", self._cosine(signature, ref))
            found.append(row)
            seen.add(_key(ref))
        form = normal_form(signature)
        if form is None:
            return found
        for ref in self.by_normal.get(form, []):
            if _key(ref) in seen:
                continue
            found.append(_row(ref, "normal_form", self._cosine(signature, ref)))
        return found

    def _query_features(self, signature: str):
        if signature not in self._queries:
            self._queries[signature] = _features(signature)
        return self._queries[signature]

    def _cosine(self, signature: str, ref: dict) -> float | None:
        left = self._query_features(signature)
        right = self._ref_features(ref)
        if left is None or right is None:
            return None
        return cosine(left, right)

    def _ref_features(self, ref: dict):
        key = (ref["corpus"], ref["module"], ref["name"])
        if key not in self._features:
            self._features[key] = _features(ref["raw_sig"])
        return self._features[key]


def partner_rank(index: Index, transported: str, partner: dict) -> int | None:
    """Rank of one declaration among normal-form matches of `transported`.

    A digest match is rank 1. Otherwise the partner must share the normal
    form. Ties do not push it down.
    """
    if digest(transported) == digest(partner["raw_sig"]):
        return 1
    form = normal_form(transported)
    if form is None or normal_form(partner["raw_sig"]) != form:
        return None
    if len(index.by_normal.get(form, [])) == 1:
        return 1
    query = index._query_features(transported)
    partner_features = index._ref_features(partner)
    if query is None or partner_features is None:
        return None
    partner_cosine = cosine(query, partner_features)
    better = 0
    for other in index.by_normal.get(form, []):
        if _key(other) == _key(partner):
            continue
        other_features = index._ref_features(other)
        if other_features is not None and cosine(query, other_features) > partner_cosine:
            better += 1
    return better + 1


def _features(signature: str):
    statement = parse_statement(signature)
    if statement is None:
        return None
    return wl_features(*formula_graph(statement, keep_names=False))


def _key(ref: dict) -> tuple[str, str, str]:
    return (ref["corpus"], ref["module"], ref["name"])


def _row(ref: dict, via: str, score: float | None) -> dict:
    return {
        "corpus": ref["corpus"],
        "module": ref["module"],
        "name": ref["name"],
        "via": via,
        "cosine": score,
    }
