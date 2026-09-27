# Sprint 0

## Exit

`uv run consilean-baseline` regenerates the LeanFrontier pilot from the pin in [`corpora/leanfrontier.toml`](../corpora/leanfrontier.toml).

The tables are [`generated/leanfrontier-79800a5.md`](generated/leanfrontier-79800a5.md), written by that command. Do not copy the numbers into this file by hand. Tests lock the faithful figures. The hypotheses are in [`PREREGISTRATION.md`](PREREGISTRATION.md), recorded before any H1–H3 measurement.

## What the faithful pilots show

Both views rank the √−1 twin, and neither puts it in the top 10. That is Sprint 1's target. The generated far-near table contains the pilot's controls: the two Paley–Zygmund families, the two `reflect` declarations, the Lucas / Tribonacci / Padovan sum identities, and the Fibonacci spine next to a Horadam specialization.

## What failed

### Comment stripping

`strip_comments` belongs on the import scan. A block comment can contain a line that starts with `import`, and the faithful regex counts it as an edge. It also misses `public import` and `meta import`.

On this pin the corrected import graph has the same internal edge count as the faithful scan. Nothing in the pinned sources is a `public import` or a `meta import` of another LeanFrontier module, and no comment-hidden import changes the edge set. A unit test covers both of those cases on a fixture.

Running `strip_comments` over the text view also blanks `/--` docstrings. That variant is reported separately. It changes which declarations parse and where the twin ranks, and the twin stays outside the top 10. The locked text baseline keeps the docstrings.

### Instance constants

Dropping constants whose last component starts with `inst` moves the twin's rank and leaves it outside the top 10. The constants the two statements share are not `inst` names. The filter is a name heuristic, not an environment `isInstance` query. It does not find the duplicate.

## Not started

Sprints 1–5.
