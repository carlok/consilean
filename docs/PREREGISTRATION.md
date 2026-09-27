# Preregistration

Recorded before any measurement of H1, H2, or H3. The Sprint 0 baselines reproduce a pilot that was already run. They are not a test of these hypotheses.

A later change to this file is a dated amendment. Silent edits are not allowed.

Corpus for Sprint 0 and Sprint 1 LeanFrontier runs: `carlok/LeanFrontier` at `79800a5709a415e43230ffe1349bf89946f697c1`, Lean `v4.34.0`, Mathlib `v4.34.0`. The pin lives in [`corpora/leanfrontier.toml`](../corpora/leanfrontier.toml). Every run stores that revision, a seed, and a config file.

No claim of new mathematics is made.

## H1 — discovery

Statement pairs at hub-aware graph distance at least d. The top-k by the primary similarity score yield kernel-checked bridges at a higher rate than matched random pairs, at the same per-pair budget.

- Primary distance cutoff: **d = 4**. Also report d = 8 and the no-path bucket (no undirected path in the corpus import graph).
- Hub sensitivity, three settings, reported separately: drop the highest-degree 0%, 1%, and 5% of modules, and the same three fractions of constants.
- Primary score, once the Sprint 1 views exist: the mean of the min-max normalized **name-free Weisfeiler–Lehman** score and the **normal-form** score. Weights are not retuned after the twin's rank is known.
- Reported separately, and not part of the primary rank: exact digest, and the semantic embedding arm. The semantic arm is also scored on MELD.
- Primary k = 10. Also report k = 50 and k = 100.
- Matched random pairs: the same distance bucket, sampled without replacement, the same number of pairs, seed stored with the run.
- Sprint 1 probe budget, no tokens: for each direction `A ↔ B`, `A → B`, and `B → A`, the tactics `rfl`, `simp`, `norm_num`, `tauto`, `omega`, `decide`, `exact?`, `apply?`, `aesop`, `grind`, with a 10 second limit per tactic attempt. Record closed, open, or timeout.
- Sprints 0–2 spend no tokens. Sprint 3 does not start until the operator sets a per-pair token cap and a total cap.

## H2 — duplicates

Known duplicates are recovered as recall at k against a ground-truth set.

- Primary k = 10. Also report k = 1, 5, and 50.
- Sprint 0/1 control: the LeanFrontier √−1 twin, `isSquare_neg_one_mod_markovNumber` and `exists_sq_modEq_neg_one_markovNumber`. The statements differ.
- Mathlib ground truth is collected in Sprint 2 and frozen, with a count and a content hash, before any H2 score is computed. The set is deprecations and deduplication pull requests whose statements differ. Pure renames are excluded.

## H3 — replay

Replay the corpus in time slices. Top-ranked far pairs are later connected (by an import, a bridge, or a dedup) more often than matched random pairs.

- Windows: 1, 3, 6, and 12 months.
- Metric: precision at k against matched random pairs in the same distance bucket.
- Uncertainty: 1000 bootstrap resamples, 95% percentile interval. The seed and the config are stored with the run.
- Report the result for every window. A handful of famous links is not the evaluation.

## Amendment 2026-09-27

H2 recall at k is the fraction of frozen pairs whose partner is among the k nearest declarations to the old one. A single global top-k list cannot hold more true pairs than k, so it is not the recall of a set. The neighbor order is the one induced by the preregistered primary score: normal-form matches first, then name-free Weisfeiler–Lehman cosine. A tie does not push the partner down. The weights are unchanged.

## Stopping

Score the preregistered far set once. A miss on a sprint exit is written down as the result. It is not a reason to change the primary score in place. Do not start a sprint whose entry condition fails; write down why instead.
