"""Coverage counts declarations and parse rate, and does not rank pairs."""

from pathlib import Path

from consilean.coverage.report import coverage_row


def test_coverage_row_counts_a_small_tree(tmp_path: Path) -> None:
    namespace = tmp_path / "Demo"
    namespace.mkdir()
    (namespace / "A.lean").write_text(
        "theorem t (n : Nat) : n = n := by rfl\n",
        encoding="utf-8",
    )
    (namespace / "B.lean").write_text("import Demo.A\n", encoding="utf-8")
    row = coverage_row(corpus="Demo", revision="abc", root=tmp_path, namespace="Demo")
    assert row["public_declarations"] == 1
    assert row["parsed"] == 1
    assert row["import_modules"] == 2
    assert row["internal_edges"] == 1
    assert "primary" not in row
