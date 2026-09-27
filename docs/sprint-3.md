# Sprint 3

The agent is behind one interface. Nothing is called until [`corpora/sprint3-budget.toml`](../corpora/sprint3-budget.toml) has a positive per-pair cap and a positive total cap, and an assistant is configured. This run has neither.

`uv run consilean-sprint3` writes the first targets and a log line with outcome `not_called`. The targets are the section 5 controls. The A053067 row is the cross-project bridge from the plan. It is not a LeanFrontier pair, and it was not sent to a model.

Attempt order, when a budget exists: equivalence, implication, instance-of, common generalization. Failures are logged with the same fields as successes: prompt hash, model, tokens, cost, outcome.

H1 is not measured. No submission was made to LeanFrontier.

Sprints 4 and 5 have not started.
