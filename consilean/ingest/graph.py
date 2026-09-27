"""Module import graphs: the pilot's naive scan, and distance on a graph."""

from __future__ import annotations

import collections
import re
from pathlib import Path

from consilean.ingest.declarations import module_name

# The pilot's importer. It misses `public import` / `meta import`, and it
# treats `import` at the start of a comment line as an edge.
FAITHFUL_IMPORT_RE = re.compile(r"^import (LeanFrontier\S*)", re.M)


def faithful_module_graph(root: Path) -> dict[str, list[str]]:
    """Map each LeanFrontier module to the imports the pilot's regex sees.

    The scan uses the raw source, comments included, as the pilot did.
    """
    graph: dict[str, list[str]] = {}
    for path in sorted(root.glob("LeanFrontier/**/*.lean")):
        source = path.read_text(encoding="utf-8")
        graph[module_name(path, root)] = FAITHFUL_IMPORT_RE.findall(source)
    return graph


def directed_internal_edges(graph: dict[str, list[str]]) -> int:
    """Count import edges whose target is a module present in `graph`."""
    modules = set(graph)
    return sum(1 for targets in graph.values() for target in targets if target in modules)


def undirected_distances(graph: dict[str, list[str]]) -> dict[str, dict[str, int]]:
    """Undirected BFS distance. An edge exists only when both ends are in `graph`."""
    modules = set(graph)
    adjacent: dict[str, set[str]] = collections.defaultdict(set)
    for source, targets in graph.items():
        for target in targets:
            if target in modules:
                adjacent[source].add(target)
                adjacent[target].add(source)

    def bfs(src: str) -> dict[str, int]:
        distance = {src: 0}
        queue: collections.deque[str] = collections.deque([src])
        while queue:
            node = queue.popleft()
            for nxt in adjacent[node]:
                if nxt not in distance:
                    distance[nxt] = distance[node] + 1
                    queue.append(nxt)
        return distance

    return {module: bfs(module) for module in graph}
