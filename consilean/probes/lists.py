"""The pairs Sprint 1 probes: section 5 controls, plus the current far lists."""

from __future__ import annotations

import re
from pathlib import Path

from consilean.ingest.declarations import Declaration, module_name

# Short names, resolved against the pinned checkout. These are the section 5
# controls, including pairs the current top-10 does not contain.
CONTROLS: list[tuple[str, str, str]] = [
    ("fibonacci-spine-horadam", "W_fibonacci_eq_fib", "markovFib_vieta_recurrence"),
    ("paley-measure-finite", "MeasurePaleyZygmund.paleyZygmund", "PaleyZygmund.paleyZygmund"),
    ("paley-measure-pmf", "MeasurePaleyZygmund.paleyZygmund", "pmf_paleyZygmund"),
    ("lucas-tribonacci", "sum_range_lucas", "tribonacci_two_mul_sum_add_one"),
    ("lucas-padovan", "sum_range_lucas", "padovan_sum_add_two"),
    ("tribonacci-padovan", "tribonacci_two_mul_sum_add_one", "padovan_sum_add_two"),
    ("reflect", "InversiveGeometry.reflect_reflect", "DescartesCircle.reflect_reflect"),
]

_ROW = re.compile(r"\|[^|]+\|[^|]+\|[^|]+\|[^|]+\| `([^`]+)` \| `([^`]+)` \|")


def pairs_under_heading(markdown: str, heading: str) -> list[tuple[str, str]]:
    """Read one generated ranking table. Names are as printed, without the LeanFrontier prefix."""
    lines = markdown.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            break
    if start is None:
        raise ValueError(f"heading not found: {heading}")
    found: list[tuple[str, str]] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        match = _ROW.search(line)
        if match:
            found.append((match.group(1), match.group(2)))
    return found


def _module_matches(module: str, suffix: str) -> bool:
    if not suffix:
        return True
    return module == suffix or module.endswith("." + suffix)


def resolve_short(declarations: list[Declaration], short: str) -> Declaration:
    """Match `Module.suffix.name` or a bare name when it is unique."""
    if "." in short:
        module_suffix, name = short.rsplit(".", 1)
    else:
        module_suffix, name = "", short
    hits = [
        decl
        for decl in declarations
        if decl.name == name and _module_matches(decl.module, module_suffix)
    ]
    if len(hits) != 1:
        raise ValueError(f"{short}: {len(hits)} matches")
    return hits[0]


def resolve_control(root: Path, short: str) -> Declaration:
    """Find a theorem by its header line.

    The Sprint 0 declaration regex can swallow a real theorem when the word
    "theorem" appears in a docstring. Probes of the controls use the header.
    """
    name = short.rsplit(".", 1)[-1]
    module_suffix = short.rsplit(".", 1)[0] if "." in short else ""
    header = re.compile(rf"^(?:theorem|lemma)\s+{re.escape(name)}\b", re.M)
    hits: list[Declaration] = []
    for path in sorted((root / "LeanFrontier").glob("**/*.lean")):
        source = path.read_text(encoding="utf-8")
        match = header.search(source)
        if match is None:
            continue
        module = module_name(path, root)
        if not _module_matches(module, module_suffix):
            continue
        rest = source[match.end() :]
        end = rest.find(":=")
        if end < 0:
            continue
        hits.append(
            Declaration(
                module=module,
                name=name,
                kind="theorem",
                statement=rest[:end].strip(),
                docstring="",
                raw_doc="",
                raw_sig=rest[:end],
            )
        )
    if len(hits) != 1:
        raise ValueError(f"{short}: {len(hits)} header matches")
    return hits[0]


def probe_jobs(cache_root: Path, declarations: list[Declaration], sprint1_markdown: str) -> list[dict]:
    """Controls first, then the two published far lists, duplicates skipped."""
    jobs: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, left: Declaration, right: Declaration) -> None:
        key = tuple(sorted((f"{left.module}.{left.name}", f"{right.module}.{right.name}")))
        if key in seen:
            return
        seen.add(key)
        jobs.append(
            {
                "list": kind,
                "left_module": left.module,
                "left_name": left.name,
                "right_module": right.module,
                "right_name": right.name,
                "left_sig": left.raw_sig,
                "right_sig": right.raw_sig,
            }
        )

    for kind, left_short, right_short in CONTROLS:
        add(kind, resolve_control(cache_root, left_short), resolve_control(cache_root, right_short))
    for heading, kind in (
        ("## Top pairs with no import path", "no-import-path"),
        ("## Top pairs at import distance at least 4", "distance-at-least-4"),
    ):
        for left_short, right_short in pairs_under_heading(sprint1_markdown, heading):
            add(kind, resolve_short(declarations, left_short), resolve_short(declarations, right_short))
    return jobs
