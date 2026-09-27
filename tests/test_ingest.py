"""Comment stripping, the instance-name filter, and the corpus pin."""

import subprocess
from pathlib import Path

import pytest

from consilean.baselines.constants import is_instance_constant
from consilean.ingest.corpus import CorpusSpec, ensure_checkout, load_spec, repo_root
from consilean.ingest.declarations import load_declarations
from consilean.ingest.graph import faithful_module_graph
from consilean.vendor.import_graph import build


def test_corrected_importer_drops_comment_imports_and_keeps_public_import(tmp_path: Path) -> None:
    namespace = tmp_path / "LeanFrontier"
    namespace.mkdir()
    (namespace / "A.lean").write_text(
        "/-\nimport LeanFrontier.Hidden\n-/\npublic import LeanFrontier.B\n",
        encoding="utf-8",
    )
    (namespace / "B.lean").write_text("", encoding="utf-8")

    faithful = faithful_module_graph(tmp_path)
    assert faithful["LeanFrontier.A"] == ["LeanFrontier.Hidden"]

    corrected = build(tmp_path, "LeanFrontier")
    assert corrected["LeanFrontier.A"] == ["LeanFrontier.B"]


def test_strip_comments_blanks_docstrings_the_faithful_parser_keeps(tmp_path: Path) -> None:
    namespace = tmp_path / "LeanFrontier"
    namespace.mkdir()
    (namespace / "T.lean").write_text(
        "/-- The square root of minus one. -/\n"
        "theorem isSquare_neg_one_mod_markovNumber : True := by\n"
        "  trivial\n"
        "\n"
        "private theorem hidden : True := by\n"
        "  trivial\n",
        encoding="utf-8",
    )
    kept = load_declarations(tmp_path, blank_block_comments=False)
    assert [decl.name for decl in kept] == ["isSquare_neg_one_mod_markovNumber"]
    assert kept[0].docstring == "The square root of minus one."
    assert kept[0].kind == "theorem"

    blanked = load_declarations(tmp_path, blank_block_comments=True)
    assert blanked[0].name == "isSquare_neg_one_mod_markovNumber"
    assert blanked[0].docstring == ""


def test_instance_name_heuristic() -> None:
    assert is_instance_constant("instOfNatNat")
    assert is_instance_constant("Rat.instField")
    assert not is_instance_constant("HPow.hPow")
    assert not is_instance_constant("Neg.neg")


def test_spec_round_trip() -> None:
    spec = load_spec(repo_root() / "corpora" / "leanfrontier.toml")
    assert spec == CorpusSpec(
        repo="https://github.com/carlok/LeanFrontier",
        revision="79800a5709a415e43230ffe1349bf89946f697c1",
        namespace="LeanFrontier",
        lean="v4.34.0",
        mathlib="v4.34.0",
    )


def test_override_must_match_the_pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _git(checkout, ["init"])
    (checkout / "README").write_text("pin check\n", encoding="utf-8")
    _git(checkout, ["add", "README"])
    _git(checkout, ["-c", "user.email=consilean-test@example.com", "-c", "user.name=consilean-test", "commit", "-m", "init"])
    head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()

    monkeypatch.setenv("CONSILEAN_LEANFRONTIER", str(checkout))
    wrong = CorpusSpec(
        repo="https://example.invalid/corpus",
        revision="0" * 40,
        namespace="LeanFrontier",
        lean="v4.34.0",
        mathlib="v4.34.0",
    )
    with pytest.raises(SystemExit, match="pinned revision"):
        ensure_checkout(wrong, tmp_path / "cache")

    right = CorpusSpec(
        repo=wrong.repo,
        revision=head,
        namespace=wrong.namespace,
        lean=wrong.lean,
        mathlib=wrong.mathlib,
    )
    assert ensure_checkout(right, tmp_path / "cache") == checkout.resolve()


def _git(root: Path, args: list[str]) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
