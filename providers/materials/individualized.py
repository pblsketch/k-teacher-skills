"""개별화 (individualized) material package provider.

Assembles ONE teacher operations plan (`teacher-individualized-plan`) and THREE
student worksheets (`worksheet-group-a/b/c`) from a single `SharedRegistry` into the
canonical lesson-package IR. It does NOT introduce a parallel IR or renderer: the
teacher plan and student worksheets are ordinary documents on the existing IR, reusing
the worksheet block vocabulary, the facet-separation gate, and the physical-workload gate.

Contract, enforced by `validate_individualized_package`:
  - the common goal, tasks, success criteria and hardest-case exit ticket are IDENTICAL
    across every group; only student-safe supports and response guidance differ;
  - student worksheets carry a neutral `Group A|B|C` label and NEVER any diagnostic,
    internal-level or teacher-profile language;
  - the teacher plan alone carries pathway meanings and rigor evidence;
  - an extension move must change the cognitive operation, never add quantity only.

The Korean user-facing term used here is 개별화.
Independent implementation (no vendored third-party code).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

from . import worksheet
from .builder import SharedRegistry, check_facet_separation  # re-exported dependencies

# Neutral student-facing group labels. Nothing else may appear on a student worksheet.
GROUP_LABELS = ("Group A", "Group B", "Group C")

TEACHER_DOC = "teacher-individualized-plan"
DOC_GROUP = {"Group A": "worksheet-group-a", "Group B": "worksheet-group-b", "Group C": "worksheet-group-c"}

# Diagnostic / internal grouping phrases that must never surface in a student
# worksheet. Bare curriculum words (for example 표준편차, 기초 대사량, 진단검사)
# remain valid subject content; only phrases that disclose an internal pathway are blocked.
STUDENT_DIAGNOSTIC_TERMS = [
    "기초단계", "기초경로", "기초그룹", "기초모둠",
    "표준단계", "표준경로", "표준그룹", "표준모둠",
    "심화단계", "심화경로", "심화과정", "심화그룹", "심화모둠",
    "수준별이동", "수준별그룹", "진단결과", "진단그룹",
    "below", "tier", "scaffold",
]

_ORD = {"recall": 1, "apply": 2, "analyze": 3, "evaluate": 4, "create": 5}
_COGNITIVE_LABELS = {"recall": "기억", "apply": "적용", "analyze": "분석", "evaluate": "평가", "create": "창안"}


@dataclass
class IndividualizedPathway:
    """One group's individualized supports. Teacher-only meaning (profile label, rigor
    evidence) is kept apart from the student-safe supports."""
    group_label: str
    teacher_profile_label: str
    access_supports: list = field(default_factory=list)
    representation_supports: list = field(default_factory=list)
    response_options: list = field(default_factory=list)
    rigor_evidence: str = ""
    extension_move: dict | None = None

    def __post_init__(self) -> None:
        if self.group_label not in GROUP_LABELS:
            raise ValueError(f"group_label must be one of {GROUP_LABELS}, got {self.group_label!r}")
        if not str(self.teacher_profile_label).strip():
            raise ValueError(f"{self.group_label}: teacher_profile_label is required")
        if not str(self.rigor_evidence).strip():
            raise ValueError(f"{self.group_label}: rigor_evidence is required (rigor must be provably preserved)")
        if self.extension_move is not None:
            if not isinstance(self.extension_move, dict) or "cognitive_operation" not in self.extension_move or "move" not in self.extension_move:
                raise ValueError(f"{self.group_label}: extension_move must carry cognitive_operation and move")

# --- structured classroom/document context (backward-compatible canonical input) ---
# Renders identically into every format as real tables/grids/answer areas. Carries the
# instructionally real, subject-grounded content a printable operating plan and student
# worksheet require. Existing minimal callers keep working; the release/golden fixture
# MUST supply real (non-placeholder) content.

# Visible table captions shared by the provider and its field-readiness validators.
CAP_OVERVIEW = "수업 개요"
CAP_SUCCESS_TEACHER = "공통 성공 기준·평가 근거"
CAP_FLOW = "45분 수업 흐름"
CAP_MATRIX = "모둠별 배치 비교 (Group A·B·C)"
CAP_REGROUP = "유연한 재편성 규칙"
CAP_OBSERVE = "관찰·피드백 기록표"
CAP_INTERPRET = "출구표 해석과 다음 단계"
CAP_HEADER = "학습자 정보"
CAP_SUCCESS_STUDENT = "성공 기준 자기 점검"
CAP_SOURCE = "대기권 층상 구조 자료 (교사 제작 학습자료)"
CAP_SELFCHECK = "스스로 점검"

# Generic phrasing that must never reach a student worksheet as "content".
_PLACEHOLDER_STRINGS = ("학급 제공 자료", "그림과 표로 정보를 함께 제시한다", "제공된 자료를 사용합니다")


@dataclass
class IndividualizedLessonContext:
    """Structured, subject-grounded classroom + document context for one lesson.

    Backward-compatible canonical input: it is serialized onto each document's content
    as `lesson_context` (metadata for the grounding gate) and expanded into real
    tables/grids/answer areas by the renderers. `lesson_phases` minutes MUST sum to
    `lesson_minutes`. Source content is teacher-created learning data, not an official
    quotation."""
    subject: str                      # 과학
    unit: str                         # 대기권과 기상
    grade: str                        # 중학교 3학년
    school_level: str                 # 중학교 (physical-workload period)
    standard_code: str                # [9과17-01]
    lesson_minutes: int               # 45
    materials: list                   # 준비물
    source_data: dict                 # {caption, headers, cells} — atmosphere layers
    source_card: dict                 # {title, body, source} — radiation/greenhouse card
    lesson_phases: list               # [{phase, minutes, teacher_move, student_action, evidence}]
    observation_criteria: list        # short observable-criteria column labels
    submission_instruction: str
    date_field_label: str = "수업 일자"

    def __post_init__(self) -> None:
        for name in ("subject", "unit", "grade", "school_level", "standard_code", "submission_instruction"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"IndividualizedLessonContext.{name} is required")
        if int(self.lesson_minutes) <= 0:
            raise ValueError("lesson_minutes must be positive")
        total = sum(int(p["minutes"]) for p in self.lesson_phases)
        if total != int(self.lesson_minutes):
            raise ValueError(f"lesson phase minutes {total} must sum to lesson_minutes {self.lesson_minutes}")
        for req in ("caption", "headers", "cells"):
            if req not in self.source_data:
                raise ValueError(f"source_data must carry {req}")
        if len(self.source_data["cells"]) < 4:
            raise ValueError("source_data must list all four atmosphere layers (>=4 rows)")
        for req in ("title", "body", "source"):
            if not str(self.source_card.get(req, "")).strip():
                raise ValueError(f"source_card must carry {req}")
        if len(self.observation_criteria) < 2:
            raise ValueError("observation_criteria needs at least two observable criteria")
        blob = json.dumps(self.to_dict(), ensure_ascii=False)
        for ph in _PLACEHOLDER_STRINGS:
            if ph in blob:
                raise ValueError(f"lesson context must not contain placeholder text {ph!r}")

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "unit": self.unit,
            "grade": self.grade,
            "school_level": self.school_level,
            "standard_code": self.standard_code,
            "lesson_minutes": int(self.lesson_minutes),
            "materials": list(self.materials),
            "source_data": {
                "caption": self.source_data["caption"],
                "headers": list(self.source_data["headers"]),
                "cells": [list(r) for r in self.source_data["cells"]],
            },
            "source_card": dict(self.source_card),
            "lesson_phases": [dict(p) for p in self.lesson_phases],
            "observation_criteria": list(self.observation_criteria),
            "submission_instruction": self.submission_instruction,
            "date_field_label": self.date_field_label,
        }


def _sec(cid: str, text: str) -> dict:
    return {"content_id": cid, "text": text}


def _core_tasks(shared: SharedRegistry) -> list:
    return [
        {"task_id": t["task_id"], "prompt": t["student_instructions"], "cognitive_demand": t.get("cognitive_demand", "analyze")}
        for t in shared.tasks
    ]


def _hardest_demand(core: list) -> str:
    return max(core, key=lambda t: _ORD[t["cognitive_demand"]])["cognitive_demand"]


def _iter_string_keys(node):
    """Yield every string dict key at any depth (used to catch a diagnostic term
    smuggled as a structural key rather than a value)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str):
                yield k
            yield from _iter_string_keys(v)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _iter_string_keys(v)


def individualization_contract(shared: SharedRegistry, group_label: str | None = None) -> dict:
    """The shared, group-invariant contract: common target, tasks, success criteria and
    hardest-case exit. `group_label` is added only for a student worksheet."""
    core = _core_tasks(shared)
    contract = {
        "target_id": "ind-target",
        "target_text": shared.standard_student_language,
        "task_ids": [t["task_id"] for t in shared.tasks],
        "tasks": core,
        "success_ids": [f"sc-{i}" for i in range(len(shared.success_criteria))],
        "success_criteria": list(shared.success_criteria),
        "exit_id": "exit-hardest",
        "exit": {"prompt": shared.exit_ticket["prompt"], "cognitive_demand": _hardest_demand(core)},
    }
    if group_label is not None:
        contract["group_label"] = group_label
    return contract


def package_core_fingerprint(document: dict) -> str:
    """Fingerprint the shared contract (excluding the neutral group_label). Identical
    across every document while support text may differ."""
    contract = dict(document["content"].get("individualization_contract", {}))
    contract.pop("group_label", None)
    payload = json.dumps(contract, ensure_ascii=False, sort_keys=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _pathway_profile(pathway: IndividualizedPathway) -> dict:
    profile = {
        "group_label": pathway.group_label,
        "teacher_profile_label": pathway.teacher_profile_label,
        "access_supports": list(pathway.access_supports),
        "representation_supports": list(pathway.representation_supports),
        "response_options": list(pathway.response_options),
        "rigor_evidence": pathway.rigor_evidence,
    }
    if pathway.extension_move is not None:
        profile["extension_move"] = dict(pathway.extension_move)
    return profile


def _student_blocks(shared: SharedRegistry, pathway: IndividualizedPathway, ctx: IndividualizedLessonContext) -> list:
    """Two-page physical worksheet. The shared source data (atmosphere table + greenhouse
    card) and the core task prompts + hardest-case exit ticket are byte-identical across
    every group; only the response/representation/access supports differ per pathway."""
    core = _core_tasks(shared)
    hardest = _hardest_demand(core)
    sd = ctx.source_data
    sc = ctx.source_card
    reps = " ".join(pathway.representation_supports) or "자료를 꼼꼼히 읽고 필요한 부분을 표시합니다."

    blocks: list = [
        # page 1 — identity, targets, real shared source, first task.
        worksheet.fill_table("header-fields", headers=["학년", "반", "번호", "이름", "날짜"],
                             rows=[["", "", "", "", ""]], caption=CAP_HEADER),
        worksheet.fill_table("success-check", headers=["확인", "성공 기준"],
                             rows=[["", c] for c in shared.success_criteria], caption=CAP_SUCCESS_STUDENT),
        worksheet.student_note("steps", text=(
            "오늘의 순서  1) 대기권 자료에서 네 개 층을 근거와 함께 구분한다  "
            "2) 온실효과가 커질 때 기온 변화를 복사 평형으로 설명한다  "
            "3) 출구표에 근거와 함께 답한다.")),
        worksheet.data_table("source-atmos", caption=sd["caption"], headers=list(sd["headers"]),
                             cells=[list(r) for r in sd["cells"]]),
        worksheet.source_card("source-evidence", title=sc["title"], body=sc["body"], source=sc["source"]),
        worksheet.student_note("response-guide", text="이렇게 답할 수 있어요: " + " / ".join(pathway.response_options)),
        worksheet.student_note("representation", text="자료 활용 도움말: " + reps),
        worksheet.sentence_support("sentence-stems", stems=[
            "나는 대기권을 ___ 기준으로 네 개 층으로 나누었다.",
            "온실효과가 커지면 지표 부근 기온은 ___, 왜냐하면 ___ 때문이다.",
        ]),
        worksheet.student_task("task-0", task_ref=core[0]["task_id"], prompt=core[0]["prompt"],
                               cognitive_demand=core[0]["cognitive_demand"]),
        worksheet.answer_box("answer-0", response_demand="paragraph", min_lines=4, min_height_mm=32),
        worksheet.page_break("student-page-break"),
    ]
    # page 2 — remaining core task(s), self-check, hardest-case exit, submission.
    for i, task in enumerate(core[1:], start=1):
        blocks.append(worksheet.student_task(f"task-{i}", task_ref=task["task_id"], prompt=task["prompt"],
                                             cognitive_demand=task["cognitive_demand"]))
        blocks.append(worksheet.answer_box(f"answer-{i}", response_demand="paragraph", min_lines=4, min_height_mm=32))
    blocks.append(worksheet.fill_table("self-check", headers=["확인", "점검 내용"], rows=[
        ["", "대기권을 네 개 층으로 근거와 함께 구분했다"],
        ["", "온실효과가 커질 때 기온 변화를 복사 평형으로 설명했다"],
    ], caption=CAP_SELFCHECK))
    blocks.append(worksheet.exit_ticket("exit-hardest", prompt=shared.exit_ticket["prompt"], cognitive_demand=hardest))
    blocks.append(worksheet.answer_box("answer-exit", response_demand="sentence", min_lines=3, min_height_mm=24))
    blocks.append(worksheet.student_note("submission", text=ctx.submission_instruction))
    return blocks


def _teacher_blocks(shared: SharedRegistry, by_label: dict, ctx: IndividualizedLessonContext) -> list:
    """Three-page teacher operating plan expressed entirely as real tables/grids on the
    shared block vocabulary, so every format renders the same structured content."""
    A, B, C = by_label["Group A"], by_label["Group B"], by_label["Group C"]

    def _join(xs):
        return " / ".join(xs) if xs else "-"

    def _ext(p):
        if not p.extension_move:
            return "-"
        op = p.extension_move['cognitive_operation']
        return f"{p.extension_move['move']} (인지 조작: {_COGNITIVE_LABELS.get(op, op)})"

    overview_cells = [
        ["과목", ctx.subject],
        ["단원", ctx.unit],
        ["학년", ctx.grade],
        ["성취기준", shared.standard_code],
        [ctx.date_field_label, ""],
        ["준비물", ", ".join(ctx.materials)],
    ]
    success_cells = [[str(i + 1), c] for i, c in enumerate(shared.success_criteria)]
    flow_cells = [[p["phase"], f"{p['minutes']}분", p["teacher_move"], p["student_action"], p["evidence"]]
                  for p in ctx.lesson_phases]
    matrix_cells = [
        ["접근 지원", _join(A.access_supports), _join(B.access_supports), _join(C.access_supports)],
        ["표상 지원", _join(A.representation_supports), _join(B.representation_supports), _join(C.representation_supports)],
        ["반응 선택", _join(A.response_options), _join(B.response_options), _join(C.response_options)],
        ["엄격성 근거", A.rigor_evidence, B.rigor_evidence, C.rigor_evidence],
        ["확장 이동", _ext(A), _ext(B), _ext(C)],
    ]
    regroup_cells = [
        ["관찰 기록에서 층 구분 근거가 약할 때", "이해 재점검 필요", "다음 차시 접근 지원(밑줄·안내 질문)을 강화한다"],
        ["출구표에서 복사 평형 연결이 정확할 때", "독립 수행 가능", "표상 지원을 줄이고 확장 과제를 제시한다"],
        ["관측 자료 근거 사용이 안정적일 때", "전이 가능", "새로운 예측·반례 설계 과제로 재편성한다"],
    ]
    obs_headers = ["학생 이름", *ctx.observation_criteria, "피드백"]
    obs_rows = [["" for _ in obs_headers] for _ in range(8)]
    interp_cells = [
        ["네 개 층 구분은 정확하나 온실효과 설명이 약함", "표상→설명 연결 부족", "복사 평형 도식을 제시하고 재설명 발문"],
        ["온실효과는 설명하나 관측 근거를 인용하지 않음", "근거 사용 습관 부족", "관측 자료에서 근거 문장을 찾아 인용하게 함"],
        ["가장 어려운 사례까지 근거와 함께 설명함", "전이 도달", "새로운 상황 예측·반례 설계로 확장"],
    ]
    return [
        # page 1
        worksheet.data_table("overview", caption=CAP_OVERVIEW, headers=["항목", "내용"], cells=overview_cells),
        worksheet.data_table("common-success", caption=CAP_SUCCESS_TEACHER, headers=["번호", "성공 기준"], cells=success_cells),
        worksheet.data_table("lesson-flow", caption=CAP_FLOW,
                             headers=["단계", "시간(분)", "교사 활동", "학생 활동", "형성 평가 근거"], cells=flow_cells),
        worksheet.page_break("teacher-page-break-1"),
        # page 2
        worksheet.data_table("deployment-matrix", caption=CAP_MATRIX,
                             headers=["구분", "Group A", "Group B", "Group C"], cells=matrix_cells),
        worksheet.data_table("regroup-rules", caption=CAP_REGROUP,
                             headers=["관찰 근거", "판단", "다음 차시 조치"], cells=regroup_cells),
        worksheet.student_note("grouping-policy", text=(
            "모둠 편성은 이번 차시 지원을 위한 임시 편성이며 고정된 서열이 아니다. "
            "과제 수행 근거에 따라 수시로 재편성한다.")),
        worksheet.page_break("teacher-page-break-2"),
        # page 3
        worksheet.fill_table("observation-grid", headers=obs_headers, rows=obs_rows, caption=CAP_OBSERVE),
        worksheet.student_note("common-exit", text=f"공통 출구표(가장 어려운 사례): {shared.exit_ticket['prompt']}"),
        worksheet.data_table("interpretation", caption=CAP_INTERPRET,
                             headers=["출구표 응답 양상", "해석", "다음 차시 지원"], cells=interp_cells),
        worksheet.student_note("post-lesson-label", text="수업 후 메모 (관찰 요약 · 다음 차시 조정 근거)"),
        worksheet.answer_box("post-lesson-notes", response_demand="paragraph", min_lines=4, min_height_mm=32),
    ]


# --- subject-grounded provenance (science, never social) ------------------------

_SUBJECT_SLUG = {"과": "science", "사": "social", "수": "math", "국": "korean", "영": "english",
                 "도": "moral", "정": "informatics", "음": "music", "미": "art", "체": "pe"}


def _subject_mark(standard_code: str) -> str | None:
    m = re.search(r"\d+\s*([가-힣])", standard_code or "")
    return m.group(1) if m else None


def _curriculum_provenance(shared: SharedRegistry, ctx: IndividualizedLessonContext):
    """One accurate curriculum provenance record + marker for the package subject.

    Teacher-created source content (atmosphere table / greenhouse card) is NOT recorded
    here — it renders as clearly labelled teacher-created learning data, keeping official
    provenance separate and accurate."""
    mark = _subject_mark(shared.standard_code)
    slug = _SUBJECT_SLUG.get(mark, "general")
    pid = f"curriculum-2022-{slug}"
    rid = f"prov-curriculum-2022-{slug}-1"
    code_slug = re.sub(r"[^0-9A-Za-z가-힣_-]", "", shared.standard_code) or "standard"
    ledger = [{
        "record_id": rid,
        "record_scope": "curriculum-context",
        "provider": {"provider_id": pid, "provider_kind": "curriculum-provider",
                     "release_id": f"{pid}@2026-07-15", "release_version": "2026.07.15"},
        "provenance_grade": ":provided",
        "source_reference": f"curriculum.pdf#{code_slug}",
        "verification_evidence_type": "provided-document",
        "verification_anchor": {"carrier": "provider-record", "locator_type": "provider-record-id",
                                "locator_value": f"provider-record::{pid}::{code_slug}"},
        "source_license": {"status": "verified-compatible", "license_id": "KOGL-1",
                           "evidence_anchor": {"carrier": "provider-release-manifest", "locator_type": "release-id",
                                               "locator_value": f"{pid}@2026-07-15"}},
        "read_only_input": True,
    }]
    markers = [{
        "record_id": rid,
        "label": "[from-curriculum:provided]",
        "evidence_text": f"2022 개정 {ctx.subject}과 성취기준 {shared.standard_code} ({ctx.unit}) 를 직접 확인함",
    }]
    return ledger, markers


def _document(document_id, document_class, title, task_ids, facet, sections, *,
              contract, blocks=None, pathway_profiles=None, provenance_markers=None) -> dict:
    content = {
        "facet": facet,
        "sections": sections,
        "individualization_contract": contract,
        "provenance_markers": provenance_markers or [],
        "unresolved_boundary_markers": [],
    }
    if blocks is not None:
        content["blocks"] = blocks
    if pathway_profiles is not None:
        content["pathway_profiles"] = pathway_profiles
    return {
        "document_id": document_id,
        "document_class": document_class,
        "title": title,
        "source_task_ids": list(task_ids),
        "render_targets": ["hwpx", "docx", "html"],
        "content": content,
    }


def build_individualized_package_ir(shared: SharedRegistry, pathways: list, base_ir: dict,
                                    context: "IndividualizedLessonContext | None" = None) -> dict:
    """Compose the four-document individualized package on the canonical IR, reusing the
    approved envelope/provider_contract from `base_ir` but grounding subject/provenance
    from the shared standard code (never inheriting a crossed-subject base fixture).

    `context` supplies the structured, subject-grounded classroom/document content that is
    expanded into real tables/grids/answer areas across all three formats."""
    labels = [p.group_label for p in pathways]
    if sorted(labels) != sorted(GROUP_LABELS):
        raise ValueError(f"pathways must cover exactly {GROUP_LABELS} (no duplicate, no omission), got {labels}")
    by_label = {p.group_label: p for p in pathways}
    if context is None:
        raise ValueError("build_individualized_package_ir requires an IndividualizedLessonContext with real content")
    ctx = context
    if _subject_mark(shared.standard_code) is None or ctx.standard_code != shared.standard_code:
        raise ValueError(
            f"lesson context standard_code {ctx.standard_code!r} must match the shared standard {shared.standard_code!r}")

    task_ids = [t["task_id"] for t in shared.tasks]
    ledger, teacher_markers = _curriculum_provenance(shared, ctx)
    full_ctx = ctx.to_dict()
    student_ctx = {k: full_ctx[k] for k in ("subject", "unit", "grade", "standard_code", "lesson_minutes")}

    # Teacher operations plan: one common-goal section (no label-duplicating prefix); all
    # structured operating content lives in real tables/grids on content.blocks.
    teacher_doc = _document(
        TEACHER_DOC, "individualized-plan", "개별화 수업 운영안", task_ids, "teacher",
        [_sec("common-goal", shared.standard_student_language)],
        contract=individualization_contract(shared),
        blocks=_teacher_blocks(shared, by_label, ctx),
        pathway_profiles=[_pathway_profile(by_label[label]) for label in GROUP_LABELS],
        provenance_markers=teacher_markers,
    )
    teacher_doc["content"]["lesson_context"] = full_ctx

    documents = [teacher_doc]
    for label in GROUP_LABELS:
        p = by_label[label]
        d = _document(
            DOC_GROUP[label], "worksheet", f"학생 활동지 ({label})", task_ids, "student",
            [_sec("student-goal", shared.standard_student_language)],
            contract=individualization_contract(shared, group_label=label),
            blocks=_student_blocks(shared, p, ctx),
        )
        d["content"]["lesson_context"] = dict(student_ctx)
        documents.append(d)

    ir = {k: v for k, v in base_ir.items() if k != "lesson_package"}
    ir["provenance_ledger"] = ledger  # subject-grounded; never the crossed-domain base ledger
    tasks = [{"task_id": t["task_id"], "title": t["title"], "document_ids": [d["document_id"] for d in documents]} for t in shared.tasks]
    ir["lesson_package"] = {"package_id": "pkg-individualized", "tasks": tasks, "documents": documents}
    return ir


def validate_individualized_package(ir: dict) -> list:
    """Deterministic contract check. Returns a sorted-free list of issue strings; empty
    list == a clean individualized package."""
    issues: list = []
    documents = {d["document_id"]: d for d in ir["lesson_package"]["documents"]}
    expected_ids = {TEACHER_DOC, *DOC_GROUP.values()}
    if set(documents) != expected_ids:
        issues.append(f"document set mismatch: expected {sorted(expected_ids)}, got {sorted(documents)}")

    teacher = documents.get(TEACHER_DOC)
    if teacher is not None:
        if teacher["document_class"] != "individualized-plan":
            issues.append("teacher plan document_class must be individualized-plan")
        if teacher["content"].get("facet") != "teacher":
            issues.append("teacher plan facet must be teacher")

    student_docs = [d for d in documents.values() if d["content"].get("facet") == "student"]
    for d in student_docs:
        if d["document_class"] != "worksheet":
            issues.append(f"{d['document_id']}: student document must be a worksheet")

    # identical source_task_ids across all documents.
    if len({tuple(d["source_task_ids"]) for d in documents.values()}) != 1:
        issues.append("source_task_ids differ across documents")

    # student labels exactly and uniquely Group A|B|C.
    labels = [d["content"].get("individualization_contract", {}).get("group_label") for d in student_docs]
    if sorted(l for l in labels if l) != sorted(GROUP_LABELS) or len(set(labels)) != len(labels):
        issues.append(f"student group labels must be exactly and uniquely {list(GROUP_LABELS)}, got {labels}")

    # shared contract fingerprint identical across every document.
    fingerprints = {package_core_fingerprint(d) for d in documents.values() if "individualization_contract" in d["content"]}
    if len(fingerprints) != 1:
        issues.append("shared target/task/success/exit contract differs across documents")

    # every contract carries an exit that targets the hardest-case demand.
    for d in documents.values():
        contract = d["content"].get("individualization_contract")
        if not contract or not contract.get("exit_id") or not contract.get("exit"):
            issues.append(f"{d['document_id']}: missing shared exit in individualization_contract")
            continue
        tasks = contract.get("tasks") or []
        if tasks:
            hardest = max(_ORD[t["cognitive_demand"]] for t in tasks)
            if _ORD[contract["exit"]["cognitive_demand"]] != hardest:
                issues.append(f"{d['document_id']}: contract exit does not target the hardest-case demand")

    # teacher-only pathway profiles: exactly A/B/C, rigor evidence present, extension elevates operation.
    profile_labels: list = []
    if teacher is not None:
        profiles = teacher["content"].get("pathway_profiles") or []
        profile_labels = [p.get("teacher_profile_label", "") for p in profiles]
        if {p.get("group_label") for p in profiles} != set(GROUP_LABELS):
            issues.append("teacher plan must carry pathway profiles for exactly Group A/B/C")
        base_contract = teacher["content"].get("individualization_contract", {})
        base_hardest = max((_ORD[t["cognitive_demand"]] for t in base_contract.get("tasks", [])), default=0)
        for p in profiles:
            if not str(p.get("rigor_evidence", "")).strip():
                issues.append(f"pathway profile {p.get('group_label')}: missing rigor evidence")
            if not str(p.get("teacher_profile_label", "")).strip():
                issues.append(f"pathway profile {p.get('group_label')}: missing teacher profile label")
            ext = p.get("extension_move")
            if ext is not None:
                op = ext.get("cognitive_operation")
                if op not in _ORD or _ORD[op] <= base_hardest:
                    issues.append(f"pathway profile {p.get('group_label')}: extension must change cognitive operation, not quantity only")
    for d in student_docs:
        if "pathway_profiles" in d["content"]:
            issues.append(f"{d['document_id']}: student worksheet must not carry pathway_profiles")

    # leak gate: reuse the existing facet separation + package diagnostic-term/profile-label scan.
    ok, violations = check_facet_separation(ir)
    if not ok:
        issues.extend(f"facet: {v}" for v in violations)
    for d in student_docs:
        leaves = [s["text"] for s in d["content"].get("sections", [])]
        leaves += list(worksheet.iter_block_string_leaves(d["content"].get("blocks", [])))
        for leaf in leaves:
            for term in STUDENT_DIAGNOSTIC_TERMS:
                if worksheet.contains_forbidden_term(leaf, term):
                    issues.append(f"{d['document_id']}: diagnostic term '{term}' in student worksheet")
            for label in profile_labels:
                if label and label in leaf:
                    issues.append(f"{d['document_id']}: teacher profile label leaked into student worksheet")
        # a diagnostic term hidden as a structural KEY leaks through the rendered
        # data-block-json attribute, so scan block keys (any depth) too.
        for key in _iter_string_keys(d["content"].get("blocks", [])):
            for term in STUDENT_DIAGNOSTIC_TERMS:
                if worksheet.contains_forbidden_term(key, term):
                    issues.append(f"{d['document_id']}: diagnostic term '{term}' in student block key")

    # rigor structure in student blocks: full core-task coverage + one hardest-case exit ticket.
    for d in student_docs:
        contract = d["content"].get("individualization_contract", {})
        want = set(contract.get("task_ids", []))
        blocks = d["content"].get("blocks", [])
        have = {b.get("task_ref") for b in blocks if b["block_type"] == "student_task"}
        missing = want - have
        if missing:
            issues.append(f"{d['document_id']}: missing core task coverage for {sorted(missing)}")
        tickets = [b for b in blocks if b["block_type"] == "exit_ticket"]
        if len(tickets) != 1:
            issues.append(f"{d['document_id']}: student worksheet must carry exactly one exit_ticket")
        else:
            demands = [b["cognitive_demand"] for b in blocks if b["block_type"] == "student_task"]
            if demands:
                hardest = max(_ORD[x] for x in demands)
                ticket = tickets[0]
                if not ticket.get("targets_hardest_case") or _ORD[ticket["cognitive_demand"]] != hardest:
                    issues.append(f"{d['document_id']}: exit ticket must target the hardest-case demand")
    return issues

# --- cross-domain grounding gate -----------------------------------------------

_SUBJECT_BY_MARK = {"과": "과학", "사": "사회", "수": "수학", "국": "국어", "영": "영어",
                    "도": "도덕", "정": "정보", "음": "음악", "미": "미술", "체": "체육"}

# Provenance/provider/domain signal tokens per subject. When a package is subject X,
# any OTHER subject's tokens appearing anywhere (ledger, markers, sections, blocks)
# is a crossed-domain grounding failure.
_SUBJECT_DOMAIN_TOKENS = {
    "과학": ["과학과", "curriculum-2022-science"],
    "사회": ["사회과", "사회 교과", "지역 사례", "지역 문제 해결", "curriculum-2022-social", "textbook-social"],
    "수학": ["수학과", "curriculum-2022-math"],
    "국어": ["국어과", "curriculum-2022-korean"],
    "영어": ["영어과", "curriculum-2022-english"],
}


def check_cross_domain_grounding(ir: dict) -> list:
    """Deterministic cross-domain grounding gate. Returns a list of issue strings; empty
    == the package's subject, standard code, declared context and every provenance
    signal agree, and no foreign-subject provenance is present anywhere."""
    issues: list = []
    documents = ir.get("lesson_package", {}).get("documents", [])

    codes = {d["content"]["lesson_context"]["standard_code"]
             for d in documents if isinstance(d["content"].get("lesson_context"), dict)
             and d["content"]["lesson_context"].get("standard_code")}
    subjects = {d["content"]["lesson_context"].get("subject")
                for d in documents if isinstance(d["content"].get("lesson_context"), dict)}
    if not codes:
        return ["no standard_code found in any lesson_context"]
    if len(codes) != 1:
        issues.append(f"standard code disagreement across documents: {sorted(codes)}")
    code = sorted(codes)[0]
    mark = _subject_mark(code)
    derived = _SUBJECT_BY_MARK.get(mark) if mark else None
    if derived is None:
        return issues + [f"unrecognized subject mark in standard code {code!r}"]
    for s in subjects:
        if s != derived:
            issues.append(f"declared subject {s!r} disagrees with standard-code subject {derived!r} ({code})")

    foreign_tokens = [tok for subj, toks in _SUBJECT_DOMAIN_TOKENS.items() if subj != derived for tok in toks]

    haystack: list = [json.dumps(rec, ensure_ascii=False) for rec in ir.get("provenance_ledger", [])]
    for d in documents:
        c = d["content"]
        for m in c.get("provenance_markers", []):
            haystack += [m.get("label", ""), m.get("evidence_text", ""), m.get("record_id", "")]
        haystack += [s.get("text", "") for s in c.get("sections", [])]
        haystack += list(worksheet.iter_block_string_leaves(c.get("blocks", [])))
    blob = "\n".join(haystack)
    for tok in foreign_tokens:
        if tok in blob:
            issues.append(f"foreign-subject provenance/token {tok!r} present in a {derived} package")
    return issues
