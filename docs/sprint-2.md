# Sprint 2

## H2

`uv run consilean-sprint2` freezes Mathlib deprecations whose statements differ, then measures recall at k. That first table is [`generated/sprint2-h2.md`](generated/sprint2-h2.md). The frozen pairs and their hash are in [`generated/sprint2-ground-truth.json`](generated/sprint2-ground-truth.json).

Aliases are excluded. So are pairs whose statements match after whitespace normalization. How recall at k is counted is the amendment of 27 September 2026 in [`PREREGISTRATION.md`](PREREGISTRATION.md).

A later reader accepts more of the frozen signatures. `uv run consilean-sprint2 --label run2` scores the same frozen set again and writes [`generated/sprint2-h2-run2.md`](generated/sprint2-h2-run2.md). It does not replace the first table or the freeze. Unparsed signatures still count as misses.

## H3

The frozen `since` dates all fall before the Mathlib revision used for H2, so none of those pairs is a later link relative to that revision.

`uv run consilean-h3` extracts Mathlib `v4.28.0` with `git archive` into the gitignored cache and ranks the frozen pairs there. The checkout is not moved. Windows are 1, 3, 6, and 12 months after 2026-02-16. The table is [`generated/sprint2-h3.md`](generated/sprint2-h3.md). A declaration missing from that snapshot is not recovered. Bootstrap intervals for recall at 10 are in [`generated/sprint2-h3.json`](generated/sprint2-h3.json).

That table is neighbor recall of the frozen deprecations. The preregistered H3 metric, precision at k against random pairs in the same distance bucket, is still unmeasured.

## Duplicate list

[`generated/sprint2-duplicates.md`](generated/sprint2-duplicates.md) is empty. `uv run consilean-h2-probes` ran the Sprint 1 tactic budget on the pairs the first H2 run recovered at k = 10. The outcomes are [`generated/sprint2-recovered-probes.json`](generated/sprint2-recovered-probes.json). No direction closed, so the list was not given a row.
