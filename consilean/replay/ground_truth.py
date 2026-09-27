"""Mathlib deprecations whose statements differ.

`alias` declarations are pure renames and are excluded. A pair is kept only
when both declarations are found and their whitespace-normalized signatures differ.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from consilean.ingest.declarations import Declaration, load_declarations, module_name

_ATTR = re.compile(r"@\[deprecated\b([^\]]*)\]", re.S)
_SINCE = re.compile(r"since\s*:=\s*\"(\d{4}-\d{2}-\d{2})\"")
_KIND = re.compile(
    r"\s*(?:protected\s+|noncomputable\s+|private\s+|scoped\s+)*"
    r"(?P<kind>alias|theorem|lemma|def|abbrev)\s+(?P<name>[A-Za-z_]\w*)"
)
def collect_ground_truth(root: Path, namespace: str = "Mathlib") -> dict:
    """Scan `root/namespace` and return the frozen pair set plus the counts that explain it."""
    declarations = load_declarations(root, namespace=namespace)
    by_name: dict[str, list[Declaration]] = {}
    for decl in declarations:
        by_name.setdefault(decl.name, []).append(decl)
    aliases = 0
    no_replacement = 0
    unresolved = 0
    identical = 0
    pairs: list[dict] = []
    for path in sorted((root / namespace).glob("**/*.lean")):
        if ".lake" in path.relative_to(root / namespace).parts:
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        module = module_name(path, root, namespace)
        for attr in _ATTR.finditer(source):
            kind_match = _KIND.match(source, attr.end())
            if kind_match is None:
                continue
            if kind_match.group("kind") == "alias" or "private" in source[attr.end() : kind_match.end()]:
                aliases += 1
                continue
            replacement = _replacement_name(attr.group(1))
            if replacement is None:
                no_replacement += 1
                continue
            old_name = kind_match.group("name")
            old_sig = _signature_after(source, kind_match.end())
            new_decl = _lookup(by_name, replacement)
            if old_sig is None or new_decl is None:
                unresolved += 1
                continue
            old_norm = " ".join(old_sig.split())
            new_norm = " ".join(new_decl.raw_sig.split())
            if old_norm == new_norm:
                identical += 1
                continue
            since = _SINCE.search(attr.group(1))
            pairs.append(
                {
                    "old": f"{module}.{old_name}",
                    "new": f"{new_decl.module}.{new_decl.name}",
                    "since": since.group(1) if since else None,
                    "old_statement": old_norm,
                    "new_statement": new_norm,
                }
            )
    pairs.sort(key=lambda row: (row["old"], row["new"], row["since"] or ""))
    payload = json.dumps(pairs, sort_keys=True, ensure_ascii=False)
    return {
        "pairs": pairs,
        "count": len(pairs),
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "aliases_excluded": aliases,
        "no_replacement": no_replacement,
        "unresolved": unresolved,
        "identical_statements_excluded": identical,
    }


def _replacement_name(attr_body: str) -> str | None:
    text = re.sub(r'"[^"]*"', " ", attr_body)
    text = re.sub(r"\(since\s*:=[^)]*\)", " ", text)
    text = re.sub(r"\bsince\s*:=[^,\]]*", " ", text)
    match = re.search(r"[A-Za-z_][\w.']*", text)
    return match.group(0) if match else None


def _signature_after(source: str, name_end: int) -> str | None:
    rest = source[name_end:]
    end = rest.find(":=")
    if end < 0:
        return None
    return rest[:end]


def _lookup(by_name: dict[str, list[Declaration]], replacement: str) -> Declaration | None:
    short = replacement.rsplit(".", 1)[-1]
    suffix = replacement.rsplit(".", 1)[0] if "." in replacement else ""
    hits = by_name.get(short, [])
    if suffix:
        hits = [decl for decl in hits if decl.module == suffix or decl.module.endswith("." + suffix)]
    if len(hits) == 1:
        return hits[0]
    return None
