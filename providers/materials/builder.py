"""Build student/teacher facet documents from one shared registry into a valid IR."""
from __future__ import annotations

from dataclasses import dataclass, field

# Teacher-only language that must NEVER appear in a student-facing document.
STUDENT_FORBIDDEN_TERMS = ["루브릭", "배점", "오개념", "misconception", "scaffold", "tier", "교사용", "관찰 기록", "미제출", "채점"]


@dataclass
class SharedRegistry:
    """Single source of truth. Student and teacher documents both reference it."""
    standard_code: str
    standard_student_language: str            # student-safe restatement
    standard_teacher_text: str                # authoritative national text (teacher only)
    tasks: list = field(default_factory=list)  # [{task_id,title,student_instructions,teacher_notes,writing_space}]
    success_criteria: list = field(default_factory=list)   # student-language "I can ..." checks
    exit_ticket: dict = field(default_factory=dict)        # {prompt, targets_hardest_case}
    misconceptions: list = field(default_factory=list)     # [{what,why,teacher_response}] teacher-only
    rubric: list = field(default_factory=list)             # [{criterion, levels}] teacher-only
    parent_summary: str | None = None


def _doc(document_id, document_class, title, task_ids, sections, facet):
    return {
        "document_id": document_id,
        "document_class": document_class,
        "title": title,
        "source_task_ids": task_ids,
        "render_targets": ["hwpx", "docx", "html"],
        "content": {
            "facet": facet,
            "sections": sections,
            "provenance_markers": [],
            "unresolved_boundary_markers": [],
        },
    }


def _sec(cid, text):
    return {"content_id": cid, "text": text}


def student_documents(shared: SharedRegistry) -> list:
    task_ids = [t["task_id"] for t in shared.tasks]
    # 과제안내 + 활동지 (worksheet): student instructions + writing space cues, student-language goal.
    worksheet_secs = [_sec("student-goal", f"오늘의 목표: {shared.standard_student_language}")]
    for t in shared.tasks:
        worksheet_secs.append(_sec(f"task-{t['task_id']}", f"{t['title']}: {t['student_instructions']}"))
        if t.get("writing_space"):
            worksheet_secs.append(_sec(f"write-{t['task_id']}", "[ 여기에 답을 씁니다 __________________________ ]"))
    # 자기점검 (assessment): success criteria as student self-check + exit ticket.
    selfcheck_secs = [_sec("selfcheck-title", "스스로 점검하기")]
    for i, sc in enumerate(shared.success_criteria):
        selfcheck_secs.append(_sec(f"can-{i}", f"□ {sc}"))
    if shared.exit_ticket:
        selfcheck_secs.append(_sec("exit-ticket", f"마무리 질문: {shared.exit_ticket.get('prompt','')}"))
    return [
        _doc("stu-worksheet", "worksheet", "학생 활동지", task_ids, worksheet_secs, "student"),
        _doc("stu-selfcheck", "assessment", "학생 자기점검", task_ids, selfcheck_secs, "student"),
    ]


def teacher_documents(shared: SharedRegistry) -> list:
    task_ids = [t["task_id"] for t in shared.tasks]
    # 운영안 (teacher-guide): authoritative standard text + teacher notes per task.
    guide_secs = [
        _sec("standard", f"성취기준 {shared.standard_code}: {shared.standard_teacher_text}"),
    ]
    for t in shared.tasks:
        guide_secs.append(_sec(f"tguide-{t['task_id']}", f"{t['title']} 운영: {t['teacher_notes']}"))
    for i, mc in enumerate(shared.misconceptions):
        guide_secs.append(_sec(f"mis-{i}", f"오개념: {mc['what']} / 원인: {mc['why']} / 대응: {mc['teacher_response']}"))
    # 루브릭 (rubric).
    rubric_secs = [_sec("rubric-title", "채점 루브릭")]
    for i, r in enumerate(shared.rubric):
        rubric_secs.append(_sec(f"rubric-{i}", f"{r['criterion']} 배점: {'/'.join(r['levels'])}"))
    # 관찰/피드백/미제출 체크리스트.
    checklist_secs = [
        _sec("obs", "관찰 기록: 각 모둠의 근거 사용 관찰"),
        _sec("feedback", "피드백: 성공 기준별 즉시 피드백"),
        _sec("missing", "미제출 체크: 미제출 학생 후속 지도"),
    ]
    return [
        _doc("tea-guide", "teacher-guide", "교사 운영안", task_ids, guide_secs, "teacher"),
        _doc("tea-rubric", "rubric", "교사 루브릭", task_ids, rubric_secs, "teacher"),
        _doc("tea-checklist", "teacher-guide", "교사 체크리스트", task_ids, checklist_secs, "teacher"),
    ]


def parent_documents(shared: SharedRegistry) -> list:
    if not shared.parent_summary:
        return []
    return [_doc("par-notice", "brief", "학부모 안내", [t["task_id"] for t in shared.tasks],
                 [_sec("parent", shared.parent_summary)], "parent")]


def build_material_ir(shared: SharedRegistry, base_ir: dict, *, include_parent: bool = False) -> dict:
    """Compose a schema-valid lesson-package IR with student+teacher(+parent) documents,
    reusing base_ir's approved envelope/provider_contract/provenance_ledger."""
    ir = {k: v for k, v in base_ir.items() if k != "lesson_package"}
    docs = student_documents(shared) + teacher_documents(shared)
    if include_parent:
        docs += parent_documents(shared)
    tasks = [{"task_id": t["task_id"], "title": t["title"], "document_ids": [d["document_id"] for d in docs]} for t in shared.tasks]
    ir["lesson_package"] = {"package_id": "pkg-materials", "tasks": tasks, "documents": docs}
    return ir


def check_facet_separation(ir: dict) -> tuple[bool, list]:
    """No teacher-only language in any student-facet document."""
    violations = []
    for doc in ir["lesson_package"]["documents"]:
        if doc["content"].get("facet") != "student":
            continue
        blob = " ".join(s["text"] for s in doc["content"]["sections"])
        for term in STUDENT_FORBIDDEN_TERMS:
            if term in blob:
                violations.append(f"{doc['document_id']}: forbidden teacher term '{term}'")
    return (len(violations) == 0, violations)


def check_bidirectional_alignment(ir: dict) -> tuple[bool, list]:
    """Every student task appears in a teacher document and vice versa."""
    issues = []
    student_tasks: set = set()
    teacher_tasks: set = set()
    for doc in ir["lesson_package"]["documents"]:
        facet = doc["content"].get("facet")
        if facet == "student":
            student_tasks |= set(doc["source_task_ids"])
        elif facet == "teacher":
            teacher_tasks |= set(doc["source_task_ids"])
    for t in student_tasks - teacher_tasks:
        issues.append(f"student task {t} missing from teacher docs")
    for t in teacher_tasks - student_tasks:
        issues.append(f"teacher task {t} missing from student docs")
    return (len(issues) == 0, issues)


@dataclass
class ApprovalResult:
    downstream_ready: bool
    reason: str


class TeacherApprovalGate:
    """A render is downstream-ready only when a valid teacher approval exists AND
    facet separation + bidirectional alignment pass. Approval carries no PII."""

    @staticmethod
    def evaluate(ir: dict, approval: dict | None) -> ApprovalResult:
        facet_ok, fviol = check_facet_separation(ir)
        align_ok, aissue = check_bidirectional_alignment(ir)
        if not facet_ok:
            return ApprovalResult(False, "facet separation violated: " + "; ".join(fviol))
        if not align_ok:
            return ApprovalResult(False, "bidirectional alignment failed: " + "; ".join(aissue))
        if not approval:
            return ApprovalResult(False, "no teacher approval -> render blocked (fail-closed)")
        if approval.get("decision") != "approved" or approval.get("approver_role") != "teacher":
            return ApprovalResult(False, f"invalid approval: {approval.get('decision')}/{approval.get('approver_role')}")
        return ApprovalResult(True, f"approved by teacher approval {approval.get('approval_id')}")
