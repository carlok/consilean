"""Window arithmetic for the H3 replay. No Mathlib tree required."""

from datetime import date

from consilean.replay.h3 import add_months, window_pairs
from consilean.views.syntax import parse_statement


def test_windows_are_calendar_months_after_the_snapshot() -> None:
    start = date(2026, 2, 16)
    assert add_months(start, 1) == date(2026, 3, 16)
    assert add_months(start, 3) == date(2026, 5, 16)
    assert add_months(start, 6) == date(2026, 8, 16)
    assert add_months(start, 12) == date(2027, 2, 16)


def test_a_pair_on_the_snapshot_date_is_outside_every_window() -> None:
    pairs = [{"since": "2026-02-16", "old": "a", "new": "b"}]
    assert window_pairs(pairs, date(2026, 2, 16), date(2026, 3, 16)) == []


def test_precision_uses_only_the_prefix() -> None:
    from consilean.replay.h3_precision import _precision

    assert _precision([True, False, False]) == 1 / 3
    assert _precision([]) is None


def test_a_deprecation_connects_only_inside_its_window() -> None:
    from datetime import date

    from consilean.replay.h3_precision import _connected

    row = {"names": ("Mathlib.A.old", "Mathlib.B.new")}
    links = {frozenset(row["names"]): date(2026, 4, 1)}
    start = date(2026, 2, 16)
    assert _connected(row, links, start, date(2026, 3, 16)) is False
    assert _connected(row, links, start, date(2026, 5, 16)) is True


def test_untyped_binders_and_fun_parse() -> None:
    binders = parse_statement("{h₁ h₂} (x : M) : h₁ = h₂")
    arrow = parse_statement("(f : M →+* N) : f = f")
    function = parse_statement("(f : α → β) : (fun x => f x) = f")
    assert binders is not None
    assert arrow is not None
    assert function is not None
