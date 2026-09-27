"""Sprint 1 normal form, the name-free kernel, and the twin's rank."""

import json
import subprocess
from pathlib import Path

import pytest

from consilean.ingest.corpus import ensure_checkout, load_spec, repo_root
from consilean.sprint1.report import build_report, render_markdown
from consilean.views.syntax import formula_graph, normal_form, parse_statement
from consilean.views.wl import cosine, wl_features

ROOT = repo_root()
IS_SQUARE = " (n : OrientedNode) :\n    IsSquare (-1 : ZMod n.markovNumber.natAbs) "
MOD_EQ = " (n : OrientedNode) :\n    ∃ r : ℤ, r ^ 2 ≡ -1 [ZMOD n.markovNumber] "
MATHLIB = ROOT.parent / "mathlib-v4.34.0-reuse"


def test_normal_form_identifies_the_twin_notations() -> None:
    left = normal_form(IS_SQUARE)
    right = normal_form(MOD_EQ)
    assert left is not None
    assert left == right
    assert "IsSquare" not in left
    assert "natAbs" not in left
    assert "[ZMOD v0.markovNumber]" in left


def test_name_free_kernel_ignores_constant_names() -> None:
    foo = parse_statement("(n : T) : ∃ r : ℤ, r ^ 2 ≡ -1 [ZMOD n.foo]")
    bar = parse_statement("(n : T) : ∃ r : ℤ, r ^ 2 ≡ -1 [ZMOD n.bar]")
    assert foo is not None and bar is not None
    free = cosine(
        wl_features(*formula_graph(foo, keep_names=False)),
        wl_features(*formula_graph(bar, keep_names=False)),
    )
    named = cosine(
        wl_features(*formula_graph(foo, keep_names=True)),
        wl_features(*formula_graph(bar, keep_names=True)),
    )
    assert free == pytest.approx(1.0)
    assert named < 1.0


@pytest.fixture(scope="module")
def sprint1_report() -> dict:
    spec = load_spec(ROOT / "corpora" / "leanfrontier.toml")
    checkout = ensure_checkout(spec, ROOT / "corpora" / "cache" / "LeanFrontier")
    return build_report(checkout, spec)


def test_twin_is_in_the_top_10(sprint1_report: dict) -> None:
    twin = sprint1_report["twin"]
    assert twin is not None
    assert twin["rank"] <= 10
    assert twin["of"] > 10
    assert twin["normal_forms_equal"] is True
    assert twin["exact_digests_equal"] is False


def test_generated_sprint1_files_match(sprint1_report: dict) -> None:
    generated = ROOT / "docs" / "generated"
    json_path = generated / "sprint1-leanfrontier-79800a5.json"
    md_path = generated / "sprint1-leanfrontier-79800a5.md"
    assert json.loads(json_path.read_text(encoding="utf-8")) == sprint1_report
    assert md_path.read_text(encoding="utf-8") == render_markdown(sprint1_report)


def test_equivalence_proof_is_at_most_ten_lines() -> None:
    text = (ROOT / "lean" / "IsSquareModEq.lean").read_text(encoding="utf-8")
    proof = text.split(":= by\n", 1)[1].strip().splitlines()
    assert 1 <= len(proof) <= 10


@pytest.mark.skipif(not (MATHLIB / "lakefile.toml").is_file(), reason="Mathlib v4.34.0 cache is local")
def test_equivalence_is_kernel_checked() -> None:
    script = ROOT / "lean" / "IsSquareModEq.lean"
    result = subprocess.run(
        ["lake", "env", "lean", str(script)],
        cwd=MATHLIB,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
