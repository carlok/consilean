"""Rung 0 and rung 1 against the v4.34.0 LeanFrontier cache.

Rung 0 keeps the seed bridge in scope. Rung 1 does not.
A rung-0 closure is an engineering check, not a result.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from consilean.ingest.declarations import Declaration
from consilean.probes.runner import TACTICS, TIMEOUT_SECONDS, textual_forall
from consilean.views.syntax import as_forall

BRIDGE_NAME = "isSquare_neg_one_zmod_iff_sq_modEq"


def bridge_source(path: Path) -> str:
    """The seed theorem, without its imports. The temp file imports Mathlib itself."""
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("import ")]
    return "\n".join(lines).strip() + "\n"


def goal_text(signature: str) -> str | None:
    """A Lean proposition. Prefer the statement parser so `∃ r : ℤ` stays a binder."""
    parsed = as_forall(signature)
    if parsed is not None:
        return parsed
    return textual_forall(signature)


def namespaces_of(source: str) -> list[str]:
    return re.findall(r"(?m)^namespace\s+(\S+)", source)


def sanitize_detail(detail: str) -> str:
    """Keep the Lean diagnostic. Drop the absolute cache directory."""
    return re.sub(r"\S*/(?=[^/\s]+\.lean\b)", "", detail)


def run_rungs(cache: Path, work: Path, bridge: Path, decl: Declaration, transported: str) -> dict:
    goal = goal_text(transported)
    if goal is None:
        return {
            "rung0": {"outcome": "open", "detail": "transported signature has no conclusion"},
            "rung1": {"outcome": "open", "tactic": None, "detail": "transported signature has no conclusion"},
            "engineering": "rung 0 was not run; the transported signature has no conclusion",
        }
    name = decl.name
    rung0 = _run(cache, work, decl, "rung0", goal, _rung0_text(cache, bridge, decl, goal, name), TIMEOUT_SECONDS)
    engineering = None
    if rung0["outcome"] != "closed":
        engineering = rung0.get("detail") or rung0["outcome"]
    rung1 = _rung1(cache, work, decl, goal)
    return {"rung0": rung0, "rung1": rung1, "engineering": engineering}


def _opens(cache: Path, decl: Declaration) -> str:
    path = cache / f"{decl.module.replace('.', '/')}.lean"
    if not path.is_file():
        return ""
    names = namespaces_of(path.read_text(encoding="utf-8", errors="replace"))
    if not names:
        return ""
    return "open " + " ".join(dict.fromkeys(names))


def _rung0_text(cache: Path, bridge: Path, decl: Declaration, goal: str, name: str) -> str:
    return "\n".join(
        [
            f"import {decl.module}",
            "import Mathlib.Data.Int.ModEq",
            "import Mathlib.Data.ZMod.Basic",
            "",
            _opens(cache, decl),
            bridge_source(bridge),
            "",
            f"example : {goal} := by",
            f"  simpa [{BRIDGE_NAME}] using {name}",
            "",
        ]
    )


def _rung1_text(cache: Path, decl: Declaration, goal: str, tactic: str) -> str:
    return "\n".join(
        [
            f"import {decl.module}",
            "",
            _opens(cache, decl),
            "set_option autoImplicit false",
            "",
            f"example : {goal} := by",
            f"  {tactic}",
            "",
        ]
    )


def _rung1(cache: Path, work: Path, decl: Declaration, goal: str) -> dict:
    attempts = []
    for tactic in TACTICS:
        outcome = _run(cache, work, decl, f"rung1-{tactic}", goal, _rung1_text(cache, decl, goal, tactic), TIMEOUT_SECONDS)
        attempts.append({"tactic": tactic, "outcome": outcome["outcome"]})
        if outcome["outcome"] == "closed":
            return {"outcome": "closed", "tactic": tactic, "attempts": attempts, "detail": ""}
    if any(item["outcome"] == "timeout" for item in attempts):
        status = "timeout"
    else:
        status = "open"
    return {"outcome": status, "tactic": None, "attempts": attempts, "detail": ""}


def _run(cache: Path, work: Path, decl: Declaration, label: str, goal: str, text: str, timeout: int) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    path = work / f"{decl.name}-{label.replace('?', '_q').replace(' ', '_')}.lean"
    path.write_text(text, encoding="utf-8")
    try:
        result = subprocess.run(
            ["lake", "env", "lean", str(path)],
            cwd=cache,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"outcome": "timeout", "detail": ""}
    if result.returncode == 0:
        return {"outcome": "closed", "detail": ""}
    tail = (result.stderr or result.stdout).strip().splitlines()
    detail = sanitize_detail(tail[-1][:240] if tail else "")
    return {"outcome": "open", "detail": detail}
