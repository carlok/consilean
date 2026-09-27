import Mathlib.Data.Int.ModEq
import Mathlib.Data.ZMod.Basic

/-- The two notations of the √−1 twin.

`IsSquare (-1)` in `ZMod |m|` is the integer congruence
`r ^ 2 ≡ -1 [ZMOD m]`. The LeanFrontier pair is this fact at
`m = n.markovNumber`. No claim of new mathematics is made.
-/
theorem isSquare_neg_one_zmod_iff_sq_modEq (m : ℤ) :
    IsSquare (-1 : ZMod m.natAbs) ↔ ∃ r : ℤ, r ^ 2 ≡ -1 [ZMOD m] := by
  simp only [IsSquare, ZMod.exists, pow_two]
  refine exists_congr fun r => ?_
  rw [← Int.cast_mul, eq_comm]
  rw [show (-1 : ZMod m.natAbs) = ↑(-1 : ℤ) by simp, ZMod.intCast_eq_intCast_iff]
  simp [Int.ModEq]
