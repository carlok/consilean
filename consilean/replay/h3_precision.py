"""Preregistered H3 precision at k on the Mathlib v4.28.0 snapshot.

The candidate universe is the amendment of 5 October 2026. Neighbor recall
stays in the earlier H3 table.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict, deque
from datetime import date
from itertools import combinations
from pathlib import Path

from consilean.ingest.corpus import repo_root
from consilean.ingest.declarations import Declaration, load_declarations
from consilean.replay.cli import MATHLIB_REV, _mathlib_root
from consilean.replay.h3 import TAG, WINDOWS_MONTHS, add_months, extract_snapshot, snapshot_date
from consilean.vendor.import_graph import build
from consilean.views.syntax import formula_graph, normal_form, parse_statement
from consilean.views.wl import cosine, wl_features

KS = (10, 50, 100)
BUCKETS = ("distance_at_least_4", "distance_at_least_8", "no_path")
GENERATING_COMMAND = "uv run consilean-h3-precision"
SEED = 0


def main() -> None:
    root = repo_root()
    mathlib = _mathlib_root(root)
    if mathlib is None:
        raise SystemExit("local Mathlib v4.34.0 tree not found")
    start = snapshot_date(mathlib, TAG)
    dest = root / "corpora" / "cache" / f"mathlib-{TAG}"
    extract_snapshot(mathlib, dest, TAG)
    frozen = json.loads((root / "docs" / "generated" / "sprint2-ground-truth.json").read_text(encoding="utf-8"))
    print("loading snapshot", flush=True)
    declarations = load_declarations(dest, namespace="Mathlib")
    print("ranking normal-form pairs", flush=True)
    ranked = rank_buckets(declarations, dest)
    links = _links(frozen["pairs"])
    windows = []
    for months in WINDOWS_MONTHS:
        end = add_months(start, months)
        windows.append(_window(ranked, links, start, end, months))
        print(f"window {months}m", flush=True)
    report = {
        "generating_command": GENERATING_COMMAND,
        "scored_revision": MATHLIB_REV,
        "snapshot_tag": TAG,
        "snapshot_date": start.isoformat(),
        "ground_truth_sha256": frozen["sha256"],
        "seed": SEED,
        "hub_fraction": 0,
        "note": (
            "Precision at k among normal-form pairs on the snapshot. "
            "A pair is later connected when it is a frozen deprecation inside the window. "
            "The neighbor-recall table is a different measurement."
        ),
        "windows": windows,
    }
    out = root / "docs" / "generated"
    (out / "sprint2-h3-precision.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "sprint2-h3-precision.md").write_text(_markdown(report), encoding="utf-8")
    print(f"wrote {out / 'sprint2-h3-precision.md'}")


def rank_buckets(declarations: list[Declaration], snapshot: Path) -> dict[str, list[dict]]:
    """Top-sortable rows per far bucket. The full bucket is kept for the random draw."""
    groups: dict[str, list[Declaration]] = defaultdict(list)
    for decl in declarations:
        form = normal_form(decl.raw_sig)
        if form is not None:
            groups[form].append(decl)
    features: dict[int, object] = {}
    modules: set[str] = set()
    for group in groups.values():
        if len(group) < 2:
            continue
        for decl in group:
            modules.add(decl.module)
            statement = parse_statement(decl.raw_sig)
            features[id(decl)] = (
                wl_features(*formula_graph(statement, keep_names=False)) if statement is not None else None
            )
    distances = _distances(build(snapshot, "Mathlib"), modules)
    buckets: dict[str, list[dict]] = {name: [] for name in BUCKETS}
    for group in groups.values():
        if len(group) < 2:
            continue
        for left, right in combinations(group, 2):
            if left.module == right.module:
                continue
            distance = _distance(distances, left.module, right.module)
            row = {
                "names": tuple(sorted((f"{left.module}.{left.name}", f"{right.module}.{right.name}"))),
                "cosine": _pair_cosine(features.get(id(left)), features.get(id(right))),
                "distance": distance,
            }
            if distance is None:
                buckets["no_path"].append(row)
            if distance is not None and distance >= 4:
                buckets["distance_at_least_4"].append(row)
            if distance is not None and distance >= 8:
                buckets["distance_at_least_8"].append(row)
    for rows in buckets.values():
        rows.sort(key=lambda item: (-item["cosine"], item["names"]))
    return buckets


def _distances(graph: dict[str, list[str]], needed: set[str]) -> dict[str, dict[str, int]]:
    """BFS from the modules that occur in a normal-form class. Hub drop is 0%."""
    modules = set(graph)
    adjacent: dict[str, set[str]] = defaultdict(set)
    for source, targets in graph.items():
        for target in targets:
            if target in modules:
                adjacent[source].add(target)
                adjacent[target].add(source)
    distances: dict[str, dict[str, int]] = {}
    for src in needed & modules:
        distance = {src: 0}
        queue: deque[str] = deque([src])
        while queue:
            node = queue.popleft()
            for nxt in adjacent[node]:
                if nxt not in distance:
                    distance[nxt] = distance[node] + 1
                    queue.append(nxt)
        distances[src] = distance
    return distances


def _distance(distances: dict[str, dict[str, int]], left: str, right: str) -> int | None:
    return distances.get(left, {}).get(right)


def _pair_cosine(left, right) -> float:
    if left is None or right is None:
        return 0.0
    return cosine(left, right)


def _links(pairs: list[dict]) -> dict[frozenset[str], date]:
    linked = {}
    for pair in pairs:
        linked[frozenset((pair["old"], pair["new"]))] = date.fromisoformat(pair["since"])
    return linked


def _window(ranked: dict[str, list[dict]], links: dict[frozenset[str], date], start: date, end: date, months: int) -> dict:
    rng = random.Random(SEED)
    buckets = []
    for name in BUCKETS:
        rows = ranked[name]
        flags = [_connected(row, links, start, end) for row in rows]
        # One shuffle, then prefixes, so the smaller random sets are prefixes of the larger one.
        order = list(range(len(rows)))
        rng.shuffle(order)
        per_k = []
        for k in KS:
            take = flags[:k]
            random_flags = [flags[index] for index in order[:k]]
            per_k.append(
                {
                    "k": k,
                    "evaluated": len(take),
                    "precision": _precision(take),
                    "random_precision": _precision(random_flags),
                    "bootstrap": _bootstrap(take),
                }
            )
        top = [
            {
                "names": list(row["names"]),
                "cosine": row["cosine"],
                "distance": row["distance"],
                "connected": flags[index],
            }
            for index, row in enumerate(rows[: max(KS)])
        ]
        buckets.append({"bucket": name, "candidates": len(rows), "k": per_k, "top": top})
    return {"months": months, "end": end.isoformat(), "buckets": buckets}


def _connected(row: dict, links: dict[frozenset[str], date], start: date, end: date) -> bool:
    since = links.get(frozenset(row["names"]))
    return since is not None and start < since <= end


def _precision(flags: list[bool]) -> float | None:
    if not flags:
        return None
    return sum(1 for flag in flags if flag) / len(flags)


def _bootstrap(flags: list[bool], *, draws: int = 1000) -> dict | None:
    if not flags:
        return None
    rng = random.Random(SEED)
    n = len(flags)
    samples = []
    for _ in range(draws):
        hits = sum(1 for _ in range(n) if flags[rng.randrange(n)])
        samples.append(hits / n)
    samples.sort()
    return {
        "draws": draws,
        "p2_5": samples[int(0.025 * draws)],
        "p50": samples[draws // 2],
        "p97_5": samples[min(draws - 1, int(0.975 * draws))],
    }


def _markdown(report: dict) -> str:
    lines = [
        "# Sprint 2 H3 precision",
        "",
        f"Generated by `{report['generating_command']}`.",
        f"Snapshot: `{report['snapshot_tag']}` dated {report['snapshot_date']}.",
        f"Frozen-set sha256: `{report['ground_truth_sha256']}`.",
        f"Seed: `{report['seed']}`. Hub drop: {report['hub_fraction']}.",
        "",
        report["note"],
        "",
        "| months | bucket | k | evaluated | precision | random | bootstrap p2.5 | p97.5 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for window in report["windows"]:
        for bucket in window["buckets"]:
            for item in bucket["k"]:
                lines.append(
                    "| {months} | {bucket} | {k} | {evaluated} | {precision} | {random} | {low} | {high} |".format(
                        months=window["months"],
                        bucket=bucket["bucket"],
                        k=item["k"],
                        evaluated=item["evaluated"],
                        precision=_cell(item["precision"]),
                        random=_cell(item["random_precision"]),
                        low=_cell(None if item["bootstrap"] is None else item["bootstrap"]["p2_5"]),
                        high=_cell(None if item["bootstrap"] is None else item["bootstrap"]["p97_5"]),
                    )
                )
    lines.append("")
    return "\n".join(lines)


def _cell(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


if __name__ == "__main__":
    main()
