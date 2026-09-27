"""Public declarations read from Lean source, without a toolchain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from consilean.vendor.import_graph import strip_comments

# Faithful to the Sprint 0 pilot: line comments only, so `/--` docstrings stay.
LINE_COMMENT_RE = re.compile(r"(?<![/-])--(?!-)[^\n]*")
DECL_RE = re.compile(
    r"(?:/--(?P<doc>.*?)-/\s*)?(?:@\[[^\]]*\]\s*)*(?P<priv>private\s+|protected\s+|noncomputable\s+)*"
    r"(?P<kind>theorem|lemma|def|abbrev)\s+(?P<name>[^\s:({\[]+)(?P<sig>.*?)(?::=|\bwhere\b|\n\s*\|)",
    re.S,
)


@dataclass(frozen=True)
class Declaration:
    """One public declaration. `raw_doc` and `raw_sig` keep the pilot's token source."""

    module: str
    name: str
    kind: str
    statement: str
    docstring: str
    raw_doc: str
    raw_sig: str


def module_name(path: Path, root: Path, namespace: str = "LeanFrontier") -> str:
    """Module name for a file under `root/namespace`, matching the LeanFrontier pilot."""
    rel = path.relative_to(root / namespace).as_posix()
    return f"{namespace}." + rel[:-5].replace("/", ".")


def load_declarations(
    root: Path,
    *,
    namespace: str = "LeanFrontier",
    blank_block_comments: bool = False,
    search_root: Path | None = None,
) -> list[Declaration]:
    """Parse public theorem/lemma/def/abbrev declarations.

    `search_root`, when set, is a tree that is not a single Lean package.
    Module names are then the relative path. `.lake` directories are skipped.

    `blank_block_comments` runs `strip_comments` first. That also blanks
    `/--` docstrings, so it is a measured variant, not the locked baseline.
    """
    if search_root is None:
        files = sorted((root / namespace).glob("**/*.lean"))
    else:
        files = sorted(
            path for path in search_root.glob("**/*.lean") if ".lake" not in path.relative_to(search_root).parts
        )
    declarations: list[Declaration] = []
    for path in files:
        source = path.read_text(encoding="utf-8", errors="replace")
        code = strip_comments(source) if blank_block_comments else LINE_COMMENT_RE.sub("", source)
        if search_root is None:
            module = module_name(path, root, namespace)
        else:
            module = path.relative_to(search_root).as_posix()[:-5].replace("/", ".")
        for match in DECL_RE.finditer(code):
            priv = match.group("priv")
            if priv and "private" in priv:
                continue
            raw_doc = match.group("doc") or ""
            raw_sig = match.group("sig") or ""
            declarations.append(
                Declaration(
                    module=module,
                    name=match.group("name"),
                    kind=match.group("kind"),
                    statement=raw_sig.strip(),
                    docstring=raw_doc.strip(),
                    raw_doc=raw_doc,
                    raw_sig=raw_sig,
                )
            )
    return declarations
