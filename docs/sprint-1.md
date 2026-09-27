# Sprint 1

## Exit

`uv run consilean-sprint1` ranks theorems and lemmas from the pin in [`corpora/leanfrontier.toml`](../corpora/leanfrontier.toml).

The tables are [`generated/sprint1-leanfrontier-79800a5.md`](generated/sprint1-leanfrontier-79800a5.md), written by that command. Do not copy the numbers into this file by hand.

The √−1 twin is the top pair under the preregistered score: the mean of the min-max normalized name-free Weisfeiler–Lehman cosine and the normal-form score. Its two statements do not have the same exact digest. Their normal forms match. The normal form is the curated one already named before this run: `IsSquare` of a `ZMod` element becomes an integer congruence, and `[ZMOD t.natAbs]` becomes `[ZMOD t]`. Binders are renamed in order.

Definitions and abbreviations are not in this ranking. Their result types are often a bare `ℕ`, and those identical types were outranking the twin. Sprint 1 asks for theorem types.

The notation equivalence is [`lean/IsSquareModEq.lean`](../lean/IsSquareModEq.lean). The proof is under ten lines. It was kernel-checked with Lean `v4.34.0` against the local Mathlib cache:

```bash
lake env lean lean/IsSquareModEq.lean
```

run from a Mathlib `v4.34.0` lake project. The LeanFrontier twin is that fact at `m = n.markovNumber`.

## What failed

The name-free kernel, on the statements as written, does not see the twin as the same formula. The keep-names variant is further away. The normal form is what puts the pair first. Both cosines are in the generated table.

Most theorem and lemma signatures do not parse. An unparsed signature gets a unique label, so it cannot match anything. The fragment is binders, quantifiers, the usual connectives, and `[ZMOD …]`. Elaborated `Expr` graphs were not built: LeanDojo and LeanExplore index Mathlib, not this LeanFrontier pin, and an exporter would mean building LeanFrontier.

The semantic arm was not run. This sprint spends no tokens, the local embedding model was not fetched, and MELD was not scored. It is not part of the primary rank.

Tactic probes were not run. They need the LeanFrontier environment, and running them in another checkout would write build files there. The far-near table therefore has no closed, open, or timeout column. What it does show is pairs whose raw name-free graphs match. Those are not the pilot's Paley–Zygmund, `reflect`, or Fibonacci-spine controls.

Dropping the highest in-degree modules, at the preregistered 1% and 5%, leaves the twin's modules at the same distance. The twin is a near pair.

## Not started

Sprints 2–5. Sprint 2 stays closed until a later run is ready to measure H2 and H3 with this score, including the pairs the fragment cannot parse.
