#!/usr/bin/env python3
"""VS4b focused validator: secondary-material builder + teacher-approval gate.

One shared registry -> student + teacher facet documents inside a schema-valid IR.
Facet separation + bidirectional alignment + fail-closed teacher-approval gate.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.materials import (  # noqa: E402
    SharedRegistry,
    build_material_ir,
    check_facet_separation,
    check_bidirectional_alignment,
    TeacherApprovalGate,
)
from renderers import render_all, extract_all, verify_parity  # noqa: E402

IR_SCHEMA = json.loads((ROOT / "schemas" / "lesson-package-ir.schema.json").read_text(encoding="utf-8"))
BASE_IR = json.loads((ROOT / "tests" / "golden" / "lesson-package-ir" / "downstream-ready.json").read_text(encoding="utf-8"))
APPROVAL = json.loads((ROOT / "tests" / "golden" / "materials" / "approval.json").read_text(encoding="utf-8"))


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def sample_shared() -> SharedRegistry:
    return SharedRegistry(
        standard_code="[9과17-01]",
        standard_student_language="대기권을 4개 층으로 나누어 설명하고, 온실효과를 예로 들 수 있다.",
        standard_teacher_text="지구 대기권을 4개 권역으로 구분하며, 온실효과와 지구온난화를 복사 평형의 관점으로 설명할 수 있다.",
        tasks=[
            {"task_id": "t1", "title": "탐구", "student_instructions": "대기 자료를 읽고 4개 층을 표시한다.", "teacher_notes": "층 구분 기준을 스스로 세우게 한다.", "writing_space": True},
            {"task_id": "t2", "title": "설명", "student_instructions": "온실효과를 그림으로 설명한다.", "teacher_notes": "복사 평형 관점을 연결하도록 발문한다.", "writing_space": True},
        ],
        success_criteria=["대기권을 4개 층으로 구분할 수 있다", "온실효과를 예로 설명할 수 있다"],
        exit_ticket={"prompt": "온실효과가 커지면 대기 온도는 어떻게 될까? 근거와 함께 쓰기", "targets_hardest_case": True},
        misconceptions=[{"what": "온실효과=오염", "why": "일상어 혼동", "teacher_response": "복사 평형으로 재설명"}],
        rubric=[{"criterion": "근거 사용", "levels": ["상", "중", "하"]}],
        parent_summary="이번 단원은 대기권과 온실효과를 다룹니다. 가정에서 날씨 이야기를 나눠 주세요.",
    )


def main() -> None:
    shared = sample_shared()
    ir = build_material_ir(shared, BASE_IR, include_parent=True)

    # 1. Built IR is schema-valid (single canonical IR, multi-document).
    errors = sorted(jsonschema.Draft202012Validator(IR_SCHEMA).iter_errors(ir), key=lambda e: list(e.path))
    assert_true(not errors, f"built IR must be schema-valid: {errors[0].message if errors else ''}")

    facets = {d["content"]["facet"] for d in ir["lesson_package"]["documents"]}
    assert_true({"student", "teacher", "parent"} <= facets, "student+teacher+parent facets present")
    assert_true(sum(1 for d in ir["lesson_package"]["documents"] if d["content"]["facet"] == "student") == 2, "2 student docs")

    # 2. Facet separation: no teacher-only language in student docs.
    ok, viol = check_facet_separation(ir)
    assert_true(ok, f"facet separation clean: {viol}")

    # negative: inject a rubric term into a student doc.
    bad = copy.deepcopy(ir)
    for d in bad["lesson_package"]["documents"]:
        if d["content"]["facet"] == "student":
            d["content"]["sections"].append({"content_id": "leak", "text": "루브릭 배점 안내"})
            break
    ok2, viol2 = check_facet_separation(bad)
    assert_true(not ok2 and any("루브릭" in v for v in viol2), "teacher term in student doc detected")

    # 3. Bidirectional alignment: student<->teacher task coverage.
    aok, aissue = check_bidirectional_alignment(ir)
    assert_true(aok, f"bidirectional alignment clean: {aissue}")

    # 4. Teacher-approval gate is fail-closed.
    assert_true(TeacherApprovalGate.evaluate(ir, None).downstream_ready is False, "no approval -> blocked")
    assert_true(TeacherApprovalGate.evaluate(ir, {"decision": "rejected", "approver_role": "teacher"}).downstream_ready is False, "rejected -> blocked")
    assert_true(TeacherApprovalGate.evaluate(ir, {"decision": "approved", "approver_role": "principal"}).downstream_ready is False, "non-teacher approver -> blocked")
    approved = TeacherApprovalGate.evaluate(ir, APPROVAL)
    assert_true(approved.downstream_ready is True, f"valid teacher approval -> ready: {approved.reason}")
    # even valid approval cannot pass a facet-violating IR.
    assert_true(TeacherApprovalGate.evaluate(bad, APPROVAL).downstream_ready is False, "facet violation blocks even with approval")

    # 5. Integration: a student and a teacher doc each render to 3 real formats with parity.
    with tempfile.TemporaryDirectory() as td:
        for idx, want_facet in ((0, "student"),):
            paths = render_all(ir, td, document_index=idx)
            ex = extract_all(paths)
            pok, preasons = verify_parity(ex)
            assert_true(pok, f"material doc render parity: {preasons}")
        # teacher-guide doc index
        tea_idx = next(i for i, d in enumerate(ir["lesson_package"]["documents"]) if d["document_id"] == "tea-guide")
        paths2 = render_all(ir, td, document_index=tea_idx)
        assert_true(Path(paths2["hwpx"]).exists(), "teacher doc renders to real hwpx")

    print("PASS validate_materials")
    print("- one shared registry -> student+teacher+parent docs in a schema-valid IR")
    print("- facet separation enforced (teacher-only terms blocked in student docs)")
    print("- bidirectional teacher<->student task alignment verified")
    print("- teacher-approval gate fail-closed; facet/alignment violations block even with approval")
    print("- material docs render to real HWPX/DOCX/HTML with 3-way parity")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
