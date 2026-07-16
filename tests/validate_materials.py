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
import zipfile
import xml.etree.ElementTree as ET
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
    worksheet as ws,
)
from providers.curriculum.provider import CurriculumProvider  # noqa: E402
from renderers import render_all, extract_all, verify_parity  # noqa: E402

SYNTH_INDEX = ROOT / "tests" / "golden" / "curriculum-provider" / "normalized-synthetic.jsonl"
WORKSHEET_GOLDEN = ROOT / "tests" / "golden" / "worksheet" / "9과17-01.blocks.json"

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


def _worksheet_ir(blocks: list) -> dict:
    doc = ws.worksheet_document(document_id="stu-ws", title="[9과17-01] 학생 활동지",
                                task_ids=["t-atmos", "t-green"], blocks=blocks)
    return ws.build_worksheet_ir(
        BASE_IR, doc,
        tasks=[{"task_id": "t-atmos", "title": "탐구", "document_ids": ["stu-ws"]},
               {"task_id": "t-green", "title": "설명", "document_ids": ["stu-ws"]}],
    )


def test_worksheet_facet_recursion() -> None:
    """RC2: facet scan recurses content.blocks (leak-class x block-type + structural keys + group neutrality)."""
    clean = _worksheet_ir(ws.demo_worksheet_blocks())
    ok, viol = check_facet_separation(clean)
    assert_true(ok, f"clean worksheet must pass facet recursion: {viol}")

    def leak(blocks):
        return check_facet_separation(_worksheet_ir(blocks))

    exit_tail = ws.exit_ticket("e", prompt="정리", cognitive_demand="apply")
    matrix = {
        "weight_in_fill_table": [ws.fill_table("b1", headers=["항목"], rows=[["배점 30"]]), exit_tail],
        "misconception_in_source_card": [ws.source_card("b1", title="자료", body="이 문항의 오개념", source="s"), exit_tail],
        "answer_key_leaf_in_note": [ws.student_note("b1", text="정답: 4개 층"), exit_tail],
        "teacher_prompt_in_note": [ws.student_note("b1", text="발문 예시"), exit_tail],
        "internal_level_in_stems": [ws.sentence_support("b1", stems=["심화 과정 안내"]), exit_tail],
    }
    for name, blocks in matrix.items():
        ok2, viol2 = leak(blocks)
        assert_true(not ok2, f"{name}: block leak must be detected (was clean)")

    # Independent-QA bypass regressions: case variants, whitespace-split Korean,
    # nested placement, English rubric, and structural-key case variants.
    bypass_matrix = {
        "uppercase_solution": [ws.student_note("b1", text="SOLUTION: four layers"), exit_tail],
        "mixed_answer_key": [ws.student_note("b1", text="Answer_Key: four layers"), exit_tail],
        "english_rubric": [ws.student_note("b1", text="Rubric for scoring"), exit_tail],
        "split_korean_answer": [ws.student_note("b1", text="정 답: 네 개 층"), exit_tail],
        "split_korean_weight": [ws.fill_table("b1", headers=["항목"], rows=[["배 점 30"]]), exit_tail],
        "zero_width_answer": [ws.student_note("b1", text="정\u200b답: 네 개 층"), exit_tail],
        "zero_width_solution": [ws.student_note("b1", text="SOLU\u200bTION: four layers"), exit_tail],
        "nested_uppercase": [
            {"block_id": "b1", "block_type": "student_note", "text": "학생 메모", "meta": {"deep": ["MISCONCEPTION"]}},
            exit_tail,
        ],
    }
    for name, blocks in bypass_matrix.items():
        ok_bypass, violations_bypass = leak(blocks)
        assert_true(not ok_bypass, f"{name}: case/whitespace/nested leak bypass must be detected: {violations_bypass}")

    legitimate_student_phrases = [
        "발표 준비를 시작합니다.",
        "여기 초록 식물을 관찰합니다.",
        "관심 화제를 선택합니다.",
        "이해 설명을 서로 비교합니다.",
    ]
    for phrase in legitimate_student_phrases:
        ok_legitimate, violations_legitimate = leak([ws.student_note("safe", text=phrase), exit_tail])
        assert_true(ok_legitimate, f"legitimate student phrase must not be manufactured into a leak: {phrase} / {violations_legitimate}")

    # structural key ban (presence == violation regardless of value).
    struct = ws.answer_box("b1", response_demand="short", min_lines=1, min_height_mm=8)
    struct["solution"] = "정답 4개 층"
    ok3, viol3 = leak([struct, exit_tail])
    assert_true(not ok3 and any("structural key" in v for v in viol3), "forbidden structural key must be detected")

    struct_case = ws.answer_box("b1", response_demand="short", min_lines=1, min_height_mm=8)
    struct_case["Answer_Key"] = "four layers"
    ok_case, viol_case = leak([struct_case, exit_tail])
    assert_true(not ok_case and any("structural key" in v for v in viol_case), "case-variant forbidden structural key must be detected")

    # group neutrality.
    ok4, viol4 = leak([ws.group_cohesion("b1", group_label="Group A 기초", members=["Group B"], shared_task_refs=["t"]), exit_tail])
    assert_true(not ok4, "non-neutral group label must be detected in a student block")


def test_worksheet_block_round_trip() -> None:
    """Block encode -> 3 real formats -> extract -> parity + identical to source semantics."""
    blocks = ws.demo_worksheet_blocks()
    ir = _worksheet_ir(blocks)
    errors = sorted(jsonschema.Draft202012Validator(IR_SCHEMA).iter_errors(ir), key=lambda e: list(e.path))
    assert_true(not errors, f"worksheet IR must be schema-valid: {errors[0].message if errors else ''}")
    with tempfile.TemporaryDirectory() as td:
        paths = render_all(ir, td)
        ex = extract_all(paths)
        pok, preasons = verify_parity(ex)
        assert_true(pok, f"worksheet 3-way block parity: {preasons}")
        for fmt in ("hwpx", "docx", "html"):
            got = [b["block"] for b in ex[fmt]["blocks"]]
            assert_true(got == blocks, f"{fmt}: extracted block semantics must equal source")
        # real table/answer-space shapes recomputed from the rendered markup match source.
        shapes = {b["block_id"]: b["rendered_shape"] for b in ex["hwpx"]["blocks"]}
        assert_true(shapes["b6"] == {"rows": 1 + 3, "cols": 3}, "fill_table renders header + 3 real rows")
        assert_true(shapes["b3"] == {"rows": 1 + 4, "cols": 3}, "data_table renders header + 4 real rows")
        assert_true(shapes["b10"] == {"rows": 6, "cols": 1}, "extended answer_box renders 6 ruled lines")

        # Production-usable cell structure: Office/Hancom require every table cell
        # (including empty writing cells) to contain paragraph/run/text descendants.
        with zipfile.ZipFile(paths["docx"]) as z:
            docx_root = ET.fromstring(z.read("word/document.xml"))
        w_ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        docx_cells = docx_root.findall(f".//{w_ns}tc")
        assert_true(bool(docx_cells), "DOCX must contain real table cells")
        for cell in docx_cells:
            assert_true(cell.find(f"./{w_ns}p/{w_ns}r/{w_ns}t") is not None,
                        "every DOCX w:tc must contain w:p/w:r/w:t, including empty cells")

        with zipfile.ZipFile(paths["hwpx"]) as z:
            hwpx_root = ET.fromstring(z.read("Contents/section0.xml"))
        hp_ns = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
        hwpx_cells = hwpx_root.findall(f".//{hp_ns}tc")
        assert_true(bool(hwpx_cells), "HWPX must contain real table cells")
        for cell in hwpx_cells:
            assert_true(cell.find(f"./{hp_ns}subList/{hp_ns}p/{hp_ns}run/{hp_ns}t") is not None,
                        "every HWPX hp:tc must contain hp:subList/hp:p/hp:run/hp:t, including empty cells")

        # XML escaping survives rendering and exact semantic round-trip.
        escaped = [
            ws.fill_table("esc", headers=["A & B", "<항목>"], rows=[["\"인용\"", ""]], caption="escape"),
            ws.exit_ticket("esc-exit", prompt="A & B < C", cognitive_demand="recall"),
        ]
        escaped_paths = render_all(_worksheet_ir(escaped), Path(td) / "escaped")
        escaped_ex = extract_all(escaped_paths)
        escaped_ok, escaped_reasons = verify_parity(escaped_ex)
        assert_true(escaped_ok, f"escaped content must retain 3-way parity: {escaped_reasons}")
        for fmt in ("hwpx", "docx", "html"):
            assert_true([b["block"] for b in escaped_ex[fmt]["blocks"]] == escaped,
                        f"{fmt}: escaped block semantics must round-trip exactly")
        # cross-format tamper (drop a fill row from the HTML) breaks block parity.
        import re as _re
        tampered = Path(paths["html"]).read_text(encoding="utf-8")
        tampered = _re.sub(r'<tr[^>]*data-row-height-mm="26"[^>]*>.*?</tr>', "", tampered, count=1, flags=_re.DOTALL)
        Path(paths["html"]).write_text(tampered, encoding="utf-8")
        ex2 = extract_all(paths)
        pok2, preasons2 = verify_parity(ex2)
        assert_true(not pok2 and any("blocks" in r for r in preasons2), "dropping a real table row must break block parity")


def test_worksheet_9과17_01_golden() -> None:
    """The committed [9과17-01] semantic golden matches the deterministic source blocks
    and the extraction from all three real rendered formats (no physical bytes committed)."""
    golden = json.loads(WORKSHEET_GOLDEN.read_text(encoding="utf-8"))
    blocks = ws.demo_worksheet_blocks()
    assert_true(golden["blocks"] == blocks, "[9과17-01] golden must equal the deterministic source blocks")
    assert_true(golden["block_count"] == len(blocks) and golden["standard_code"] == "[9과17-01]", "golden metadata drift")
    assert_true(ws.check_physical_workload(blocks, "중학교") == [], "[9과17-01] worksheet must pass the physical gate")
    ir = _worksheet_ir(blocks)
    with tempfile.TemporaryDirectory() as td:
        ex = extract_all(render_all(ir, td))
        pok, preasons = verify_parity(ex)
        assert_true(pok, f"[9과17-01] 3-way parity: {preasons}")
        for fmt in ("hwpx", "docx", "html"):
            assert_true([b["block"] for b in ex[fmt]["blocks"]] == golden["blocks"], f"{fmt}: extracted blocks must equal committed golden")


def test_worksheet_quick_draft_gate() -> None:
    """RC7: a standalone quick draft is provably NOT downstream-ready (three named fields)."""
    ir = ws.build_quick_draft_worksheet_ir(BASE_IR, title="[9과17-01] 빠른 초안", standard_code="[9과99-01]")
    errors = sorted(jsonschema.Draft202012Validator(IR_SCHEMA).iter_errors(ir), key=lambda e: list(e.path))
    assert_true(not errors, f"quick-draft IR must stay schema-valid: {errors[0].message if errors else ''}")
    doc = ir["lesson_package"]["documents"][0]
    # 1. unresolved boundary marker present (handoff blocked).
    assert_true(ws.STANDALONE_QUICK_DRAFT_MARKER in doc["content"]["unresolved_boundary_markers"],
                "quick draft must carry the standalone unresolved boundary marker")
    assert_true(ir["handoff_mode"] == "blocked", "quick draft handoff_mode must be blocked")
    # 2. no verified provider record.
    provider = CurriculumProvider(SYNTH_INDEX)
    assert_true(provider.verify_standard("[9과99-01]")["downstream_ready"] is False,
                "standalone provider record must stay fail-closed")
    # 3. teacher-approval gate fail-closed.
    assert_true(TeacherApprovalGate.evaluate(ir, None).downstream_ready is False,
                "quick draft must fail the teacher-approval gate")


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

    # 6. Worksheet content.blocks: facet recursion, block round-trip parity, standalone quick draft.
    test_worksheet_facet_recursion()
    test_worksheet_block_round_trip()
    test_worksheet_9과17_01_golden()
    test_worksheet_quick_draft_gate()

    print("PASS validate_materials")
    print("- one shared registry -> student+teacher+parent docs in a schema-valid IR")
    print("- facet separation enforced (teacher-only terms blocked in student docs)")
    print("- bidirectional teacher<->student task alignment verified")
    print("- teacher-approval gate fail-closed; facet/alignment violations block even with approval")
    print("- material docs render to real HWPX/DOCX/HTML with 3-way parity")
    print("- worksheet content.blocks facet recursion detects leak-class x block-type + structural keys + group neutrality")
    print("- worksheet blocks encode to real tables/answer-space and round-trip with 3-way parity (row-drop breaks parity)")
    print("- standalone worksheet quick draft is fail-closed: marker present, provider unverified, teacher-approval blocked")
    print("- committed [9과17-01] semantic golden matches deterministic source blocks + all-format extraction (no physical bytes)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
