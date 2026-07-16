#!/usr/bin/env python3
"""Focused validator: 개별화 (individualized) material package.

One SharedRegistry -> exactly four canonical documents inside the single
lesson-package IR:
  - teacher-individualized-plan  (document_class individualized-plan, facet teacher)
  - worksheet-group-a/b/c        (document_class worksheet, facet student)

The common goal / tasks / success criteria / hardest-case exit ticket are IDENTICAL
across every group; only the student-safe supports and response guidance differ.
Teacher-only pathway meanings and rigor evidence live ONLY on the teacher plan and
must never leak into a student worksheet. Independent implementation (no vendored code).
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
    check_facet_separation,
    check_bidirectional_alignment,
    TeacherApprovalGate,
    worksheet as ws,
)
from providers.materials.individualized import (  # noqa: E402
    IndividualizedPathway,
    GROUP_LABELS,
    build_individualized_package_ir,
    validate_individualized_package,
    package_core_fingerprint,
    STUDENT_DIAGNOSTIC_TERMS,
)
from renderers import render_all, render_package, extract_all, verify_parity  # noqa: E402

IR_SCHEMA = json.loads((ROOT / "schemas" / "lesson-package-ir.schema.json").read_text(encoding="utf-8"))
BASE_IR = json.loads((ROOT / "tests" / "golden" / "lesson-package-ir" / "downstream-ready.json").read_text(encoding="utf-8"))
APPROVAL = json.loads((ROOT / "tests" / "golden" / "materials" / "approval.json").read_text(encoding="utf-8"))
PACKAGE_GOLDEN = ROOT / "tests" / "golden" / "individualized-materials" / "9과17-01.package.json"

TEACHER_DOC = "teacher-individualized-plan"
GROUP_DOCS = {"Group A": "worksheet-group-a", "Group B": "worksheet-group-b", "Group C": "worksheet-group-c"}
ALL_DOC_IDS = {TEACHER_DOC, *GROUP_DOCS.values()}


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def sample_shared() -> SharedRegistry:
    return SharedRegistry(
        standard_code="[9과17-01]",
        standard_student_language="대기권을 4개 층으로 나누어 설명하고, 온실효과를 예로 들 수 있다.",
        standard_teacher_text="지구 대기권을 4개 권역으로 구분하며, 온실효과와 지구온난화를 복사 평형의 관점으로 설명할 수 있다.",
        tasks=[
            {"task_id": "t-atmos", "title": "탐구", "student_instructions": "대기 자료를 읽고 대기권을 네 개 층으로 구분하여 표시한다.",
             "teacher_notes": "층 구분 기준을 스스로 세우게 한다.", "writing_space": True, "cognitive_demand": "analyze"},
            {"task_id": "t-green", "title": "설명", "student_instructions": "온실효과가 커질 때 대기 온도 변화를 복사 평형으로 설명한다.",
             "teacher_notes": "복사 평형 관점을 연결하도록 발문한다.", "writing_space": True, "cognitive_demand": "evaluate"},
        ],
        success_criteria=["대기권을 4개 층으로 구분할 수 있다", "온실효과를 복사 평형으로 설명할 수 있다"],
        exit_ticket={"prompt": "온실효과가 계속 커지면 지표면 온도는 어떻게 될지 근거와 함께 쓰시오.", "targets_hardest_case": True},
        misconceptions=[{"what": "온실효과=대기오염", "why": "일상어 혼동", "teacher_response": "복사 평형으로 재설명"}],
        rubric=[{"criterion": "근거 사용", "levels": ["상", "중", "하"]}],
    )


def sample_pathways() -> list:
    return [
        IndividualizedPathway(
            group_label="Group A",
            teacher_profile_label="자료 해석에 추가 발판이 필요한 학습자",
            access_supports=["핵심 용어에 밑줄이 표시된 자료를 사용한다.", "단계별 안내 질문을 함께 제공한다."],
            representation_supports=["그림과 표로 정보를 함께 제시한다."],
            response_options=["문장 또는 그림과 문장을 함께 사용해 답한다."],
            rigor_evidence="동일한 분석·설명 과제와 가장 어려운 사례 출구표를 그대로 수행한다.",
        ),
        IndividualizedPathway(
            group_label="Group B",
            teacher_profile_label="핵심 과제를 독립적으로 수행하는 학습자",
            access_supports=["필요할 때만 참고할 수 있는 힌트 카드를 둔다."],
            representation_supports=["자료를 글 중심으로 제시한다."],
            response_options=["문장으로 설명한다."],
            rigor_evidence="공통 과제와 동일한 출구표를 동일 기준으로 수행한다.",
        ),
        IndividualizedPathway(
            group_label="Group C",
            teacher_profile_label="빠르게 도달하여 확장 연결이 필요한 학습자",
            access_supports=["자료를 스스로 조직하도록 최소한의 안내만 제공한다."],
            representation_supports=["원자료를 그대로 제시한다."],
            response_options=["문장과 도식을 함께 사용한다."],
            rigor_evidence="공통 과제를 수행한 뒤 인과 관계를 새로운 상황에 적용한다.",
            extension_move={"cognitive_operation": "create",
                            "move": "관측 자료로 새로운 예측을 구성하고 반례가 되는 상황을 설계한다."},
        ),
    ]


def build_sample_ir() -> dict:
    return build_individualized_package_ir(sample_shared(), sample_pathways(), BASE_IR)


def _docs(ir: dict) -> dict:
    return {d["document_id"]: d for d in ir["lesson_package"]["documents"]}


def _student_docs(ir: dict) -> list:
    return [d for d in ir["lesson_package"]["documents"] if d["content"].get("facet") == "student"]


# --------------------------------------------------------------------------- #
# 1. RED-frozen contract: shape, IDs, facets, shared contract, teacher-only meaning
# --------------------------------------------------------------------------- #

def test_package_contract() -> None:
    ir = build_sample_ir()

    errors = sorted(jsonschema.Draft202012Validator(IR_SCHEMA).iter_errors(ir), key=lambda e: list(e.path))
    assert_true(not errors, f"individualized package IR must be schema-valid: {errors[0].message if errors else ''}")

    assert_true(validate_individualized_package(ir) == [], f"clean package must validate: {validate_individualized_package(ir)}")

    docs = _docs(ir)
    assert_true(set(docs) == ALL_DOC_IDS, f"exactly four documents expected: {set(docs)}")
    assert_true(docs[TEACHER_DOC]["document_class"] == "individualized-plan", "teacher plan class")
    assert_true(docs[TEACHER_DOC]["content"]["facet"] == "teacher", "teacher plan facet")
    for gid in GROUP_DOCS.values():
        assert_true(docs[gid]["document_class"] == "worksheet", f"{gid} must be a worksheet")
        assert_true(docs[gid]["content"]["facet"] == "student", f"{gid} must be a student facet")

    # identical source_task_ids on every document.
    task_id_sets = {tuple(d["source_task_ids"]) for d in docs.values()}
    assert_true(len(task_id_sets) == 1, f"every document must carry identical source_task_ids: {task_id_sets}")

    # student labels exactly Group A|B|C.
    labels = sorted(d["content"]["individualization_contract"]["group_label"] for d in _student_docs(ir))
    assert_true(labels == list(GROUP_LABELS), f"student labels must be exactly Group A|B|C: {labels}")

    # shared target/task/success/exit contract identical across every document (support may differ).
    fingerprints = {package_core_fingerprint(d) for d in docs.values()}
    assert_true(len(fingerprints) == 1, "shared target/task/success/exit contract must be identical across all four docs")

    # teacher plan alone carries pathway meanings + rigor evidence.
    profiles = docs[TEACHER_DOC]["content"]["pathway_profiles"]
    assert_true({p["group_label"] for p in profiles} == set(GROUP_LABELS), "teacher plan must carry all three pathway profiles")
    for p in profiles:
        assert_true(p["rigor_evidence"].strip(), "each pathway profile must carry rigor evidence")
        assert_true(p["teacher_profile_label"].strip(), "each pathway profile must carry a teacher profile label")
    for d in _student_docs(ir):
        assert_true("pathway_profiles" not in d["content"], "student worksheet must NOT carry pathway_profiles")

    # student worksheets are leak-clean (existing facet gate) and diagnostic-clean (package gate).
    ok, viol = check_facet_separation(ir)
    assert_true(ok, f"student worksheets must pass facet separation: {viol}")


# --------------------------------------------------------------------------- #
# 2. Model guards
# --------------------------------------------------------------------------- #

def test_pathway_model_guards() -> None:
    def expect_value_error(fn, name):
        try:
            fn()
        except ValueError:
            return
        raise AssertionError(f"{name}: expected ValueError")

    expect_value_error(lambda: IndividualizedPathway(
        group_label="Group D", teacher_profile_label="x", access_supports=[], representation_supports=[],
        response_options=[], rigor_evidence="ok"), "label_out_of_range")
    expect_value_error(lambda: IndividualizedPathway(
        group_label="Group A", teacher_profile_label="x", access_supports=[], representation_supports=[],
        response_options=[], rigor_evidence="  "), "missing_rigor_evidence")

    shared = sample_shared()
    # duplicate labels rejected at build time.
    dup = [sample_pathways()[0], sample_pathways()[0], sample_pathways()[2]]
    try:
        build_individualized_package_ir(shared, dup, BASE_IR)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate group labels must be rejected")
    # omitted group rejected at build time.
    try:
        build_individualized_package_ir(shared, sample_pathways()[:2], BASE_IR)
    except ValueError:
        pass
    else:
        raise AssertionError("omitting a group must be rejected")


# --------------------------------------------------------------------------- #
# 3. Schema positive + negative mutations
# --------------------------------------------------------------------------- #

def test_schema_mutations() -> None:
    validator = jsonschema.Draft202012Validator(IR_SCHEMA)
    ir = build_sample_ir()
    assert_true(not list(validator.iter_errors(ir)), "positive schema case must pass")

    def schema_invalid(mutate, name):
        bad = copy.deepcopy(ir)
        mutate(bad)
        assert_true(bool(list(validator.iter_errors(bad))), f"{name}: mutated IR must be schema-invalid")

    def set_student_label(bad, label):
        for d in bad["lesson_package"]["documents"]:
            if d["content"].get("facet") == "student":
                d["content"]["individualization_contract"]["group_label"] = label
                return
    schema_invalid(lambda b: set_student_label(b, "Group D"), "non_neutral_label")
    schema_invalid(lambda b: set_student_label(b, "Group A 기초"), "decorated_label")

    def drop_exit(bad):
        for d in bad["lesson_package"]["documents"]:
            d["content"]["individualization_contract"].pop("exit_id", None)
    schema_invalid(drop_exit, "missing_shared_exit")

    def teacher_profile_on_student(bad):
        for d in bad["lesson_package"]["documents"]:
            if d["content"].get("facet") == "student":
                d["content"]["pathway_profiles"] = copy.deepcopy(
                    _docs(ir)[TEACHER_DOC]["content"]["pathway_profiles"])
                return
    schema_invalid(teacher_profile_on_student, "teacher_profile_on_student_doc")


# --------------------------------------------------------------------------- #
# 4. Rigor + leak gates (semantic validator negative mutations)
# --------------------------------------------------------------------------- #

def test_rigor_and_leak_gates() -> None:
    base = build_sample_ir()
    assert_true(validate_individualized_package(base) == [], "clean package must have no issues")

    def issues(mutate):
        bad = copy.deepcopy(base)
        mutate(bad)
        return validate_individualized_package(bad)

    def group_doc(bad, gid):
        return _docs(bad)[GROUP_DOCS[gid]]

    # remove a core task (student_task block) from Group A.
    def remove_core_task(bad):
        d = group_doc(bad, "Group A")
        d["content"]["blocks"] = [b for b in d["content"]["blocks"]
                                  if not (b["block_type"] == "student_task" and b["task_ref"] == "t-atmos")]
    assert_true(any("core task" in i or "coverage" in i for i in issues(remove_core_task)),
                "dropping a core task from a group must be flagged")

    # replace the hardest-case exit ticket with an easier one.
    def weaken_exit(bad):
        d = group_doc(bad, "Group B")
        for b in d["content"]["blocks"]:
            if b["block_type"] == "exit_ticket":
                b["prompt"] = "오늘 배운 낱말을 하나 쓰시오."
                b["cognitive_demand"] = "recall"
    assert_true(any("exit" in i for i in issues(weaken_exit)), "weakening the hardest-case exit must be flagged")

    # remove rigor evidence from a pathway profile.
    def strip_rigor(bad):
        _docs(bad)[TEACHER_DOC]["content"]["pathway_profiles"][0]["rigor_evidence"] = "   "
    assert_true(any("rigor" in i for i in issues(strip_rigor)), "missing rigor evidence must be flagged")

    # diagnostic / internal-level language planted in a student worksheet (variants).
    diagnostic_variants = {
        "plain_internal_level": "심화 과정 안내",
        "spaced_internal_level": "기 초 단계입니다",
        "zero_width_internal_level": "표\u200b준 경로입니다",
        "english_tier": "tier 2 support",
        "english_below": "below grade level",
        "level_grouping": "수준별 이동 안내",
    }
    for name, text in diagnostic_variants.items():
        def plant(bad, _text=text):
            d = group_doc(bad, "Group C")
            d["content"]["blocks"].insert(0, ws.student_note(f"leak-{name}", text=_text))
        assert_true(bool(issues(plant)), f"{name}: diagnostic language in a student worksheet must be flagged")

    # a diagnostic term smuggled as a structural KEY (not a value) must also be flagged.
    def plant_diagnostic_key(bad):
        block = ws.student_note("leak-key", text="메모")
        block["tier"] = "2"
        group_doc(bad, "Group C")["content"]["blocks"].insert(0, block)
    assert_true(bool(issues(plant_diagnostic_key)), "diagnostic term as a student block key must be flagged")

    # teacher profile label leaking into a student worksheet.
    def leak_profile_label(bad):
        d = group_doc(bad, "Group A")
        label = _docs(base)[TEACHER_DOC]["content"]["pathway_profiles"][0]["teacher_profile_label"]
        d["content"]["blocks"].insert(0, ws.student_note("leak-label", text=label))
    assert_true(bool(issues(leak_profile_label)), "teacher profile label leaking into a student doc must be flagged")

    # duplicate a group (two docs claim Group A) and omit a group.
    def duplicate_group(bad):
        _docs(bad)[GROUP_DOCS["Group B"]]["content"]["individualization_contract"]["group_label"] = "Group A"
    assert_true(bool(issues(duplicate_group)), "duplicate group label across docs must be flagged")

    # quantity-only extension (no cognitive-operation change).
    def quantity_only_extension(bad):
        _docs(bad)[TEACHER_DOC]["content"]["pathway_profiles"][2]["extension_move"] = {
            "cognitive_operation": "analyze", "move": "같은 유형의 문제를 10개 더 푼다."}
    assert_true(any("extension" in i for i in issues(quantity_only_extension)),
                "a quantity-only extension must be flagged")

    # false-positive controls: legitimate student phrases must not manufacture issues.
    legitimate = [
        "발표 준비를 시작합니다.",
        "표를 준비해 관찰 결과를 적습니다.",
        "초록 식물의 잎을 관찰합니다.",
        "친구의 설명을 이해하고 비교합니다.",
        "자료의 표준편차를 계산합니다.",
        "운동 전후의 기초 대사량을 비교합니다.",
        "진단검사의 민감도와 특이도를 해석합니다.",
    ]
    for phrase in legitimate:
        def plant_safe(bad, _p=phrase):
            group_doc(bad, "Group A")["content"]["blocks"].insert(0, ws.student_note("safe", text=_p))
        assert_true(issues(plant_safe) == [], f"legitimate phrase must not be flagged: {phrase}")


# --------------------------------------------------------------------------- #
# 5. Package renderer: 12 files, per-doc parity, cross-doc shared contract
# --------------------------------------------------------------------------- #

def test_package_renderer() -> None:
    ir = build_sample_ir()
    with tempfile.TemporaryDirectory() as td:
        rendered = render_package(ir, td)
        assert_true(set(rendered) == ALL_DOC_IDS, f"render_package must render all four documents: {set(rendered)}")
        files = [Path(p) for doc in rendered.values() for p in doc.values()]
        assert_true(len(files) == 12, f"exactly 12 files expected, got {len(files)}")
        for f in files:
            assert_true(f.exists() and f.stat().st_size > 200, f"{f} must be a non-trivial rendered file")

        # each document: valid ZIP/XML members, embedded marker, exact round-trip, 3-format parity.
        for did, paths in rendered.items():
            ex = extract_all(paths)
            pok, preasons = verify_parity(ex)
            assert_true(pok, f"{did}: within-document 3-format parity failed: {preasons}")
            for fmt, member in (("hwpx", "Contents/section0.xml"), ("docx", "word/document.xml")):
                with zipfile.ZipFile(paths[fmt]) as z:
                    names = set(z.namelist())
                    assert_true(member in names, f"{did} {fmt}: missing {member}")
                    marker = "META-INF/kteacher-backport-marker.json" if fmt == "hwpx" else "customXml/kteacher-backport-marker.json"
                    assert_true(marker in names, f"{did} {fmt}: missing embedded marker member")
                    ET.fromstring(z.read(member))  # must be well-formed XML

        # cross-document validator: shared contract fingerprint identical, support blocks differ.
        docs = _docs(ir)
        fps = {package_core_fingerprint(d) for d in docs.values()}
        assert_true(len(fps) == 1, "cross-document shared contract fingerprint must be identical")
        group_block_texts = []
        for gid in GROUP_DOCS.values():
            blocks = docs[gid]["content"]["blocks"]
            support = [b for b in blocks if b["block_type"] in ("student_note", "source_card", "sentence_support")]
            group_block_texts.append(json.dumps(support, ensure_ascii=False, sort_keys=True))
        assert_true(len(set(group_block_texts)) == 3, "each group's support blocks must differ (individualized supports)")

        # core task prompts + exit ticket are byte-identical across the three worksheets.
        core = []
        for gid in GROUP_DOCS.values():
            blocks = docs[gid]["content"]["blocks"]
            shared = [b for b in blocks if b["block_type"] in ("student_task", "exit_ticket")]
            core.append(json.dumps(shared, ensure_ascii=False, sort_keys=True))
        assert_true(len(set(core)) == 1, "core tasks + exit ticket must be identical across all three worksheets")

        # duplicate document id / unsupported render target are refused.
        dup = copy.deepcopy(ir)
        dup["lesson_package"]["documents"].append(copy.deepcopy(dup["lesson_package"]["documents"][1]))
        try:
            render_package(dup, Path(td) / "dup")
        except ValueError:
            pass
        else:
            raise AssertionError("duplicate document id must be refused")

        bad_target = copy.deepcopy(ir)
        bad_target["lesson_package"]["documents"][1]["render_targets"] = ["pdf"]
        try:
            render_package(bad_target, Path(td) / "badtarget")
        except ValueError:
            pass
        else:
            raise AssertionError("unsupported render target must be refused")


# --------------------------------------------------------------------------- #
# 6. Physical worksheet contract (per group)
# --------------------------------------------------------------------------- #

def test_physical_worksheet_contract() -> None:
    ir = build_sample_ir()
    docs = _docs(ir)
    for gid in GROUP_DOCS.values():
        blocks = docs[gid]["content"]["blocks"]
        violations = ws.check_physical_workload(blocks, "중학교")
        assert_true(violations == [], f"{gid} must pass the 45-minute 중학교 physical gate: {violations}")
        # real answer space + real task prompt + exit ticket present.
        assert_true(any(b["block_type"] == "student_task" for b in blocks), f"{gid}: must carry real task prompts")
        assert_true(any(b["block_type"] in ("answer_box", "fill_table") for b in blocks), f"{gid}: must carry writing space")
        assert_true(sum(1 for b in blocks if b["block_type"] == "exit_ticket") == 1, f"{gid}: exactly one exit ticket")

    # negative: insufficient write rows fails; missing exit ticket fails.
    thin = [ws.student_task("t", task_ref="t-atmos", prompt="설명하시오.", cognitive_demand="analyze"),
            ws.answer_box("a", response_demand="short", min_lines=1, min_height_mm=8),
            ws.exit_ticket("e", prompt="가장 어려운 사례를 설명하시오.", cognitive_demand="analyze")]
    assert_true(ws.check_physical_workload(thin, "중학교") != [], "thin worksheet must fail the physical gate")

    no_exit = [b for b in docs[GROUP_DOCS["Group A"]]["content"]["blocks"] if b["block_type"] != "exit_ticket"]
    assert_true(any("exit_ticket" in v for v in ws.check_physical_workload(no_exit, "중학교")),
                "missing exit ticket must fail the physical gate")


# --------------------------------------------------------------------------- #
# 7. Approval / provenance fail-closed
# --------------------------------------------------------------------------- #

def test_approval_and_provenance() -> None:
    ir = build_sample_ir()

    # bidirectional alignment holds across teacher plan <-> student worksheets.
    aok, aissue = check_bidirectional_alignment(ir)
    assert_true(aok, f"teacher/student task alignment must hold: {aissue}")

    # no approval -> downstream blocked.
    assert_true(TeacherApprovalGate.evaluate(ir, None).downstream_ready is False, "no approval -> blocked")
    assert_true(TeacherApprovalGate.evaluate(ir, {"decision": "rejected", "approver_role": "teacher"}).downstream_ready is False,
                "rejected -> blocked")
    # valid teacher approval + verified provider -> ready.
    assert_true(TeacherApprovalGate.evaluate(ir, APPROVAL).downstream_ready is True, "valid teacher approval -> ready")

    # unverified / inferred curriculum provenance -> never a deployable canonical IR (schema fail-closed).
    draft = copy.deepcopy(ir)
    draft["provider_contract"]["provenance_status"] = "inferred"
    assert_true(bool(list(jsonschema.Draft202012Validator(IR_SCHEMA).iter_errors(draft))),
                "unverified/inferred provenance must not validate as a canonical (deployable) IR")

    # teacher pathway metadata stays PII-free.
    teacher = _docs(ir)[TEACHER_DOC]
    import re as _re
    pii = _re.compile(r"\d{3}-\d{3,4}-\d{4}|@[a-z]|\b010\d{7,8}\b", _re.IGNORECASE)
    for leaf in ws.iter_block_string_leaves(teacher["content"].get("pathway_profiles", [])):
        assert_true(not pii.search(leaf), f"pathway metadata must be PII-free: {leaf}")


# --------------------------------------------------------------------------- #
# 8. Committed golden
# --------------------------------------------------------------------------- #

def test_package_golden() -> None:
    golden = json.loads(PACKAGE_GOLDEN.read_text(encoding="utf-8"))
    built = build_sample_ir()
    assert_true(built == golden, "built individualized package IR must equal the committed golden")


def main() -> None:
    test_package_contract()
    test_pathway_model_guards()
    test_schema_mutations()
    test_rigor_and_leak_gates()
    test_package_renderer()
    test_physical_worksheet_contract()
    test_approval_and_provenance()
    test_package_golden()
    print("PASS validate_individualized_materials")
    print("- one SharedRegistry -> teacher-individualized-plan + worksheet-group-a/b/c in one schema-valid IR")
    print("- common goal/tasks/success/hardest-case exit identical across groups; only supports differ")
    print("- teacher-only pathway meanings + rigor evidence never leak into student worksheets")
    print("- schema forbids non-neutral labels, missing shared exit, teacher profiles on student docs")
    print("- rigor/leak gates catch dropped tasks, weakened exits, diagnostic language, quantity-only extensions")
    print("- render_package emits 12 real HWPX/DOCX/HTML files with per-doc parity + shared cross-doc contract")
    print("- every group passes the 45-minute 중학교 physical worksheet gate")
    print("- approval + provenance stay fail-closed; teacher pathway metadata is PII-free")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
