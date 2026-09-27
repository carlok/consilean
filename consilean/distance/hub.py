"""Drop the highest in-degree modules and recompute undirected distance.

The preregistered settings are 0%, 1%, and 5% of the modules. A positive
fraction rounds to the nearest count. Removing a hub deletes it as a node,
so paths that only existed through it become longer or disappear.
"""

from __future__ import annotations

from consilean.ingest.graph import undirected_distances


def in_degrees(graph: dict[str, list[str]]) -> dict[str, int]:
    modules = set(graph)
    degree = {module: 0 for module in modules}
    for targets in graph.values():
        for target in targets:
            if target in modules:
                degree[target] = degree.get(target, 0) + 1
    return degree


def drop_hubs(graph: dict[str, list[str]], fraction: float) -> tuple[dict[str, list[str]], list[str]]:
    """Return the graph with the top `fraction` of in-degree modules removed."""
    degree = in_degrees(graph)
    count = round(fraction * len(degree)) if fraction else 0
    hubs = [name for name, _ in sorted(degree.items(), key=lambda item: (-item[1], item[0]))[:count]]
    removed = set(hubs)
    kept = {
        source: [target for target in targets if target not in removed and target in degree]
        for source, targets in graph.items()
        if source not in removed
    }
    modules = set(kept)
    return {source: [target for target in targets if target in modules] for source, targets in kept.items()}, hubs


def distances_at(graph: dict[str, list[str]], fraction: float) -> tuple[dict[str, dict[str, int]], list[str]]:
    kept, hubs = drop_hubs(graph, fraction)
    return undirected_distances(kept), hubs
