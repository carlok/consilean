"""Deprecations enter the frozen set only when the statements differ."""

from pathlib import Path

from consilean.replay.ground_truth import collect_ground_truth


def test_aliases_and_identical_statements_are_excluded(tmp_path: Path) -> None:
    mathlib = tmp_path / "Mathlib"
    mathlib.mkdir()
    (mathlib / "A.lean").write_text(
        "\n".join(
            [
                '@[deprecated (since := "2026-01-01")] alias oldName := newName',
                "",
                "theorem newName (n : Nat) : n = n := by rfl",
                "",
                '@[deprecated newName (since := "2026-02-01")]',
                "theorem same (n : Nat) : n = n := by rfl",
                "",
                '@[deprecated newName (since := "2026-03-01")]',
                "theorem different (n : Nat) : n = n + 0 := by rfl",
                "",
            ]
        ),
        encoding="utf-8",
    )
    frozen = collect_ground_truth(tmp_path)
    assert frozen["aliases_excluded"] == 1
    assert frozen["identical_statements_excluded"] == 1
    assert frozen["count"] == 1
    assert frozen["pairs"][0]["old"].endswith(".different")
    assert frozen["pairs"][0]["since"] == "2026-03-01"
    assert len(frozen["sha256"]) == 64
