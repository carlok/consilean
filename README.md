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

Sprint 2 freezes Mathlib deprecations whose statements differ, then measures H2 recall at k. Aliases and identical statements are excluded. The first result is [`docs/generated/sprint2-h2.md`](docs/generated/sprint2-h2.md). A second ranking of that same frozen set, after a wider statement reader, is [`docs/generated/sprint2-h2-run2.md`](docs/generated/sprint2-h2-run2.md). Neighbor recall of those pairs on Mathlib `v4.28.0`, extracted read-only, is [`docs/generated/sprint2-h3.md`](docs/generated/sprint2-h3.md). That is not the preregistered precision-at-k comparison. Tactic probes of the pairs recovered at k = 10 in the first H2 run are in [`docs/generated/sprint2-recovered-probes.json`](docs/generated/sprint2-recovered-probes.json). None closed, so [`docs/generated/sprint2-duplicates.md`](docs/generated/sprint2-duplicates.md) stays empty.

```bash
uv run consilean-sprint2
```

Sprint 3 lists the section 5 controls and does not call a model. The budget in [`corpora/sprint3-budget.toml`](corpora/sprint3-budget.toml) is closed until both caps are set above zero.

```bash
uv run consilean-sprint3
```

H1 is not measured.

Tables are written to `docs/generated/`. The preregistered tests, including the 27 September amendment on how recall at k is counted, are in [`docs/PREREGISTRATION.md`](docs/PREREGISTRATION.md).

## Future

Sprint 3 calls stay blocked until both caps in [`corpora/sprint3-budget.toml`](corpora/sprint3-budget.toml) are set and an assistant is chosen. The targets are already in [`docs/generated/sprint3-targets.md`](docs/generated/sprint3-targets.md). H1 is the measurement after calls exist.

Sprint 4 is a cross-project index: digests, near-duplicate clusters, recorded bridges, and a query for whether a statement is already somewhere. Mathlib, Tau Ceti, and Prove2Me have only been counted.

Sprint 5 is papers, and only after a positive H1 or a positive result on the preregistered H3 metric.

Sprint 6 transports statements across a checked bridge and asks whether the image already matches a pinned corpus. The full Sprint 4 index does not exist. This sprint builds the smaller lookup it needs: exact digest and normal form across the pinned corpora. Definitions, skips, and commands are in [`docs/sprint-6.md`](docs/sprint-6.md). Tables are [`docs/generated/sprint6-gaps.md`](docs/generated/sprint6-gaps.md), [`docs/generated/sprint6-controls.md`](docs/generated/sprint6-controls.md), [`docs/generated/sprint6-unportable.md`](docs/generated/sprint6-unportable.md), and [`docs/generated/sprint6-rung2-targets.md`](docs/generated/sprint6-rung2-targets.md).

```bash
uv run consilean-sprint6
```

Nothing is submitted to LeanFrontier until a probe or a checked proof closes a bridge. That repo is not edited from here.

## Requirements

Python 3.12 and [uv](https://docs.astral.sh/uv/). The baseline fetches `carlok/LeanFrontier` at the pinned revision into `corpora/cache/` (not committed). Set `CONSILEAN_LEANFRONTIER` to a checkout of that exact commit to skip the fetch.

The equivalence check uses a local Mathlib `v4.34.0` lake project, when one is present next to this repository as `mathlib-v4.34.0-reuse`.

## Tests

```bash
uv run --frozen pytest
```
