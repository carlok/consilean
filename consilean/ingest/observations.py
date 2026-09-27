"""Receiver observations: statement digests and type-level dependencies."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Entrypoint:
    """One observed entrypoint. Dependencies may be empty."""

    name: str
    statement_sha256: str | None
    type_dependencies: frozenset[str]


def load_entrypoints(root: Path) -> dict[str, Entrypoint]:
    """Load entrypoints from `receiver-observations/*/*.json`.

    Files are read in sorted path order. A repeated name keeps the later file.
    """
    entrypoints: dict[str, Entrypoint] = {}
    observations = root / "receiver-observations"
    for path in sorted(observations.glob("*/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        observed = data.get("report", {}).get("observed", {})
        for name, entry in (observed.get("entrypoints") or {}).items():
            deps = entry.get("type_dependencies") or []
            entrypoints[name] = Entrypoint(
                name=name,
                statement_sha256=entry.get("statement_sha256"),
                type_dependencies=frozenset(deps),
            )
    return entrypoints
