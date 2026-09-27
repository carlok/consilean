"""Count modules, declarations, and how many signatures parse.

This is not a similarity ranking and not an H2 or H3 measurement.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from consilean.ingest.declarations import load_declarations
from consilean.vendor.import_graph import build, summarise
from consilean.views.syntax import parse_statement


def coverage_row(
    *,
    corpus: str,
    revision: str | None,
    root: Path,
    namespace: str | None = None,
    search_root: Path | None = None,
    note: str = "",
) -> dict:
    declarations = load_declarations(root, namespace=namespace or "", search_root=search_root)
    parsed = sum(1 for decl in declarations if parse_statement(decl.raw_sig) is not None)
    row = {
        "corpus": corpus,
        "revision": revision,
        "lean_files": _file_count(root, namespace, search_root),
        "public_declarations": len(declarations),
        "parsed": parsed,
        "note": note,
        "import_modules": None,
        "internal_edges": None,
    }
    if namespace and search_root is None and (root / namespace).is_dir():
        summary = summarise(build(root, namespace), namespace)
        row["import_modules"] = summary["modules"]
        row["internal_edges"] = summary["internal_edges"]
    return row


def git_revision(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _file_count(root: Path, namespace: str | None, search_root: Path | None) -> int:
    base = search_root if search_root is not None else root / (namespace or "")
    if not base.is_dir():
        return 0
    return sum(1 for path in base.glob("**/*.lean") if ".lake" not in path.relative_to(base).parts)
