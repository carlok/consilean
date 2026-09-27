"""Per-pair and total token caps. Both must be set by the operator."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Budget:
    per_pair_tokens: int
    total_tokens: int

    @property
    def is_open(self) -> bool:
        return self.per_pair_tokens > 0 and self.total_tokens > 0


def load_budget(path: Path) -> Budget:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Budget(
        per_pair_tokens=int(data.get("per_pair_tokens") or 0),
        total_tokens=int(data.get("total_tokens") or 0),
    )
