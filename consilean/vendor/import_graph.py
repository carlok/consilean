# Vendored from https://github.com/carlok/lean-corpus-density tools/import_graph.py
# Apache License 2.0. Blob d48190298d212ca8a0233e4b6909b7c5f36a0386.
# The logic below is unchanged.

"""Direct import graph of a Lean 4 corpus, read from file headers.

No Lean toolchain and no build: this reads source text only, so it runs
against any checkout at any toolchain version. Transitive closure is
deliberately not computed -- through the foundations every module reaches
every other one, and the density stops meaning anything.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Lean 4.34 introduced the module system, so an import line is one of
# `import M`, `public import M`, `meta import M`, `public meta import M`.
IMPORT_RE = re.compile(r"^(?:public\s+)?(?:meta\s+)?import\s+([A-Za-z_][\w.']*)", re.M)


def strip_comments(source: str) -> str:
    """Blank out `--` line comments and nestable `/- -/` blocks.

    Prose routinely contains the word "import" at the start of a wrapped
    comment line, which a naive header scan reads as an edge.
    """
    out: list[str] = []
    depth = 0
    i = 0
    n = len(source)
    while i < n:
        two = source[i : i + 2]
        if depth == 0 and two == "--":
            while i < n and source[i] != "\n":
                out.append(" ")
                i += 1
            continue
        if two == "/-":
            depth += 1
            out.append("  ")
            i += 2
            continue
        if two == "-/" and depth:
            depth -= 1
            out.append("  ")
            i += 2
            continue
        out.append(" " if depth and source[i] != "\n" else source[i])
        i += 1
    return "".join(out)


def module_name(path: Path, root: Path) -> str:
    return ".".join(path.relative_to(root).with_suffix("").parts)


def build(root: Path, namespace: str) -> dict[str, list[str]]:
    """Map every module under `root/namespace` to the modules it imports."""
    base = root / namespace
    graph: dict[str, list[str]] = {}
    for path in sorted(base.rglob("*.lean")):
        source = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        graph[module_name(path, root)] = IMPORT_RE.findall(source)
    return graph


def summarise(graph: dict[str, list[str]], namespace: str) -> dict:
    modules = set(graph)
    prefix = namespace + "."
    internal: list[tuple[str, str]] = []
    external = 0
    for source, targets in graph.items():
        for target in targets:
            # An edge counts as internal only if it lands on a module that is
            # actually present in this checkout, not merely on a matching name.
            if target in modules or target.startswith(prefix):
                internal.append((source, target))
            else:
                external += 1
    in_degree: dict[str, int] = {}
    for _, target in internal:
        in_degree[target] = in_degree.get(target, 0) + 1
    roots = sum(1 for m in graph if not any(t in modules or t.startswith(prefix) for t in graph[m]))
    return {
        "modules": len(graph),
        "internal_edges": len(internal),
        "external_edges": external,
        "internal_per_module": round(len(internal) / len(graph), 4) if graph else 0.0,
        "isolated_from_corpus": roots,
        "max_in_degree": max(in_degree.values(), default=0),
        "reused_modules": len(in_degree),
        "top_in_degree": sorted(in_degree.items(), key=lambda kv: (-kv[1], kv[0]))[:10],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="repository root")
    parser.add_argument("namespace", help="top-level source directory, e.g. Mathlib")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    graph = build(args.root, args.namespace)
    report = summarise(graph, args.namespace)
    if args.json_out:
        args.json_out.write_text(json.dumps({"graph": graph, "summary": report}, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
