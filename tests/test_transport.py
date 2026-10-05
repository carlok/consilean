"""Transport along the seed bridge, before any corpus measurement."""

from consilean.ingest.declarations import Declaration
from consilean.transport.report import not_measured
from consilean.transport.rungs import goal_text, namespaces_of, sanitize_detail
from consilean.transport.seed import explicit_additive_name, in_neighbourhood, translate_identifier, transport_signature
from consilean.transport.views import Index

IS_SQUARE = " (n : OrientedNode) :\n    IsSquare (-1 : ZMod n.markovNumber.natAbs) "
MOD_EQ = " (n : OrientedNode) :\n    ∃ r : ℤ, r ^ 2 ≡ -1 [ZMOD n.markovNumber] "


def _decl(name: str, sig: str, doc: str = "") -> Declaration:
    return Declaration("M", name, "theorem", sig.strip(), doc, doc, sig)


def test_transport_replaces_one_seed_side() -> None:
    transported = transport_signature(IS_SQUARE)
    assert transported is not None
    assert "IsSquare" not in transported
    assert "ZMOD n.markovNumber" in transported


def test_neighbourhood_ignores_the_docstring() -> None:
    mentioned = _decl("other", " (n : Nat) : n = n ", doc="uses isSquare_neg_one_mod_markovNumber")
    in_sig = _decl("other", " (n : Nat) : isSquare_neg_one_mod_markovNumber n ")
    assert in_neighbourhood(mentioned) is False
    assert in_neighbourhood(in_sig) is True


def test_match_is_digest_or_normal_form() -> None:
    index = Index()
    index.add("fixture", [_decl("isSquare", IS_SQUARE)])
    hits = index.matches(MOD_EQ)
    assert hits
    assert hits[0]["via"] == "normal_form"
    assert "cosine" in hits[0]


def test_segment_map_rewrites_mul_in_a_name() -> None:
    assert translate_identifier("comp_mul_left") == "comp_add_left"
    assert translate_identifier("HMul") == "HAdd"


def test_explicit_additive_name_skips_the_attr_block() -> None:
    assert explicit_additive_name(" (attr := simp, to_additive) dite_smul") == "dite_smul"
    assert explicit_additive_name("") is None


def test_transported_goal_keeps_the_exists_binder() -> None:
    transported = transport_signature(IS_SQUARE)
    assert transported is not None
    goal = goal_text(transported)
    assert goal is not None
    assert "∃ r : ℤ" in goal
    assert "∃ r, ℤ" not in goal


def test_namespaces_are_read_from_the_source() -> None:
    assert namespaces_of("namespace LeanFrontier.Int\ntheorem t : True := by trivial\n") == ["LeanFrontier.Int"]


def test_engineering_detail_drops_the_absolute_directory() -> None:
    detail = "/Users/a/probes-sprint6/foo.lean:20:33: error: unexpected type ascription"
    assert sanitize_detail(detail) == "foo.lean:20:33: error: unexpected type ascription"


def test_missing_corpus_does_not_score() -> None:
    report = not_measured("local Mathlib v4.34.0 tree not found")
    assert report["measured"] is False
    assert report["gaps"] == []
    assert report["controls"]["status"] == "not_measured"
    assert "Mathlib" in report["reason"]
