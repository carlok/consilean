# consilean

consilean scores pairs of formal statements in Lean corpora on two axes: how similar they are, and how far apart they sit in the dependency graph.

Similar statements that sit near each other are duplicate candidates. Similar statements that sit far apart are candidate hidden connections. Lean's kernel is the authority on whether a connection holds. A similarity score is a pattern, not a claim.

No claim of new mathematics is made.

## Origin

The question comes from [@qazW12345](https://github.com/qazW12345). On [LeanFrontier pull request 340](https://github.com/carlok/LeanFrontier/pull/340) he described an idea he had shelved: embed mathematics papers, then look for pairs that are close in the embedding and far apart in the citation graph, and point an agent at those pairs. He set it aside because of token cost, the expertise required, and licensing.

The reply on that thread suggested trying the idea where a checker can judge it. Use Lean corpora first: the dependency graph is exact, there is no licensing question, and a proof checker can decide whether a suggested connection is real. Alongside that, build a cross-project index of statement fingerprints so projects stop duplicating each other.

consilean is that experiment. qazW12345 is credited as the origin of the question. Contributions are welcome.

## Status

Sprint 0 regenerates the LeanFrontier pilot baselines:

```bash
uv run consilean-baseline
```

Sprint 1 ranks theorems and lemmas with the preregistered score (name-free Weisfeiler–Lehman, plus a normal form that sends `IsSquare` in `ZMod` to an integer congruence):

```bash
uv run consilean-sprint1
```

On the pinned corpus the √−1 twin is the top pair. The notation equivalence is kernel-checked in [`lean/IsSquareModEq.lean`](lean/IsSquareModEq.lean). Tactic probes of the far-near controls are in [`docs/generated/sprint1-probes.md`](docs/generated/sprint1-probes.md): none closed. A coverage smoke of Mathlib, Prove2Me, and Tau Ceti, with no pair ranking, is in [`docs/generated/coverage.md`](docs/generated/coverage.md). The semantic arm was not run.

Sprint 2 freezes Mathlib deprecations whose statements differ, then measures H2 recall at k. Aliases and identical statements are excluded. The result is in [`docs/generated/sprint2-h2.md`](docs/generated/sprint2-h2.md). H3 replay was not measured: every frozen `since` date is already earlier than that Mathlib revision. The checker-closed duplicate list is empty.

```bash
uv run consilean-sprint2
```

Sprint 3 lists the section 5 controls and does not call a model. The budget in [`corpora/sprint3-budget.toml`](corpora/sprint3-budget.toml) is closed until both caps are set above zero.

```bash
uv run consilean-sprint3
```

Sprints 4 and 5 have not started. H1 is not measured.

Tables are written to `docs/generated/`. The preregistered tests, including the 27 September amendment on how recall at k is counted, are in [`docs/PREREGISTRATION.md`](docs/PREREGISTRATION.md).

## Requirements

Python 3.12 and [uv](https://docs.astral.sh/uv/). The baseline fetches `carlok/LeanFrontier` at the pinned revision into `corpora/cache/` (not committed). Set `CONSILEAN_LEANFRONTIER` to a checkout of that exact commit to skip the fetch.

The equivalence check uses a local Mathlib `v4.34.0` lake project, when one is present next to this repository as `mathlib-v4.34.0-reuse`.

## Tests

```bash
uv run --frozen pytest
```
