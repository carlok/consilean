"""The seed bridge and textual transport along its two sides.

The sides and the segment map are the amendment of 5 October 2026.
They are not fitted to a gap list.
"""

from __future__ import annotations

import re

from consilean.ingest.declarations import Declaration

ENDPOINT_NAMES = (
    "isSquare_neg_one_mod_markovNumber",
    "exists_sq_modEq_neg_one_markovNumber",
)

# Each pair is one direction of the seed iff. Whitespace in a signature may differ.
SIDES = (
    ("IsSquare (-1 : ZMod m.natAbs)", "∃ r : ℤ, r ^ 2 ≡ -1 [ZMOD m]"),
    (
        "IsSquare (-1 : ZMod n.markovNumber.natAbs)",
        "∃ r : ℤ, r ^ 2 ≡ -1 [ZMOD n.markovNumber]",
    ),
)

# Longest first. The replacement keeps the source piece's initial case.
SEGMENTS = (
    ("smul", "vadd"),
    ("hmul", "hadd"),
    ("mul", "add"),
    ("inv", "neg"),
    ("div", "sub"),
    ("semigroup", "addSemigroup"),
    ("monoid", "addMonoid"),
    ("group", "addGroup"),
    ("one", "zero"),
)

_ATTR = re.compile(
    r"@\[to_additive(?P<args>[^\]]*)\]\s*"
    r"(?:/--.*?-/\s*)?"
    r"(?:@\[[^\]]*\]\s*)*"
    r"(?P<priv>(?:(?:private|protected|noncomputable)\s+)*)"
    r"(?P<kind>theorem|lemma|def|abbrev|instance)\s+"
    r"(?P<name>[^\s:({\[]+)",
    re.S,
)


def _phrase(phrase: str) -> re.Pattern[str]:
    parts = [re.escape(part) for part in phrase.split()]
    return re.compile(r"\s+".join(parts))


def transport_signature(signature: str) -> str | None:
    """Replace one seed side, or one endpoint name, with the other side."""
    for left, right in SIDES:
        pattern = _phrase(left)
        if pattern.search(signature):
            return pattern.sub(right, signature, count=1)
        pattern = _phrase(right)
        if pattern.search(signature):
            return pattern.sub(left, signature, count=1)
    for name in ENDPOINT_NAMES:
        other = ENDPOINT_NAMES[1] if name == ENDPOINT_NAMES[0] else ENDPOINT_NAMES[0]
        pattern = re.compile(rf"(?<![\w.]){re.escape(name)}(?![\w])")
        if pattern.search(signature):
            return pattern.sub(other, signature, count=1)
    return None


def in_neighbourhood(decl: Declaration) -> bool:
    """True when the signature, not the docstring, meets an endpoint."""
    if transport_signature(decl.raw_sig) is None:
        return False
    return True


def _apply_case(source: str, replacement: str) -> str:
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement[:1].lower() + replacement[1:]


def _translate_piece(piece: str) -> str:
    folded = piece.lower()
    for source, replacement in SEGMENTS:
        if folded == source:
            return _apply_case(piece, replacement)
    return piece


def translate_identifier(name: str) -> str:
    """Apply the frozen segment map to one Lean identifier."""
    parts = re.split(r"(\.)", name)
    translated = []
    for part in parts:
        if part == ".":
            translated.append(part)
            continue
        pieces = re.split(r"(_)", part)
        out = []
        for piece in pieces:
            if piece == "_":
                out.append(piece)
                continue
            humps = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+|[^A-Za-z0-9]+", piece)
            out.append("".join(_translate_piece(hump) if hump.isalnum() else hump for hump in humps) or piece)
        translated.append("".join(out))
    return "".join(translated)


def translate_statement(signature: str) -> str:
    """Transport a multiplicative signature across the frozen segment map."""

    def repl(match: re.Match[str]) -> str:
        return translate_identifier(match.group(0))

    text = re.sub(r"[A-Za-z_][A-Za-z0-9_'.]*", repl, signature)
    text = text.replace(" * ", " + ")
    text = text.replace(" / ", " - ")
    return text


def explicit_additive_name(args: str) -> str | None:
    """The additive name written in the attribute, if it wrote one."""
    text = re.sub(r"\(attr\s*:=.*?\)", " ", args, flags=re.S)
    text = re.sub(r"/--.*?-/", " ", text, flags=re.S)
    match = re.search(r"[A-Za-z_][A-Za-z0-9_'.]*", text)
    if match is None:
        return None
    return match.group(0)


def iter_to_additive(source: str):
    """Yield `(kind, multiplicative name, explicit additive name or None)`."""
    for match in _ATTR.finditer(source):
        private = "private" in (match.group("priv") or "")
        yield match.group("kind"), match.group("name"), explicit_additive_name(match.group("args")), private
