"""Probe lists and the quantified goal, without starting Lean."""

from consilean.ingest.declarations import Declaration
from consilean.probes.lists import pairs_under_heading, resolve_short
from consilean.probes.runner import _goal
from consilean.views.syntax import as_forall

MARKDOWN = """
## Top pairs with no import path

| primary | normal form | WL | distance | left | right |
|---:|---:|---:|---:|---|---|
| 0.50 | 0 | 1.00 | ∞ | `Combinatorics.Josephus.OneIndexed.josephus_one` | `NumberTheory.LucasNumber.lucas_one` |

## Top pairs at import distance at least 4

| primary | normal form | WL | distance | left | right |
|---:|---:|---:|---:|---|---|
| 0.46 | 0 | 0.93 | 12 | `NumberTheory.DescartesCircle.isQuadruple_reflect` | `NumberTheory.MarkovEquation.isSolution_jump` |
"""


def _decl(module: str, name: str) -> Declaration:
    return Declaration(module, name, "theorem", "True", "", "", " : True")


def test_far_tables_are_read_separately() -> None:
    far = pairs_under_heading(MARKDOWN, "## Top pairs with no import path")
    distant = pairs_under_heading(MARKDOWN, "## Top pairs at import distance at least 4")
    assert far == [("Combinatorics.Josephus.OneIndexed.josephus_one", "NumberTheory.LucasNumber.lucas_one")]
    assert distant[0][0].endswith("isQuadruple_reflect")


def test_module_suffix_does_not_match_a_longer_name() -> None:
    decls = [
        _decl("LeanFrontier.Probability.MeasurePaleyZygmund", "paleyZygmund"),
        _decl("LeanFrontier.Probability.PaleyZygmund", "paleyZygmund"),
    ]
    found = resolve_short(decls, "PaleyZygmund.paleyZygmund")
    assert found.module.endswith(".PaleyZygmund")
    assert "Measure" not in found.module.rsplit(".", 1)[-1]


def test_implicit_binders_and_comparison_parse() -> None:
    from consilean.views.syntax import parse_statement

    sig = "{α : Type*} (a b : α) [CommRing α] : a ≤ b"
    assert parse_statement(sig) is not None


def test_as_forall_keeps_source_names() -> None:
    sig = " (n : OrientedNode) :\n    IsSquare (-1 : ZMod n.markovNumber.natAbs) "
    goal = as_forall(sig)
    assert goal is not None
    assert goal.startswith("∀ (n : OrientedNode),")
    assert "natAbs" in goal
    text = _goal("iff", goal, "True")
    assert "↔" in text
