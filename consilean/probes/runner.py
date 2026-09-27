"""Run the preregistered tactic budget against a LeanFrontier checkout.

Each tactic gets its own process and a 10 second wall clock. Import time counts.
The first tactic that closes the goal stops that direction.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

def textual_forall(sig: str) -> str | None:
    """Turn a signature into a proposition without the statement parser.

    The colon that splits binders from the conclusion is the last `:` at
    parenthesis depth zero. Implicit binders stay as they appear in the source.
    """
    depth = 0
    split = None
    for index, char in enumerate(sig):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        elif char == ":" and depth == 0:
            split = index
    if split is None:
        body = " ".join(sig.split())
        return body or None
    binders = " ".join(sig[:split].split())
    body = " ".join(sig[split + 1 :].split())
    if not body:
        return None
    if not binders:
        return body
    return f"∀ {binders}, {body}"

TACTICS = (
    "rfl",
    "simp",
    "norm_num",
    "tauto",
    "omega",
    "decide",
    "exact?",
    "apply?",
    "aesop",
    "grind",
)
TIMEOUT_SECONDS = 10
DIRECTIONS = ("iff", "left_to_right", "right_to_left")


def link_mathlib_packages(cache: Path, mathlib_project: Path) -> None:
    """Point the cache's package directory at an existing v4.34.0 package tree.

    The link lives under the gitignored cache. It does not copy or edit that tree.
    """
    packages = mathlib_project / ".lake" / "packages"
    if not packages.is_dir():
        raise SystemExit(f"no Mathlib packages at {packages}")
    lake = cache / ".lake"
    lake.mkdir(parents=True, exist_ok=True)
    dest = lake / "packages"
    if dest.is_symlink() or dest.exists():
        return
    dest.symlink_to(packages)


def build_cache(cache: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["lake", "build", "LeanFrontier"],
        cwd=cache,
        check=False,
        capture_output=True,
        text=True,
    )


def probe_job(cache: Path, job: dict, work: Path) -> dict:
    """Probe one pair. Unparsed signatures are recorded as open and Lean is not started."""
    left_prop = textual_forall(job["left_sig"])
    right_prop = textual_forall(job["right_sig"])
    base = {
        "list": job["list"],
        "left": f"{job['left_module']}.{job['left_name']}",
        "right": f"{job['right_module']}.{job['right_name']}",
    }
    if left_prop is None or right_prop is None:
        return {
            **base,
            "directions": [
                {"direction": direction, "outcome": "open", "tactic": None, "detail": "signature did not parse"}
                for direction in DIRECTIONS
            ],
        }
    directions = []
    for direction in DIRECTIONS:
        directions.append(_probe_direction(cache, work, job, direction, left_prop, right_prop))
    return {**base, "directions": directions}


def _probe_direction(cache: Path, work: Path, job: dict, direction: str, left_prop: str, right_prop: str) -> dict:
    goal = _goal(direction, left_prop, right_prop)
    attempts = []
    for tactic in TACTICS:
        outcome, detail = _run_tactic(cache, work, job, direction, tactic, goal)
        attempts.append({"tactic": tactic, "outcome": outcome})
        if outcome == "closed":
            return {"direction": direction, "outcome": "closed", "tactic": tactic, "attempts": attempts, "detail": detail}
    if any(item["outcome"] == "timeout" for item in attempts):
        outcome = "timeout"
    else:
        outcome = "open"
    return {"direction": direction, "outcome": outcome, "tactic": None, "attempts": attempts, "detail": ""}


def _goal(direction: str, left_prop: str, right_prop: str) -> str:
    if direction == "iff":
        return f"({left_prop}) ↔ ({right_prop})"
    if direction == "left_to_right":
        return f"({left_prop}) → ({right_prop})"
    if direction == "right_to_left":
        return f"({right_prop}) → ({left_prop})"
    raise ValueError(direction)


def _run_tactic(
    cache: Path,
    work: Path,
    job: dict,
    direction: str,
    tactic: str,
    goal: str,
) -> tuple[str, str]:
    work.mkdir(parents=True, exist_ok=True)
    path = work / f"{_slug(job)}-{direction}-{_slug_tactic(tactic)}.lean"
    imports = []
    for module in (job["left_module"], job["right_module"]):
        line = f"import {module}"
        if line not in imports:
            imports.append(line)
    path.write_text(
        "\n".join(
            [
                *imports,
                "",
                "set_option autoImplicit false",
                "",
                f"example : {goal} := by",
                f"  {tactic}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    try:
        result = subprocess.run(
            ["lake", "env", "lean", str(path)],
            cwd=cache,
            check=False,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return "timeout", ""
    if result.returncode == 0:
        return "closed", ""
    tail = (result.stderr or result.stdout).strip().splitlines()
    detail = tail[-1][:240] if tail else ""
    return "open", detail


def _slug(job: dict) -> str:
    return f"{job['left_name']}__{job['right_name']}"


def _slug_tactic(tactic: str) -> str:
    return tactic.replace("?", "_q")
