"""A closed budget does not record a model call."""

from consilean.agents.budget import Budget, load_budget
from consilean.agents.cli import _reason
from consilean.ingest.corpus import repo_root


def test_default_budget_is_closed() -> None:
    budget = load_budget(repo_root() / "corpora" / "sprint3-budget.toml")
    assert budget == Budget(0, 0)
    assert budget.is_open is False
    assert "No call" in _reason(False) or "before any model call" in _reason(False)
