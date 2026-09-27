# consilean

consilean scores pairs of formal statements in Lean corpora on two axes: how similar they are, and how far apart they sit in the dependency graph.

Similar statements that sit near each other are duplicate candidates. Similar statements that sit far apart are candidate hidden connections. Lean's kernel is the authority on whether a connection holds. A similarity score is a pattern, not a claim.

No claim of new mathematics is made.

## Status

Sprint 0 is done. This command regenerates the LeanFrontier pilot baselines from the pinned commit in [`corpora/leanfrontier.toml`](corpora/leanfrontier.toml):

```bash
uv run consilean-baseline
```

The numbers are written to `docs/generated/`. Sprints 1–5 have not started. The preregistered tests are in [`docs/PREREGISTRATION.md`](docs/PREREGISTRATION.md).

## Requirements

Python 3.12 and [uv](https://docs.astral.sh/uv/). The baseline fetches `carlok/LeanFrontier` at the pinned revision into `corpora/cache/` (not committed). Set `CONSILEAN_LEANFRONTIER` to a checkout of that exact commit to skip the fetch.

## Tests

```bash
uv run --frozen pytest
```
