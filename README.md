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

On the pinned corpus the √−1 twin is the top pair. The notation equivalence is kernel-checked in [`lean/IsSquareModEq.lean`](lean/IsSquareModEq.lean). The semantic arm and the tactic probes were not run. Sprints 2–5 have not started.

Tables are written to `docs/generated/`. The preregistered tests are in [`docs/PREREGISTRATION.md`](docs/PREREGISTRATION.md).

## Requirements

Python 3.12 and [uv](https://docs.astral.sh/uv/). The baseline fetches `carlok/LeanFrontier` at the pinned revision into `corpora/cache/` (not committed). Set `CONSILEAN_LEANFRONTIER` to a checkout of that exact commit to skip the fetch.

The equivalence check uses a local Mathlib `v4.34.0` lake project, when one is present next to this repository as `mathlib-v4.34.0-reuse`.

## Tests

```bash
uv run --frozen pytest
```
