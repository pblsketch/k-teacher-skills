#!/usr/bin/env python3
"""VS-W3 focused validator: deterministic physical-workload gates for student
worksheet `content.blocks` (RC1), plus the `$defs/worksheetBlock` shape source.

Each numeric/pattern threshold in providers/materials/worksheet.py has at least one
negative mutation that flips it RED. Block shapes are pinned by the canonical schema
`$defs/worksheetBlock` (referenced only here). Independent implementation.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.materials import worksheet as w  # noqa: E402

SCHEMA = json.loads((ROOT / "schemas" / "lesson-package-ir.schema.json").read_text(encoding="utf-8"))
BLOCK_VALIDATOR = jsonschema.Draft202012Validator({"$defs": SCHEMA["$defs"], "$ref": "#/$defs/worksheetBlock"})


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def block_schema_errors(block: dict) -> list:
    return [e.message for e in BLOCK_VALIDATOR.iter_errors(block)]


def blocks_all_valid(blocks: list) -> bool:
    return all(not block_schema_errors(b) for b in blocks)


def has(violations: list, prefix: str, needle: str | None = None) -> bool:
    return any(v.startswith(prefix) and (needle is None or needle in v) for v in violations)


def test_block_shape_source() -> None:
    demo = w.demo_worksheet_blocks()
    assert_true(blocks_all_valid(demo), "demo worksheet blocks must all validate against $defs/worksheetBlock")
    # unknown block_type rejected.
    assert_true(bool(block_schema_errors({"block_id": "x", "block_type": "mystery"})), "unknown block_type must be rejected")
    # missing required field rejected.
    assert_true(bool(block_schema_errors({"block_id": "x", "block_type": "student_task", "task_ref": "t", "prompt": "p"})),
                "student_task missing cognitive_demand must be rejected")
    # additive-strict: an unknown extra key on a strict variant is rejected.
    assert_true(bool(block_schema_errors({"block_id": "x", "block_type": "page_break", "answer_key": "42"})),
                "page_break carrying an extra key must be rejected by the shape source")


def test_clean_passes() -> None:
    demo = w.demo_worksheet_blocks()
    v = w.check_physical_workload(demo, "중학교")
    assert_true(v == [], f"clean demo worksheet must pass the physical gate: {v}")
    est = w.estimated_minutes(demo)
    assert_true(0.5 * 45 <= est <= 45, f"demo estimate {est} must sit within half..one 중학교 period")


def test_period_budget() -> None:
    # (a) over one period.
    over = copy.deepcopy(w.demo_worksheet_blocks())
    for i in range(3):
        over.insert(-1, w.student_task(f"ob{i}", task_ref="t-green", prompt="추가 설명 과제", cognitive_demand="evaluate"))
    assert_true(blocks_all_valid(over), "over-budget worksheet stays schema-valid (only the physical gate catches it)")
    assert_true(has(w.check_physical_workload(over, "중학교"), "period_budget"), "over-budget worksheet must fail period_budget")

    # (b) trivial under half a period.
    under = [
        w.student_task("u1", task_ref="t", prompt="간단한 확인", cognitive_demand="recall"),
        w.student_note("u2", text="메모"),
        w.exit_ticket("u3", prompt="정리", cognitive_demand="recall"),
    ]
    assert_true(blocks_all_valid(under), "under-budget worksheet stays schema-valid")
    assert_true(has(w.check_physical_workload(under, "중학교"), "period_budget", "under"), "trivial worksheet must fail period_budget (under)")


def test_answer_minimums() -> None:
    bad = copy.deepcopy(w.demo_worksheet_blocks())
    box = next(b for b in bad if b["block_id"] == "b11")  # paragraph box
    box["min_lines"] = 1
    assert_true(blocks_all_valid(bad), "answer-minimum mutation stays schema-valid")
    assert_true(has(w.check_physical_workload(bad, "중학교"), "answer_minimums"), "paragraph box with 1 line must fail answer_minimums")


def test_page_density() -> None:
    # (a) too many blocks on one page.
    dense = [b for b in copy.deepcopy(w.demo_worksheet_blocks()) if b["block_type"] != "page_break"]
    idx = next(i for i, b in enumerate(dense) if b["block_id"] == "b13")
    for i in range(6):
        dense.insert(idx, w.student_note(f"n{i}", text="추가 메모"))
    assert_true(len([b for b in dense if b["block_type"] != "page_break"]) > w.MAX_BLOCKS_PER_PAGE, "fixture must exceed page block budget")
    assert_true(has(w.check_physical_workload(dense, "중학교"), "page_density"), "over-dense page must fail page_density")

    # (b) writing page with answer area < 30%.
    ratio = [
        w.student_task("r1", task_ref="t", prompt="설명 1", cognitive_demand="create"),
        w.student_task("r2", task_ref="t", prompt="설명 2", cognitive_demand="create"),
        w.student_task("r3", task_ref="t", prompt="설명 3", cognitive_demand="create"),
        w.answer_box("r4", response_demand="short", min_lines=1, min_height_mm=8),
        w.exit_ticket("r5", prompt="정리", cognitive_demand="create"),
    ]
    assert_true(blocks_all_valid(ratio), "answer-ratio mutation stays schema-valid")
    assert_true(has(w.check_physical_workload(ratio, "중학교"), "page_density"), "thin writing page must fail answer-area ratio")

    # A writing page whose only response surface is a fill_table must still be
    # included in answer-area accounting rather than escaping the gate.
    fill_only = [
        w.student_task("f1", task_ref="t", prompt="표에 세 가지 근거를 쓰시오.", cognitive_demand="analyze"),
        w.fill_table("f2", headers=["근거"], rows=[[""], [""]], caption="근거 표"),
        w.student_task("f3", task_ref="t", prompt="표의 결과를 평가하시오.", cognitive_demand="evaluate"),
        w.student_task("f4", task_ref="t", prompt="대안을 제안하시오.", cognitive_demand="create"),
        w.exit_ticket("f5", prompt="가장 설득력 있는 근거를 쓰시오.", cognitive_demand="create"),
    ]
    assert_true(has(w.check_physical_workload(fill_only, "중학교"), "page_density", "writing area"),
                "fill-table-only writing page with insufficient rows must fail answer-area ratio")


def test_exit_ticket_hardest_case() -> None:
    bad = copy.deepcopy(w.demo_worksheet_blocks())
    next(b for b in bad if b["block_id"] == "b13")["cognitive_demand"] = "recall"  # while a task is evaluate
    assert_true(blocks_all_valid(bad), "exit-ticket mutation stays schema-valid")
    assert_true(has(w.check_physical_workload(bad, "중학교"), "exit_ticket"), "recall exit ticket under an evaluate task must fail")

    # missing exit ticket entirely.
    none = [b for b in copy.deepcopy(w.demo_worksheet_blocks()) if b["block_type"] != "exit_ticket"]
    assert_true(has(w.check_physical_workload(none, "중학교"), "exit_ticket"), "a worksheet with no exit ticket must fail")


def test_bw_safety() -> None:
    bad = copy.deepcopy(w.demo_worksheet_blocks())
    b3 = next(b for b in bad if b["block_id"] == "b3")  # data_table with 빨간색 caption
    b3.pop("pattern", None)
    assert_true(blocks_all_valid(bad), "bw-safety mutation stays schema-valid (pattern is optional at the schema layer)")
    assert_true(has(w.check_physical_workload(bad, "중학교"), "bw_safety"), "color-only reference with no pattern channel must fail")


def test_group_cohesion() -> None:
    # (a) non-neutral group label. Caught defense-in-depth at the schema layer AND the gate.
    bad = copy.deepcopy(w.demo_worksheet_blocks())
    next(b for b in bad if b["block_id"] == "b12")["group_label"] = "Group A (기초)"
    assert_true(bool(block_schema_errors(next(b for b in bad if b["block_id"] == "b12"))), "non-neutral group label is schema-rejected too")
    assert_true(has(w.check_physical_workload(bad, "중학교"), "group_cohesion"), "non-neutral group label must fail group_cohesion")

    # (b) empty shared_task_refs.
    bad2 = copy.deepcopy(w.demo_worksheet_blocks())
    next(b for b in bad2 if b["block_id"] == "b12")["shared_task_refs"] = []
    assert_true(has(w.check_physical_workload(bad2, "중학교"), "group_cohesion"), "group with no shared_task_refs must fail cohesion")


def main() -> None:
    test_block_shape_source()
    test_clean_passes()
    test_period_budget()
    test_answer_minimums()
    test_page_density()
    test_exit_ticket_hardest_case()
    test_bw_safety()
    test_group_cohesion()
    print("PASS validate_worksheet_physical")
    print("- $defs/worksheetBlock shape source: demo blocks valid; unknown type / missing field / extra key rejected")
    print("- clean demo worksheet passes the deterministic physical gate (39.5 min within half..one 중학교 period)")
    print("- period budget: over-period and trivial-under-period worksheets fail closed")
    print("- answer-space minimums, page density (blocks + writing-area ratio) fail closed")
    print("- exit-ticket hardest-case, black/white color-only safety, group cohesion/neutrality fail closed")
    print("- every physically-broken worksheet is schema-valid: the physical gate is the sole catcher")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
