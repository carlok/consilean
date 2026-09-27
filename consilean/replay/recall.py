"""Recall at k for a frozen pair set.

For each frozen pair, the partner's rank is one plus the number of other
declarations that score strictly higher against the old declaration.
Normal-form matches sort above non-matches. Within a normal-form class the
order is the name-free Weisfeiler–Lehman cosine. That is the neighbor order
induced by the preregistered primary score. Ties do not push the partner down.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from consilean.ingest.declarations import Declaration
from consilean.views.syntax import formula_graph, normal_form, parse_statement
from consilean.views.wl import cosine, wl_features

KS = (1, 5, 10, 50)


def aggregate(outcomes: list[dict], parsed_declarations: int) -> dict:
    """Turn per-pair outcomes into the recall table."""
    hits = {k: 0 for k in KS}
    evaluated = 0
    unparsed = 0
    missing = 0
    ranks: list[int | None] = []
    for item in outcomes:
        if item["status"] == "missing":
            missing += 1
            continue
        evaluated += 1
        if item["status"] == "unparsed":
            unparsed += 1
            ranks.append(None)
            continue
        rank = item["rank"]
        ranks.append(rank)
        for k in KS:
            if rank <= k:
                hits[k] += 1
    return {
        "frozen_pairs": len(outcomes),
        "evaluated": evaluated,
        "missing_declaration": missing,
        "unparsed": unparsed,
        "parsed_declarations": parsed_declarations,
        "parsed_ranks": ranks,
        "recovered": hits,
        "recall": {str(k): (hits[k] / evaluated if evaluated else None) for k in KS},
        "primary_k": 10,
    }


def pair_outcomes(declarations: list[Declaration], pairs: list[dict]) -> tuple[int, list[dict]]:
    """Rank each pair once. Later windows reuse the same snapshot views."""
    views = [_view(decl) for decl in declarations]
    index = {f"{decl.module}.{decl.name}": i for i, decl in enumerate(declarations)}
    nf_groups: dict[str, list[int]] = defaultdict(list)
    for i, (nf, _wl) in enumerate(views):
        if nf is not None:
            nf_groups[nf].append(i)
    postings, norms = _postings(views)
    parsed = sum(1 for _nf, wl in views if wl is not None)
    outcomes = []
    for pair in pairs:
        old = index.get(pair["old"])
        new = index.get(pair["new"])
        if old is None or new is None:
            outcomes.append({**pair, "status": "missing"})
            continue
        if views[old][1] is None or views[new][1] is None:
            outcomes.append({**pair, "status": "unparsed"})
            continue
        rank = _partner_rank(old, new, views, nf_groups, postings, norms)
        outcomes.append({**pair, "status": "ranked", "rank": rank})
    return parsed, outcomes


def recall_at_k(
    declarations: list[Declaration],
    pairs: list[dict],
) -> dict:
    views = [_view(decl) for decl in declarations]
    index = {f"{decl.module}.{decl.name}": i for i, decl in enumerate(declarations)}
    nf_groups: dict[str, list[int]] = defaultdict(list)
    for i, (nf, _wl) in enumerate(views):
        if nf is not None:
            nf_groups[nf].append(i)
    postings, norms = _postings(views)
    hits = {k: 0 for k in KS}
    evaluated = 0
    unparsed = 0
    missing = 0
    parsed_ranks: list[int | None] = []
    for pair in pairs:
        old = index.get(pair["old"])
        new = index.get(pair["new"])
        if old is None or new is None:
            missing += 1
            continue
        evaluated += 1
        if views[old][1] is None or views[new][1] is None:
            unparsed += 1
            parsed_ranks.append(None)
            continue
        rank = _partner_rank(old, new, views, nf_groups, postings, norms)
        parsed_ranks.append(rank)
        for k in KS:
            if rank <= k:
                hits[k] += 1
    parsed_declarations = sum(1 for _nf, wl in views if wl is not None)
    return {
        "frozen_pairs": len(pairs),
        "evaluated": evaluated,
        "missing_declaration": missing,
        "unparsed": unparsed,
        "parsed_declarations": parsed_declarations,
        "parsed_ranks": parsed_ranks,
        "recovered": hits,
        "recall": {str(k): (hits[k] / evaluated if evaluated else None) for k in KS},
        "primary_k": 10,
    }


def _view(decl: Declaration) -> tuple[str | None, Counter[str] | None]:
    if parse_statement(decl.raw_sig) is None:
        return None, None
    return normal_form(decl.raw_sig), wl_features(*formula_graph(parse_statement(decl.raw_sig), keep_names=False))


def _postings(views: list[tuple[str | None, Counter[str] | None]]):
    postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
    norms: list[float] = []
    for i, (_nf, counts) in enumerate(views):
        if not counts:
            norms.append(0.0)
            continue
        norm = sum(value * value for value in counts.values()) ** 0.5
        norms.append(norm)
        for feature, value in counts.items():
            postings[feature].append((i, value))
    return postings, norms


def _partner_rank(
    old: int,
    new: int,
    views: list[tuple[str | None, Counter[str] | None]],
    nf_groups: dict[str, list[int]],
    postings: dict[str, list[tuple[int, int]]],
    norms: list[float],
) -> int:
    query_nf, query_wl = views[old]
    partner_nf, partner_wl = views[new]
    assert query_wl is not None and partner_wl is not None
    partner_cosine = cosine(query_wl, partner_wl)
    same = [i for i in nf_groups.get(query_nf or "", []) if i != old] if query_nf else []
    partner_same = partner_nf is not None and partner_nf == query_nf
    if partner_same:
        better = 0
        for other in same:
            if other == new:
                continue
            other_wl = views[other][1]
            if other_wl is not None and cosine(query_wl, other_wl) > partner_cosine:
                better += 1
        return better + 1
    better = len(same)
    scores = _cosine_scores(old, query_wl, postings, norms)
    for other, score in scores.items():
        if other == new or other == old:
            continue
        if query_nf and views[other][0] == query_nf:
            continue
        if score > partner_cosine:
            better += 1
    return better + 1


def _cosine_scores(
    query: int,
    query_wl: Counter[str],
    postings: dict[str, list[tuple[int, int]]],
    norms: list[float],
) -> dict[int, float]:
    dots: dict[int, float] = defaultdict(float)
    for feature, value in query_wl.items():
        for doc, count in postings.get(feature, []):
            if doc != query:
                dots[doc] += value * count
    qn = norms[query]
    if qn == 0.0:
        return {}
    return {doc: dot / (qn * norms[doc]) for doc, dot in dots.items() if norms[doc]}
