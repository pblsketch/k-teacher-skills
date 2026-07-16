"""School↔national achievement-standard alignment (VS3).

Emits a NEW national curriculum-record (Tier 0) for every school-plan code that
exactly matches the national provider, ADDITIVE to the school curriculum-context
record. Never mutates the school record's scope. Mismatch/ambiguity/missing-revision
quarantines with teacher-confirm. Enforces INV-1..5.
"""
from .aligner import (
    align_plan_codes_to_national,
    extract_codes,
    AlignmentResult,
    AlignedPair,
    QuarantineEntry,
)

__all__ = [
    "align_plan_codes_to_national",
    "extract_codes",
    "AlignmentResult",
    "AlignedPair",
    "QuarantineEntry",
]
