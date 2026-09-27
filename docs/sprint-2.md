# Sprint 2

## H2

`uv run consilean-sprint2` freezes Mathlib deprecations whose statements differ, then measures recall at k. The tables are [`generated/sprint2-h2.md`](generated/sprint2-h2.md). The frozen pairs and their hash are in [`generated/sprint2-ground-truth.json`](generated/sprint2-ground-truth.json).

Aliases are excluded. So are pairs whose statements match after whitespace normalization. How recall at k is counted is the amendment of 27 September 2026 in [`PREREGISTRATION.md`](PREREGISTRATION.md).

Recall at the primary k is low. Most evaluated pairs are not recovered because a signature does not parse. Those count as misses.

## H3

Not measured. A replay needs a ranking of the corpus at past releases. This run does not check out those revisions. The `since` dates are on the frozen pairs.

## Duplicate list

[`generated/sprint2-duplicates.md`](generated/sprint2-duplicates.md) is empty. No equivalence was closed by the checker.

## Not started

Sprints 3–5.
