# Sprint 6

Transport asks what a checked bridge is good for. A statement moved across an `↔` by rewriting is provable by construction, so a transported proof is not a finding. The map has three parts: where a transported statement has no match, how many match a pinned corpus, and whether the image can be closed without the bridge lemma.

The definitions are the amendment of 5 October 2026 in [`PREREGISTRATION.md`](PREREGISTRATION.md). A match is exact digest equality or normal-form equality. Name-free cosine is stored and is not a gate.

## Entry

Sprint 4's cross-project index does not exist. This sprint is allowed because it builds the part it needs: digest and normal-form lookup over the corpora below. If the pinned Mathlib tree or the LeanFrontier cache is missing, `uv run consilean-sprint6` writes the reason and does not score.

## Corpora

Kernel checks use LeanFrontier at the pin in [`corpora/leanfrontier.toml`](../corpora/leanfrontier.toml), Lean and Mathlib `v4.34.0`.

Mathlib is pinned in [`corpora/mathlib.toml`](../corpora/mathlib.toml) to tag `v4.34.0`. The local tree is checked against that revision and is not checked out to another commit.

Tau Ceti stays the pin in [`corpora/tauceti.toml`](../corpora/tauceti.toml). It is text lookup only. Lean there is `v4.35.0-rc3`. A statement not elaborated in that toolchain is unportable.

Prove2Me's public repository is [`corpora/prove2me.toml`](../corpora/prove2me.toml), which points at `carlok/prove2me-logs`. That repository is journal entries. The local `missions` tree, when present, is declarations only: it is not one Lean package and has no import graph.

`erdos-straus-offset-lean`, `magma-1518-obstruction-lean`, `diaz-modulus-lean`, and the other local Mathlib projects next to this repository are not pinned. They are not part of the measurement until one of them has a public revision and a license note.

## Seed and control

The seed bridge is [`lean/IsSquareModEq.lean`](../lean/IsSquareModEq.lean). The neighbourhood is declarations in the pinned LeanFrontier whose signatures, not docstrings, meet an endpoint.

Rung 0 rewrites with that bridge and closes with the original theorem. A closure is an engineering check. Rung 1 uses the H1 tactic list at 10 seconds, with the bridge lemma out of scope. Rung 2 is a target list. No model is called.

The positive control is `to_additive` on the pinned Mathlib, if the attribute is there. `to_dual` is counted and is not a bridge. H4b is not measured: there is no kernel-rejected bridge. The month-window replay is not measured.

## Command

```bash
uv run consilean-sprint6
```

Tables, written by that command:

- [`generated/sprint6-gaps.md`](generated/sprint6-gaps.md) and [`generated/sprint6-gaps.json`](generated/sprint6-gaps.json)
- [`generated/sprint6-controls.md`](generated/sprint6-controls.md) and [`generated/sprint6-controls.json`](generated/sprint6-controls.json)
- [`generated/sprint6-unportable.md`](generated/sprint6-unportable.md)
- [`generated/sprint6-rung2-targets.md`](generated/sprint6-rung2-targets.md)

## Exit

The command has run once. H4a is the gap table. The control table is either a recall or a record that `to_additive` is absent. Rung 2 has no calls. H1, preregistered H3 precision at k, H4b, the month-window replay, and elaboration in Tau Ceti stay unmeasured.

## Still unmeasured

H1. Preregistered H3 precision at k. H4b. The 1/3/6/12-month replay. Rung 2 calls. Elaboration inside Tau Ceti and Prove2Me.
