"""Secondary-material builder (VS4b).

Derives student-facing and teacher-facing documents from ONE shared registry inside
a single canonical lesson-package IR. Enforces teacher/student facet separation,
bidirectional teacher<->student alignment, and a teacher-approval gate before any
render is downstream-ready. Independent implementation (no anthropics code).
"""
from .builder import (
    SharedRegistry,
    build_material_ir,
    check_facet_separation,
    check_bidirectional_alignment,
    TeacherApprovalGate,
    STUDENT_FORBIDDEN_TERMS,
)
from . import worksheet
from .worksheet import (
    BLOCK_TYPES,
    build_worksheet_ir,
    worksheet_document,
    build_quick_draft_worksheet_ir,
    check_physical_workload,
    estimated_minutes,
    iter_block_string_leaves,
    iter_block_forbidden_keys,
    demo_worksheet_blocks,
    STANDALONE_QUICK_DRAFT_MARKER,
    STUDENT_FACET_FORBIDDEN_KEYS,
    FACET_LEAK_PATTERNS,
)

from .individualized import (
    IndividualizedPathway,
    IndividualizedLessonContext,
    GROUP_LABELS,
    build_individualized_package_ir,
    validate_individualized_package,
    check_cross_domain_grounding,
    individualization_contract,
    package_core_fingerprint,
    STUDENT_DIAGNOSTIC_TERMS,
)

__all__ = [
    "SharedRegistry",
    "build_material_ir",
    "check_facet_separation",
    "check_bidirectional_alignment",
    "TeacherApprovalGate",
    "STUDENT_FORBIDDEN_TERMS",
    "worksheet",
    "BLOCK_TYPES",
    "build_worksheet_ir",
    "worksheet_document",
    "build_quick_draft_worksheet_ir",
    "check_physical_workload",
    "estimated_minutes",
    "iter_block_string_leaves",
    "iter_block_forbidden_keys",
    "demo_worksheet_blocks",
    "STANDALONE_QUICK_DRAFT_MARKER",
    "STUDENT_FACET_FORBIDDEN_KEYS",
    "FACET_LEAK_PATTERNS",
    "IndividualizedPathway",
    "IndividualizedLessonContext",
    "GROUP_LABELS",
    "build_individualized_package_ir",
    "validate_individualized_package",
    "check_cross_domain_grounding",
    "individualization_contract",
    "package_core_fingerprint",
    "STUDENT_DIAGNOSTIC_TERMS",
]
