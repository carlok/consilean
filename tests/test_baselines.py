"""The Sprint 0 pilots regenerate the locked LeanFrontier figures."""

import json
from pathlib import Path

import pytest

from consilean.baselines.report import build_report, render_markdown
from consilean.ingest.corpus import ensure_checkout, load_spec, repo_root

ROOT = repo_root()
SHARED = [
    "LeanFrontier.MarkovTree.OrientedNode",
    "LeanFrontier.MarkovTree.OrientedNode.markovNumber",
    "Neg.neg",
    "OfNat.ofNat",
]


@pytest.fixture(scope="session")
def report() -> dict:
    spec = load_spec(ROOT / "corpora" / "leanfrontier.toml")
    checkout = ensure_checkout(spec, ROOT / "corpora" / "cache" / "LeanFrontier")
    return build_report(checkout, spec)


def test_faithful_text_baseline(report: dict) -> None:
    text = report["faithful"]["text"]
    assert text["modules"] == 89
    assert text["public_declarations"] == 451
    assert text["directed_internal_import_edges"] == 72
    assert text["pairs_above_cutoff"] == 888
    twin = text["twin"]
    assert twin["rank"] == 163
    assert twin["of"] == 888
    assert f"{twin['score']:.2f}" == "0.41"
    assert text["top_similar"][0]["left"].endswith("CalkinWilf.pair_positive_coprime")
    assert text["top_similar"][0]["right"].endswith("SternBrocot.pair_positive_coprime")


def test_faithful_constants_baseline(report: dict) -> None:
    constants = report["faithful"]["constants"]
    assert constants["entrypoints"] == 264
    assert constants["pairs"] == 34716
    twin = constants["twin"]
    assert twin["rank"] == 5307
    assert twin["of"] == 34716
    assert f"{twin['score']:.2f}" == "0.08"
    assert twin["shared_constants"] == SHARED
    assert len(twin["shared_constants"]) == 4


def test_generated_files_match_the_fresh_report(report: dict) -> None:
    generated = ROOT / "docs" / "generated"
    json_path = generated / "leanfrontier-79800a5.json"
    md_path = generated / "leanfrontier-79800a5.md"
    assert json.loads(json_path.read_text(encoding="utf-8")) == report
    assert md_path.read_text(encoding="utf-8") == render_markdown(report)


def test_corrected_views_still_see_the_twin(report: dict) -> None:
    corrected = report["corrected"]
    assert corrected["import_graph"]["modules"] == 89
    stripped = corrected["text_strip_comments"]["twin"]
    dropped = corrected["constants_drop_instances"]["twin"]
    assert stripped is not None and stripped["rank"] >= 1
    assert dropped is not None and dropped["rank"] >= 1
    for constant in dropped["shared_constants"] + dropped["only_is_square"] + dropped["only_mod_eq"]:
        assert not constant.rsplit(".", 1)[-1].startswith("inst")
