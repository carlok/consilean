"""First Sprint 3 targets. These are the section 5 controls, not a new ranking."""

# (label, left short name, right short name)
FIRST_TARGETS: list[tuple[str, str, str]] = [
    ("fibonacci-spine-horadam", "W_fibonacci_eq_fib", "markovFib_vieta_recurrence"),
    ("paley-measure-finite", "MeasurePaleyZygmund.paleyZygmund", "PaleyZygmund.paleyZygmund"),
    ("paley-measure-pmf", "MeasurePaleyZygmund.paleyZygmund", "pmf_paleyZygmund"),
    ("lucas-tribonacci", "sum_range_lucas", "tribonacci_two_mul_sum_add_one"),
    ("lucas-padovan", "sum_range_lucas", "padovan_sum_add_two"),
    ("tribonacci-padovan", "tribonacci_two_mul_sum_add_one", "padovan_sum_add_two"),
    ("reflect", "InversiveGeometry.reflect_reflect", "DescartesCircle.reflect_reflect"),
    (
        "a053067",
        "A053067 residue / natFixedA",
        "formal-conjectures OEIS a",
    ),
]

ATTEMPT_ORDER = ("equivalence", "implication", "instance_of", "common_generalization")
