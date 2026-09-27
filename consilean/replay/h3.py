"""H3: rank the frozen pairs on a Mathlib snapshot from before March 2026.

The snapshot is extracted with git archive. The Mathlib checkout is not moved.
Windows are 1, 3, 6, and 12 months after the snapshot date. A pair counts in a
window when its since date falls strictly after the snapshot and on or before
the window end.
"""

from __future__ import annotations

import json
import random
import subprocess
from datetime import date
from pathlib import Path

from consilean.ingest.corpus import repo_root
from consilean.ingest.declarations import load_declarations
from consilean.replay.cli import MATHLIB_REV, _mathlib_root
from consilean.replay.recall import aggregate, pair_outcomes

TAG = "v4.28.0"
WINDOWS_MONTHS = (1, 3, 6, 12)
GENERATING_COMMAND = "uv run consilean-h3"


def add_months(start: date, months: int) -> date:
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, _month_length(year, month))
    return date(year, month, day)


def _month_length(year: int, month: int) -> int:
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    if month in {1, 3, 5, 7, 8, 10, 12}:
        return 31
    return 30


def snapshot_date(mathlib: Path, tag: str) -> date:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cs", tag],
        cwd=mathlib,
        check=True,
        capture_output=True,
        text=True,
    )
    return date.fromisoformat(result.stdout.strip())


def extract_snapshot(mathlib: Path, dest: Path, tag: str) -> None:
    """Extract Mathlib sources for a tag. Skip if the tree is already there."""
    marker = dest / "Mathlib"
    if marker.is_dir():
        return
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "archive", tag, "Mathlib"],
        cwd=mathlib,
        check=True,
        capture_output=True,
    )
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive.stdout, check=True)


def window_pairs(pairs: list[dict], start: date, end: date) -> list[dict]:
    chosen = []
    for pair in pairs:
        since = date.fromisoformat(pair["since"])
        if start < since <= end:
            chosen.append(pair)
    return chosen


def bootstrap_recall(ranks: list[int], k: int, *, draws: int = 1000, seed: int = 0) -> dict | None:
    """Percentiles of recall@k when resampling the observed ranks."""
    if not ranks:
        return None
    rng = random.Random(seed)
    n = len(ranks)
    samples = []
    for _ in range(draws):
        hits = sum(1 for _ in range(n) if rng.choice(ranks) <= k)
        samples.append(hits / n)
    samples.sort()
    return {
        "draws": draws,
        "p2_5": samples[int(0.025 * draws)],
        "p50": samples[int(0.5 * draws)],
        "p97_5": samples[min(draws - 1, int(0.975 * draws))],
    }


def main() -> None:
    root = repo_root()
    mathlib = _mathlib_root(root)
    if mathlib is None:
        raise SystemExit("local Mathlib v4.34.0 tree not found")
    start = snapshot_date(mathlib, TAG)
    dest = root / "corpora" / "cache" / f"mathlib-{TAG}"
    print(f"extract {TAG} dated {start.isoformat()} into {dest}", flush=True)
    extract_snapshot(mathlib, dest, TAG)
    frozen = json.loads((root / "docs" / "generated" / "sprint2-ground-truth.json").read_text(encoding="utf-8"))
    print("loading snapshot declarations", flush=True)
    declarations = load_declarations(dest, namespace="Mathlib")
    later = [pair for pair in frozen["pairs"] if date.fromisoformat(pair["since"]) > start]
    print(f"ranking {len(later)} pairs on {len(declarations)} declarations", flush=True)
    parsed, outcomes = pair_outcomes(declarations, later)
    windows = []
    for months in WINDOWS_MONTHS:
        end = add_months(start, months)
        chosen = [item for item in outcomes if date.fromisoformat(item["since"]) <= end]
        measured = aggregate(chosen, parsed)
        ranks = measured.pop("parsed_ranks")
        windows.append(
            {
                "months": months,
                "end": end.isoformat(),
                "pairs": len(chosen),
                "h3": measured,
                "random_recall_at_10": (10 / (parsed - 1) if parsed > 1 else None),
                "declarations": len(declarations),
                "parsed": parsed,
                "bootstrap_recall_at_10": bootstrap_recall(
                    [10**9 if rank is None else rank for rank in ranks],
                    10,
                ),
            }
        )
        print(
            f"window {months}m pairs {len(chosen)} recall@10 {measured['recall'].get('10')}",
            flush=True,
        )
    report = {
        "generating_command": GENERATING_COMMAND,
        "scored_revision": MATHLIB_REV,
        "snapshot_tag": TAG,
        "snapshot_date": start.isoformat(),
        "ground_truth_sha256": frozen["sha256"],
        "note": (
            "Neighbor recall of frozen deprecations whose since date is after the snapshot. "
            "A missing declaration on that snapshot is not recovered."
        ),
        "windows": windows,
    }
    out = root / "docs" / "generated"
    (out / "sprint2-h3.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "sprint2-h3.md").write_text(_markdown(report), encoding="utf-8")
    print(f"wrote {out / 'sprint2-h3.md'}")


def _markdown(report: dict) -> str:
    lines = [
        "# Sprint 2 H3",
        "",
        f"Generated by `{report['generating_command']}`.",
        f"Snapshot: `{report['snapshot_tag']}` dated {report['snapshot_date']}.",
        f"Frozen-set sha256: `{report['ground_truth_sha256']}`.",
        "",
        report["note"],
        "",
        "| months | end | pairs | evaluated | unparsed | missing | recall@10 | random@10 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for window in report["windows"]:
        h3 = window["h3"]
        recall = h3["recall"].get("10")
        shown = "" if recall is None else f"{recall:.4f}"
        random_recall = window["random_recall_at_10"]
        random_shown = "" if random_recall is None else f"{random_recall:.6f}"
        lines.append(
            f"| {window['months']} | {window['end']} | {window['pairs']} | {h3['evaluated']} | "
            f"{h3['unparsed']} | {h3['missing_declaration']} | {shown} | {random_shown} |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
