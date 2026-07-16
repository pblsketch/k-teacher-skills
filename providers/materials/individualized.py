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


def _student_blocks(shared: SharedRegistry, pathway: IndividualizedPathway) -> list:
    """Physical worksheet blocks. Core task prompts + exit ticket are byte-identical
    across groups (shared block ids); only the leading supports differ per pathway."""
    core = _core_tasks(shared)
    hardest = _hardest_demand(core)
    blocks: list = [
        worksheet.student_note("response-guide", text="이렇게 답할 수 있어요: " + " / ".join(pathway.response_options)),
        worksheet.source_card("material-support", title="자료 안내",
                              body=" ".join(pathway.representation_supports) or "제공된 자료를 사용합니다.",
                              source="학급 제공 자료"),
        worksheet.sentence_support("access-stems", stems=list(pathway.access_supports) or ["나는 ___라고 생각한다.", "왜냐하면 ___ 때문이다."]),
    ]
    last = len(core) - 1
    for i, task in enumerate(core):
        blocks.append(worksheet.student_task(f"task-{i}", task_ref=task["task_id"], prompt=task["prompt"], cognitive_demand=task["cognitive_demand"]))
        if i == last:
            blocks.append(worksheet.answer_box(f"answer-{i}", response_demand="extended", min_lines=6, min_height_mm=48))
        else:
            blocks.append(worksheet.answer_box(f"answer-{i}", response_demand="paragraph", min_lines=4, min_height_mm=32))
    blocks.append(worksheet.exit_ticket("exit-hardest", prompt=shared.exit_ticket["prompt"], cognitive_demand=hardest))
    return blocks


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


def build_individualized_package_ir(shared: SharedRegistry, pathways: list, base_ir: dict) -> dict:
    """Compose the four-document individualized package on the canonical IR, reusing the
    approved envelope/provider_contract/provenance_ledger from `base_ir`."""
    labels = [p.group_label for p in pathways]
    if sorted(labels) != sorted(GROUP_LABELS):
        raise ValueError(f"pathways must cover exactly {GROUP_LABELS} (no duplicate, no omission), got {labels}")
    by_label = {p.group_label: p for p in pathways}

    task_ids = [t["task_id"] for t in shared.tasks]
    base_docs = base_ir.get("lesson_package", {}).get("documents", [])
    base_provenance = base_docs[0]["content"].get("provenance_markers", []) if base_docs else []

    # Teacher operations plan: common goal, temporary grouping policy, regroup evidence,
    # common success/exit, and one teacher-only section per pathway.
    teacher_sections = [
        _sec("common-goal", f"공통 목표: {shared.standard_student_language}"),
        _sec("grouping-policy", "모둠 편성은 이번 차시 지원을 위한 임시 편성이며 고정된 서열이 아니다. 과제 수행 근거에 따라 수시로 재편성한다."),
        _sec("regroup-evidence", "재편성 근거: 각 학생의 과제 수행 관찰 기록과 출구표 응답을 근거로 다음 차시 지원을 조정한다."),
        _sec("common-success", "공통 성공 기준: " + "; ".join(shared.success_criteria)),
        _sec("common-exit", f"공통 출구표(가장 어려운 사례): {shared.exit_ticket['prompt']}"),
    ]
    for label in GROUP_LABELS:
        p = by_label[label]
        txt = (f"{label} 지원 프로파일({p.teacher_profile_label}): "
               f"접근 지원 {'; '.join(p.access_supports) or '없음'} / "
               f"표상 지원 {'; '.join(p.representation_supports) or '없음'} / "
               f"반응 선택 {'; '.join(p.response_options) or '없음'} / "
               f"엄격성 유지 근거: {p.rigor_evidence}")
        if p.extension_move is not None:
            txt += f" / 확장: {p.extension_move['move']} (인지 조작: {p.extension_move['cognitive_operation']})"
        teacher_sections.append(_sec(f"pathway-{label[-1].lower()}", txt))

    teacher_doc = _document(
        TEACHER_DOC, "individualized-plan", "개별화 수업 운영안", task_ids, "teacher", teacher_sections,
        contract=individualization_contract(shared),
        pathway_profiles=[_pathway_profile(by_label[label]) for label in GROUP_LABELS],
        provenance_markers=base_provenance,
    )

    documents = [teacher_doc]
    for label in GROUP_LABELS:
        p = by_label[label]
        documents.append(_document(
            DOC_GROUP[label], "worksheet", f"학생 활동지 ({label})", task_ids, "student",
            [_sec("student-goal", f"오늘의 목표: {shared.standard_student_language}")],
            contract=individualization_contract(shared, group_label=label),
            blocks=_student_blocks(shared, p),
        ))

    ir = {k: v for k, v in base_ir.items() if k != "lesson_package"}
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
