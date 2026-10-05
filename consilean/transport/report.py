"""Assemble the Sprint 6 tables. Counts are written by the caller, not by hand."""

from __future__ import annotations

from pathlib import Path

from consilean.ingest.declarations import Declaration, load_declarations
from consilean.probes.runner import TACTICS, TIMEOUT_SECONDS
from consilean.transport.rungs import run_rungs
from consilean.transport.seed import SEGMENTS, in_neighbourhood, iter_to_additive, translate_identifier, translate_statement, transport_signature
from consilean.transport.views import Index, partner_rank

KS = (1, 5, 10)
GENERATING_COMMAND = "uv run consilean-sprint6"

CONFIG = {
    "amendment": "2026-10-05",
    "seed_bridge": "lean/IsSquareModEq.lean",
    "match": ["exact_digest", "normal_form"],
    "wl_cosine": "stored, not a gate",
    "seed": 0,
    "segments": [list(pair) for pair in SEGMENTS],
    "operator_tokens": {" * ": " + ", " / ": " - "},
    "inverse_postfix": "not rewritten",
    "tactics": list(TACTICS),
    "timeout_seconds": TIMEOUT_SECONDS,
    "k": list(KS),
}

PRIVATE_SKIPS = (
    {
        "corpus": "erdos-straus-offset-lean",
        "reason": "Local project. No public pin and no license note in this repository.",
    },
    {
        "corpus": "magma-1518-obstruction-lean",
        "reason": "Local project. No public pin and no license note in this repository.",
    },
    {
        "corpus": "diaz-modulus-lean",
        "reason": "Local project. No public pin and no license note in this repository.",
    },
    {
        "corpus": "other local Mathlib projects next to this repository",
        "reason": "Not pinned. Adding one needs a public revision and a license note.",
    },
)


def not_measured(reason: str, skips: list[dict] | None = None) -> dict:
    """A report that did not score. Used when a required tree is missing."""
    return {
        "generating_command": GENERATING_COMMAND,
        "config": CONFIG,
        "measured": False,
        "reason": reason,
        "skipped": list(skips or []) + list(PRIVATE_SKIPS),
        "gaps": [],
        "controls": {
            "status": "not_measured",
            "reason": reason,
        },
        "unportable": [],
        "rung2_targets": [],
        "not_measured": {
            "h4b": "No kernel-rejected bridge. Open and timeout probes are not rejections.",
            "replay": "The 1/3/6/12-month variant is not this sprint.",
            "h3_precision": "Preregistered H3 precision at k is still unmeasured.",
            "rung2_calls": "Both Sprint 3 caps are zero. No model call.",
        },
    }


def build(
    *,
    mathlib: Path,
    leanfrontier: Path,
    bridge: Path,
    prove2me: Path | None,
    tauceti: Path | None,
    extra_skips: list[dict],
    work: Path | None,
    run_lean: bool,
) -> dict:
    """Score the seed neighbourhood and the to_additive control once."""
    lf = load_declarations(leanfrontier, namespace="LeanFrontier")
    mathlib_decls = load_declarations(mathlib, namespace="Mathlib")
    index = Index()
    index.add("LeanFrontier", lf)
    index.add("Mathlib", mathlib_decls)
    corpora = [
        {"corpus": "LeanFrontier", "role": "kernel and lookup", "lean": "v4.34.0"},
        {"corpus": "Mathlib", "role": "lookup and to_additive control", "lean": "v4.34.0"},
    ]
    skips = list(extra_skips)
    if prove2me is not None and prove2me.is_dir():
        index.add("Prove2Me", load_declarations(prove2me, search_root=prove2me))
        corpora.append(
            {
                "corpus": "Prove2Me",
                "role": "declarations only",
                "reason": "Local missions tree is not one package and has no import graph. The public repository is logs.",
            }
        )
    else:
        skips.append({"corpus": "Prove2Me", "reason": "local missions tree not found"})
    if tauceti is not None and tauceti.is_dir():
        namespace = "TauCeti" if (tauceti / "TauCeti").is_dir() else None
        decls = load_declarations(
            tauceti,
            namespace=namespace or "TauCeti",
            search_root=None if namespace else tauceti,
        )
        index.add("Tau Ceti", decls)
        corpora.append(
            {
                "corpus": "Tau Ceti",
                "role": "text lookup only",
                "reason": "Lean v4.35.0-rc3. This sprint does not build that toolchain.",
            }
        )
    else:
        skips.append({"corpus": "Tau Ceti", "reason": "pinned checkout not available"})

    gaps = []
    for decl in lf:
        if not in_neighbourhood(decl):
            continue
        transported = transport_signature(decl.raw_sig)
        if transported is None:
            continue
        hits = index.matches(transported)
        row = {
            "module": decl.module,
            "name": decl.name,
            "transported": " ".join(transported.split()),
            "matches": hits,
            "gap": not hits,
            "rung0": None,
            "rung1": None,
            "engineering": None,
        }
        if run_lean and work is not None:
            checked = run_rungs(leanfrontier, work, bridge, decl, transported)
            row["rung0"] = checked["rung0"]
            row["rung1"] = checked["rung1"]
            row["engineering"] = checked["engineering"]
        gaps.append(row)

    controls = _controls(mathlib, mathlib_decls, index)
    unportable = _unportable(gaps)
    rung2 = [
        {"module": row["module"], "name": row["name"]}
        for row in gaps
        if row["gap"] and (row["rung1"] or {}).get("outcome") != "closed"
    ]
    return {
        "generating_command": GENERATING_COMMAND,
        "config": CONFIG,
        "measured": True,
        "reason": "",
        "corpora": corpora,
        "skipped": skips + list(PRIVATE_SKIPS),
        "gaps": gaps,
        "h4a": _h4a(gaps),
        "controls": controls,
        "unportable": unportable,
        "rung2_targets": rung2,
        "not_measured": {
            "h4b": "No kernel-rejected bridge. Open and timeout probes are not rejections.",
            "replay": "The 1/3/6/12-month variant is not this sprint.",
            "h3_precision": "Preregistered H3 precision at k is still unmeasured.",
            "rung2_calls": "Both Sprint 3 caps are zero. No model call.",
            "tau_ceti_elaboration": "Tau Ceti was not elaborated. Text lookup is separate.",
            "prove2me_elaboration": "Prove2Me was not elaborated. It is declarations only.",
        },
    }


def _h4a(gaps: list[dict]) -> dict:
    corpora = ("LeanFrontier", "Mathlib", "Tau Ceti", "Prove2Me")
    out = {}
    for corpus in corpora:
        hits = sum(1 for row in gaps if any(match["corpus"] == corpus for match in row["matches"]))
        out[corpus] = {"matches": hits, "transported": len(gaps), "fraction": (hits / len(gaps) if gaps else None)}
    return out


def _unportable(gaps: list[dict]) -> list[dict]:
    rows = []
    for row in gaps:
        rows.append(
            {
                "module": row["module"],
                "name": row["name"],
                "corpus": "Tau Ceti",
                "outcome": "unportable",
                "reason": "Not elaborated. Tau Ceti is Lean v4.35.0-rc3 and this sprint does not build that toolchain.",
            }
        )
        rows.append(
            {
                "module": row["module"],
                "name": row["name"],
                "corpus": "Prove2Me",
                "outcome": "unportable",
                "reason": "Not elaborated. The missions tree is not one Lean package.",
            }
        )
    return rows


def _controls(mathlib: Path, declarations: list[Declaration], index: Index) -> dict:
    by_short: dict[str, list[Declaration]] = {}
    for decl in declarations:
        by_short.setdefault(decl.name, []).append(decl)
    attributes = 0
    instances = 0
    private = 0
    to_dual = 0
    denominator = 0
    resolved = 0
    ranks: list[int | None] = []
    for path in sorted((mathlib / "Mathlib").glob("**/*.lean")):
        if ".lake" in path.relative_to(mathlib).parts:
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        to_dual += source.count("@[to_dual")
        module = "Mathlib." + path.relative_to(mathlib / "Mathlib").as_posix()[:-5].replace("/", ".")
        for kind, name, explicit, is_private in iter_to_additive(source):
            attributes += 1
            if kind == "instance":
                instances += 1
                continue
            if is_private:
                private += 1
                continue
            denominator += 1
            partner = _resolve(explicit, name, module, by_short)
            multiplicative = _find(name, module, by_short)
            if partner is None or multiplicative is None:
                ranks.append(None)
                continue
            resolved += 1
            transported = translate_statement(multiplicative.raw_sig)
            ref = {
                "corpus": "Mathlib",
                "module": partner.module,
                "name": partner.name,
                "raw_sig": partner.raw_sig,
            }
            ranks.append(partner_rank(index, transported, ref))
    recovered = {k: sum(1 for rank in ranks if rank is not None and rank <= k) for k in KS}
    resolved_ranks = [rank for rank in ranks if rank is not None]
    recovered_resolved = {
        k: sum(1 for rank in resolved_ranks if rank <= k) for k in KS
    }
    status = "measured" if attributes else "absent"
    return {
        "status": status,
        "reason": "" if attributes else "No to_additive attribute in the pinned Mathlib sources.",
        "note": (
            "The denominator is to_additive on a theorem, lemma, def, or abbrev. "
            "An additive name that is not a source declaration is not recovered. "
            "Recall among resolved names is reported separately and is not a second gate."
        ),
        "attributes": attributes,
        "instances_excluded": instances,
        "private_excluded": private,
        "denominator": denominator,
        "resolved": resolved,
        "recovered": recovered,
        "recall": {str(k): (recovered[k] / denominator if denominator else None) for k in KS},
        "resolved_recall": {
            str(k): (recovered_resolved[k] / len(resolved_ranks) if resolved_ranks else None) for k in KS
        },
        "to_dual_attributes": to_dual,
        "to_dual_role": "Counted only. Not used as a bridge.",
    }


def _resolve(explicit: str | None, mul_name: str, module: str, by_short: dict[str, list[Declaration]]) -> Declaration | None:
    if explicit:
        found = _find(explicit, module, by_short)
        if found is not None and _same_decl(found, mul_name, module):
            return None
        return found
    guessed = translate_identifier(mul_name.split(".")[-1])
    found = _find(guessed, module, by_short)
    if found is not None and found.name == mul_name.split(".")[-1] and found.module == module:
        return None
    return found


def _same_decl(found: Declaration, mul_name: str, module: str) -> bool:
    return found.name == mul_name.split(".")[-1] and found.module == module


def _find(name: str, module: str, by_short: dict[str, list[Declaration]]) -> Declaration | None:
    short = name.split(".")[-1]
    hits = by_short.get(short, [])
    if "." in name:
        qualified = [decl for decl in hits if f"{decl.module}.{decl.name}".endswith(name) or decl.name == name]
        hits = qualified or hits
    if len(hits) == 1:
        return hits[0]
    same = [decl for decl in hits if decl.module == module]
    if len(same) == 1:
        return same[0]
    return None

