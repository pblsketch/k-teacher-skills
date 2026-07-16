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

__all__ = [
    "SharedRegistry",
    "build_material_ir",
    "check_facet_separation",
    "check_bidirectional_alignment",
    "TeacherApprovalGate",
    "STUDENT_FORBIDDEN_TERMS",
]
