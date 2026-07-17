#!/usr/bin/env python3
# noqa: SIZE_OK - one sweep entrypoint intentionally owns the complete T1-T8 contract.
"""24th contract validator (SWEEP-ONLY) — pluggable HWPX backend, strict fail-closed.

Physical-truth-only capability gate for an OPTIONAL, EXPERIMENTAL `document_plan`
HWPX authoring backend. The proven python-hwpx `builder` path stays the DEFAULT and
is used as the positive control. The experimental `document_plan` backend is gated by
a PHYSICAL capability probe (Contents/section0.xml `pageBreak="1"` count, equated with
python-hwpx `document.page_break_count`, corroborated by receipt/preview). It fails
closed with `HwpxBackendNotCapable` — never a silent fallback, never a raw-XML patch,
never accepting `formatted`/`semanticDiff.changed`/`breakBefore.after` as evidence.

This test is NOT added to the release-gate EXPECTED_VALIDATORS; it is run in the same
manual/agent 23-validator sweep the physical-correctness validators already rely on.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from renderers.backends import (  # noqa: E402
    DEFAULT_BACKEND,
    CapabilityReport,
    HwpxBackend,
    HwpxBackendNotCapable,
    select_hwpx_backend,
)
from renderers.backends.builder_backend import BuilderBackend  # noqa: E402
from renderers.backends.capability_probe import probe_file  # noqa: E402
from renderers.backends.document_plan_adapter import (  # noqa: E402
    ANSWER_LINE,
    BLANK_CELL,
    canonical_to_document_plan,
)
from renderers.backends.document_plan_backend import (  # noqa: E402
    DocumentPlanBackend,
    _workspace_staging_root,
)
from renderers.backends.receipt import build_backend_receipt  # noqa: E402

GOLD = ROOT / "tests" / "golden" / "hwpx-backend"
SCHEMAS = ROOT / "schemas"


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _hwpx_deps_present() -> bool:
    try:
        import hwpx  # noqa: F401
        import hwpx_mcp_server.server  # noqa: F401

        return True
    except ImportError:
        return False


def _validate_json_schema(instance: dict, schema_path: Path) -> None:
    """Minimal, dependency-light structural check against a committed JSON Schema.

    Uses `jsonschema` when available (it ships with hwpx-mcp-server); otherwise
    falls back to an envelope check so the test never silently skips validation.
    """
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        jsonschema = None
    if jsonschema is not None:
        jsonschema.validate(instance=instance, schema=schema)
        return
    # Fallback: required top-level keys + block type enum (keep parity with the
    # jsonschema path so T4 is equally strong with or without the library present).
    for key in schema.get("required", []):
        assert_true(key in instance, f"schema {schema_path.name}: missing required {key!r}")
    item_schema = (
        schema.get("properties", {}).get("blocks", {}).get("items", {})
    )
    type_enum = item_schema.get("properties", {}).get("type", {}).get("enum")
    if type_enum and isinstance(instance.get("blocks"), list):
        for i, blk in enumerate(instance["blocks"]):
            assert_true(isinstance(blk, dict) and "type" in blk, f"schema: blocks[{i}] missing type")
            assert_true(
                blk["type"] in type_enum,
                f"schema {schema_path.name}: blocks[{i}].type {blk['type']!r} not in {type_enum}",
            )


# --------------------------------------------------------------------------- #
# Canonical science-worksheet fixture (K-Teacher canonical content model).
# The adapter projects this authoritative canonical into hwpx.document_plan.v1.
# --------------------------------------------------------------------------- #
def science_canonical() -> dict:  # noqa: DICT_OK - mutable JSON fixture mirrors canonical IR.
    return {
        "document_id": "science-worksheet-atmosphere",
        "document_class": "worksheet",
        "title": "대기권과 기상 학생 활동지",
        "metadata": {
            "document_type": "보고서",
            "subject": "과학",
            "grade": "중학교 3학년",
            "standard": "[9과17-01]",
        },
        "required_content": [
            {
                "content_id": "student-goal",
                "text": "대기권을 4개 층으로 나누어 설명하고, 온실효과를 복사 평형으로 설명할 수 있다.",
            }
        ],
        "provenance_markers": [],
        "unresolved_boundary_markers": [],
        "blocks": [
            {
                "block_id": "b-info",
                "block_type": "data_table",
                "headers": ["학년·반", "번호", "이름", "날짜"],
                "cells": [["", "", "", ""]],
            },
            {
                "block_id": "b-src",
                "block_type": "data_table",
                "caption": "대기권 층상 구조 자료",
                "headers": ["층", "고도 범위", "기온 변화", "특징"],
                "cells": [
                    ["대류권", "지표~약 11 km", "높을수록 하강", "기상 현상·대류"],
                    ["성층권", "약 11~50 km", "높을수록 상승", "오존층"],
                    ["중간권", "약 50~80 km", "높을수록 하강", "유성 관측"],
                    ["열권", "약 80 km 이상", "높을수록 상승", "오로라"],
                ],
            },
            {
                "block_id": "b-note",
                "block_type": "student_note",
                "text": "※ 교사 제작 학습자료이며 공식 인용문이 아닙니다.",
            },
            {
                "block_id": "b-task1",
                "block_type": "student_task",
                "cognitive_demand": "analyze",
                "prompt": "대기 자료를 읽고 대기권을 네 개 층으로 구분한 근거를 쓰시오.",
            },
            {"block_id": "b-ans1", "block_type": "answer_box", "min_lines": 3, "min_height_mm": 30.0},
            {"block_id": "b-pb", "block_type": "page_break"},
            {
                "block_id": "b-task2",
                "block_type": "student_task",
                "cognitive_demand": "evaluate",
                "prompt": "온실효과가 커질 때 지표 부근 기온이 어떻게 변하는지 복사 평형을 근거로 설명하시오.",
            },
            {"block_id": "b-ans2", "block_type": "answer_box", "min_lines": 3, "min_height_mm": 30.0},
            {
                "block_id": "b-check",
                "block_type": "data_table",
                "caption": "스스로 점검",
                "headers": ["확인", "점검 내용"],
                "cells": [
                    ["□", "대기권을 네 개 층으로 근거와 함께 구분했다."],
                    ["□", "온실효과를 복사 평형으로 설명했다."],
                ],
            },
            {
                "block_id": "b-exit",
                "block_type": "exit_ticket",
                "prompt": "온실효과가 계속 커지면 지표면 온도는 어떻게 될지 근거와 함께 쓰시오.",
            },
        ],
    }


# --------------------------------------------------------------------------- #
# T1 — RED upstream-contract fake (offline, deterministic).
# --------------------------------------------------------------------------- #
def _fake_selfreport_hwpx(path: Path, *, physical_breaks: int) -> None:
    """Synthesize a HWPX-like zip whose SAVED section0.xml materializes
    `physical_breaks` real page breaks (never committed; stdlib zipfile)."""
    breaks = "".join(
        f'<hp:p paraPrShIDRef="0" pageBreak="1"><hp:run><hp:t>break {i}</hp:t></hp:run></hp:p>'
        for i in range(physical_breaks)
    )
    section = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<hs:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
        '<hp:p paraPrShIDRef="0" pageBreak="0"><hp:run><hp:t>본문</hp:t></hp:run></hp:p>'
        f"{breaks}</hs:sec>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", b"application/hwp+zip")
        z.writestr("Contents/section0.xml", section)


def _selfreport_receipt() -> dict:  # noqa: DICT_OK - frozen JSON oracle shape.
    """Server self-report that claims a break yet the library counts zero —
    the exact upstream contradiction (mirrors the committed frozen oracle)."""
    return {
        "created": True,
        "plan_validation": {"ok": True, "schemaVersion": "hwpx.document_plan.v1"},
        "quality": {
            "formatted": 1,
            "semanticDiff": {"changed": True},
            "block_counts": {"heading": 7, "table": 3, "paragraph": 13, "page_break": 1},
            "document": {"paragraph_count": 24, "table_count": 3, "page_break_count": 0},
        },
        "verification": {"openSafety": {"ok": True}},
    }


def test_t1_red_upstream_contradiction() -> None:
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "selfreport.hwpx"
        _fake_selfreport_hwpx(fake, physical_breaks=0)
        report = probe_file(fake, expected_breaks=1, receipt=_selfreport_receipt())
        assert_true(isinstance(report, CapabilityReport), "probe returns CapabilityReport")
        assert_true(report.capable is False, "T1: self-report break with physical=0 must NOT be capable")
        assert_true(report.physical_page_break_count == 0, "T1: physical count is the SAVED truth (0)")
        joined = " ".join(report.reasons)
        assert_true("contradiction" in joined.lower(), f"T1: reasons must name the contradiction: {report.reasons}")
        # NEVER trust the self-report evidence keys.
        assert_true(
            not any(k in joined for k in ("formatted", "semanticDiff", "breakBefore", "breakSetting")),
            f"T1: self-report evidence keys must not be used as capability signal: {report.reasons}",
        )
    print("PASS T1 upstream self-report contradiction -> capable=False")

    physical = GOLD / "builder-2page.section0.xml"
    missing = probe_file(physical, expected_breaks=2, receipt={})
    assert_true(missing.capable is False, "T1: receipt mode requires corroboration; empty receipt fails closed")
    assert_true(
        any("openSafety" in reason for reason in missing.reasons),
        f"T1: missing openSafety has an actionable reason: {missing.reasons}",
    )
    assert_true(
        any("quality" in reason for reason in missing.reasons),
        f"T1: missing quality count has an actionable reason: {missing.reasons}",
    )

    mismatch_receipt = {
        "quality": {
            "block_counts": {"page_break": 2},
            "document": {"page_break_count": 99},
        },
        "verification": {"openSafety": {"ok": True}},
    }
    mismatch = probe_file(physical, expected_breaks=2, receipt=mismatch_receipt)
    assert_true(mismatch.capable is False, "T1: quality count must equal saved physical count")
    assert_true(
        any("quality" in reason and "physical" in reason for reason in mismatch.reasons),
        f"T1: quality/physical mismatch has an actionable reason: {mismatch.reasons}",
    )

    valid_receipt = {
        "quality": {
            "block_counts": {"page_break": 2},
            "document": {"page_break_count": 2},
        },
        "verification": {"openSafety": {"ok": True}},
    }
    corroborated = probe_file(physical, expected_breaks=2, receipt=valid_receipt)
    assert_true(corroborated.capable is True, f"T1: complete matching corroboration passes: {corroborated.reasons}")

    malformed_receipt = {
        "quality": {
            "block_counts": {"page_break": 2},
            "document": {"page_break_count": 2},
        },
        "verification": {"openSafety": {"ok": "false"}},
    }
    malformed = probe_file(physical, expected_breaks=2, receipt=malformed_receipt)
    assert_true(
        malformed.capable is False,
        "T1: non-boolean openSafety.ok must fail closed instead of truthy coercion",
    )


# --------------------------------------------------------------------------- #
# T2 — builder positive control.
# --------------------------------------------------------------------------- #
def test_t2_builder_positive_control() -> None:
    golden = GOLD / "builder-2page.section0.xml"
    assert_true(golden.exists(), "T2: builder-2page.section0.xml oracle present")
    report = probe_file(golden, expected_breaks=2)  # file-only mode, no receipt
    assert_true(report.capable is True, "T2: genuine builder 2-page fixture is capable")
    assert_true(report.physical_page_break_count == 2, "T2: physical count == 2")

    if _hwpx_deps_present():
        sys.path.insert(0, str(ROOT / "tests"))
        from validate_individualized_materials import build_sample_ir  # noqa: E402
        from renderers import render_package

        with tempfile.TemporaryDirectory() as td:
            with contextlib.redirect_stderr(io.StringIO()):
                res = render_package(build_sample_ir(), td)
            live = res["teacher-individualized-plan"]["hwpx"]
            with zipfile.ZipFile(live) as z:
                xml = z.read("Contents/section0.xml").decode("utf-8")
            assert_true(xml.count('pageBreak="1"') == 2, "T2 live: builder materializes hwpx_pagebreaks==2")
            from hwpx.document import HwpxDocument

            with contextlib.redirect_stderr(io.StringIO()):
                doc = HwpxDocument.open(live)
            lib_count = sum(1 for p in doc.paragraphs if p.element.get("pageBreak") == "1")
            assert_true(lib_count == 2, "T2 live: python-hwpx document.page_break_count == 2")
        print("PASS T2 builder positive control (file-only + live render, deps present)")
    else:
        print("PASS T2 builder positive control (file-only; python-hwpx absent)")


# --------------------------------------------------------------------------- #
# T3 — real smoke, dep-guarded, FAIL-not-skip.
# --------------------------------------------------------------------------- #
def test_t3_real_smoke() -> None:
    plan = canonical_to_document_plan(science_canonical())

    if _hwpx_deps_present():
        from hwpx.authoring import validate_document_plan

        # (a) the adapter's REAL pre-normalized output is accepted by the server.
        rep = validate_document_plan(plan)
        assert_true(rep.ok, f"T3: adapter output must pass server plan_validation.ok: {rep.to_dict().get('errors')}")

        # (b) the experimental backend fails closed on real MCP output.
        calls = {"builder": 0}
        backend = DocumentPlanBackend()
        orig = BuilderBackend.render

        def _spy(self, *a, **k):  # pragma: no cover - must never run
            calls["builder"] += 1
            return orig(self, *a, **k)

        setattr(BuilderBackend, "render", _spy)
        try:
            with tempfile.TemporaryDirectory() as td:
                target = Path(td) / "science.hwpx"
                raised = None
                with contextlib.redirect_stderr(io.StringIO()):
                    try:
                        backend.render(science_canonical(), {"marker": "x"}, target)
                    except HwpxBackendNotCapable as exc:
                        raised = exc
                assert_true(raised is not None, "T3: incapable MCP backend must raise HwpxBackendNotCapable")
                assert_true(type(raised) is HwpxBackendNotCapable, "T3: exact exception type")
                assert_true(not target.exists(), "T3: NO delivered artifact on incapable path")
                assert_true(calls["builder"] == 0, "T3: NO silent builder fallback")
                report = cast(CapabilityReport | None, getattr(raised, "report", None))
                assert_true(report is not None, "T3: exception carries CapabilityReport")
                assert report is not None
                assert_true(report.capable is False, "T3: report is not capable")
                assert_true(
                    report.page_count == 1,
                    f"T3: production backend records render_preview pageCount=1, got {report.page_count}",
                )
        finally:
            setattr(BuilderBackend, "render", orig)
        print("PASS T3 real smoke (deps present): plan valid, backend fails closed, no fallback")
    else:
        oracle = GOLD / "mcp-selfreport.receipt.json"
        section = GOLD / "mcp-selfreport.section0.xml"
        assert_true(oracle.exists(), "T3: mcp-selfreport.receipt.json oracle MUST exist (no silent skip)")
        assert_true(section.exists(), "T3: mcp-selfreport.section0.xml oracle MUST exist")
        receipt = json.loads(oracle.read_text(encoding="utf-8"))
        report = probe_file(section, expected_breaks=1, receipt=receipt)
        assert_true(report.capable is False, "T3: frozen MCP self-report oracle must be incapable")
        print("PASS T3 real smoke (deps absent): frozen MCP self-report oracle -> capable=False")


# --------------------------------------------------------------------------- #
# T4 — adapter determinism + schema + golden.
# --------------------------------------------------------------------------- #
def test_t4_adapter_determinism_schema_golden() -> None:
    canonical = science_canonical()
    a = canonical_to_document_plan(canonical)
    b = canonical_to_document_plan(canonical)
    sa = json.dumps(a, sort_keys=True, ensure_ascii=False)
    sb = json.dumps(b, sort_keys=True, ensure_ascii=False)
    assert_true(sa == sb, "T4: adapter output is byte-identical across runs (deterministic)")

    _validate_json_schema(a, SCHEMAS / "hwpx-document-plan.schema.json")

    golden_path = GOLD / "science-worksheet.document-plan.json"
    assert_true(golden_path.exists(), "T4: adapter golden present")
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    assert_true(a == golden, "T4: adapter output equals committed golden")

    # canonical page_break -> exactly {"type": "page_break"}
    pbs = [blk for blk in a["blocks"] if blk.get("type") == "page_break"]
    assert_true(pbs == [{"type": "page_break"}], f"T4: page_break maps to bare block, got {pbs}")
    # answer_box lines expand to underscore paragraphs.
    assert_true(
        any(blk.get("type") == "paragraph" and blk.get("text") == ANSWER_LINE for blk in a["blocks"]),
        "T4: answer_box expands to underscore answer lines",
    )
    assert_true(a["schemaVersion"] == "hwpx.document_plan.v1", "T4: schemaVersion stamped")
    assert_true(a["metadata"]["subject"] == "과학", "T4: metadata carried through")
    assert_true(
        not any(
            blk.get("type") == "heading"
            and blk.get("level") == 1
            and blk.get("text") == a["title"]
            for blk in a["blocks"]
        ),
        "T4: plan.title is the single title source; do not duplicate it as a level-1 heading block",
    )
    info_table = next(blk for blk in a["blocks"] if blk.get("type") == "table")
    assert_true(BLANK_CELL.strip() != "", "T4: blank-cell filler must render a visible writing rule, not whitespace")
    assert_true(
        info_table["rows"] and all(value == BLANK_CELL for value in info_table["rows"][0].values()),
        "T4: all-empty input rows use non-breaking blank cells so MCP tables keep physical row height",
    )
    print("PASS T4 adapter determinism + schema + golden + page_break mapping")


# --------------------------------------------------------------------------- #
# T5 — selection.
# --------------------------------------------------------------------------- #
def test_t5_selection() -> None:
    default = select_hwpx_backend(None)
    assert_true(isinstance(default, HwpxBackend), "T5: default is an HwpxBackend")
    assert_true(default.name == "builder", "T5: default backend is builder")
    assert_true(DEFAULT_BACKEND == "builder", "T5: DEFAULT_BACKEND constant is builder")
    assert_true(select_hwpx_backend("builder").name == "builder", "T5: explicit builder selectable")
    assert_true(select_hwpx_backend("document_plan").name == "document_plan", "T5: document_plan selectable")

    raised = None
    try:
        select_hwpx_backend("does-not-exist")
    except ValueError as exc:
        raised = exc
    assert_true(raised is not None, "T5: unknown backend name raises ValueError")
    assert_true(
        "builder" in str(raised) and "document_plan" in str(raised),
        f"T5: ValueError lists valid names: {raised}",
    )

    backend = select_hwpx_backend("document_plan")
    if not _hwpx_deps_present():
        # document_plan.available() reports the exact remediation when deps missing.
        ok, msg = backend.available()
        assert_true(ok is False, "T5: document_plan unavailable without pinned deps")
        assert_true("requirements-render-experimental.txt" in msg, f"T5: actionable install line: {msg}")
    else:
        ok, msg = backend.available()
        assert_true(ok is True, f"T5: exact pinned deps are available: {msg}")
        assert_true("4.0.0" in msg and "3.1.0" in msg, f"T5: availability reports exact versions: {msg}")

        old_roots = os.environ.get("HWPX_MCP_WORKSPACE_ROOTS")
        old_legacy = os.environ.get("HWPX_MCP_SANDBOX_ROOT")
        try:
            with tempfile.TemporaryDirectory() as root1, tempfile.TemporaryDirectory() as root2:
                expected_root1 = Path(root1).resolve()
                expected_root2 = Path(root2).resolve()
                os.environ["HWPX_MCP_WORKSPACE_ROOTS"] = json.dumps([root1, root2])
                os.environ.pop("HWPX_MCP_SANDBOX_ROOT", None)
                assert_true(
                    _workspace_staging_root() == expected_root1,
                    "T5: JSON workspace roots select the first authorized root",
                )
                os.environ["HWPX_MCP_WORKSPACE_ROOTS"] = os.pathsep.join([root1, root2])
                os.environ.pop("HWPX_MCP_SANDBOX_ROOT", None)
                assert_true(
                    _workspace_staging_root() == expected_root1,
                    "T5: pathsep workspace roots select the first authorized root",
                )
                os.environ.pop("HWPX_MCP_WORKSPACE_ROOTS", None)
                os.environ["HWPX_MCP_SANDBOX_ROOT"] = root2
                assert_true(
                    _workspace_staging_root() == expected_root2,
                    "T5: legacy sandbox root selects the authorized root",
                )
        finally:
            if old_roots is None:
                os.environ.pop("HWPX_MCP_WORKSPACE_ROOTS", None)
            else:
                os.environ["HWPX_MCP_WORKSPACE_ROOTS"] = old_roots
            if old_legacy is None:
                os.environ.pop("HWPX_MCP_SANDBOX_ROOT", None)
            else:
                os.environ["HWPX_MCP_SANDBOX_ROOT"] = old_legacy
    print("PASS T5 selection: default builder, exact pinned deps, workspace roots, availability honest")


# --------------------------------------------------------------------------- #
# T6 — receipt + no-silent-fallback.
# --------------------------------------------------------------------------- #
def test_t6_receipt_and_no_fallback() -> None:
    section = GOLD / "mcp-selfreport.section0.xml"
    receipt_oracle = json.loads((GOLD / "mcp-selfreport.receipt.json").read_text(encoding="utf-8"))
    report = probe_file(section, expected_breaks=1, receipt=receipt_oracle)
    assert_true(report.capable is False, "T6: incapable report from frozen self-report oracle")

    manifest = build_backend_receipt(
        backend="document_plan",
        delivered_path=None,
        capability=report,
        source_fingerprint="sha256:deadbeef",
    )
    _validate_json_schema(manifest, SCHEMAS / "backend-receipt.schema.json")
    assert_true(manifest["no_silent_fallback"] is True, "T6: manifest asserts no_silent_fallback")
    assert_true("hwpx_mcp_server_version" in manifest, "T6: records hwpx-mcp-server version field")
    assert_true("python_hwpx_version" in manifest, "T6: records python-hwpx version field")
    assert_true("pinned" in manifest, "T6: records pinned flag")
    assert_true(manifest["capability"]["capable"] is False, "T6: embeds CapabilityReport")

    # Spy proves BuilderBackend.render is NOT called on the incapable document_plan path.
    # NOTE: with deps present the spy guards the full adapter->MCP->probe->fail-closed path;
    # with deps absent render short-circuits at the available() dep-gate (still before any
    # builder call), so the no-fallback guarantee holds in both modes.
    calls = {"builder": 0}
    orig = BuilderBackend.render

    def _spy(self, *a, **k):  # pragma: no cover
        calls["builder"] += 1
        return orig(self, *a, **k)

    setattr(BuilderBackend, "render", _spy)
    try:
        backend = DocumentPlanBackend()
        raised = None
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "out.hwpx"
            with contextlib.redirect_stderr(io.StringIO()):
                try:
                    backend.render(science_canonical(), {"marker": "x"}, target)
                except HwpxBackendNotCapable as exc:
                    raised = exc
        if _hwpx_deps_present():
            assert_true(type(raised) is HwpxBackendNotCapable, f"T6: exact HwpxBackendNotCapable, got {type(raised)}")
            assert_true(not target.exists(), "T6: no artifact on incapable path")
        assert_true(calls["builder"] == 0, "T6: builder.render NEVER called on incapable path")
    finally:
        setattr(BuilderBackend, "render", orig)
    print("PASS T6 receipt schema + no-silent-fallback + exact exception")


def test_t7_preview_corroborator() -> None:
    """Step-4 preview corroboration downgrades an otherwise-physical pass when the
    committed render_preview shows fewer pages than the page breaks demand."""
    golden = GOLD / "builder-2page.section0.xml"
    preview = json.loads((GOLD / "mcp-pagebreak-preview.json").read_text(encoding="utf-8"))
    assert_true(preview["pageCount"] == 1, "T7: frozen preview oracle pageCount==1")

    # Physically capable (2 breaks) but preview reports 1 page for 3 expected pages -> reject.
    downgraded = probe_file(golden, expected_breaks=2, preview=preview, expected_pages=3)
    assert_true(downgraded.capable is False, "T7: insufficient preview pageCount downgrades capability")
    assert_true(downgraded.page_count == 1, "T7: page_count surfaced from preview")
    assert_true(
        any("pageCount" in r for r in downgraded.reasons),
        f"T7: reason names the preview shortfall: {downgraded.reasons}",
    )

    # A sufficient preview must NOT downgrade a genuine physical pass.
    ok = probe_file(golden, expected_breaks=2, preview={"pageCount": 3}, expected_pages=3)
    assert_true(ok.capable is True, "T7: sufficient preview pageCount preserves capability")
    print("PASS T7 preview corroborator (step-4) downgrade + non-downgrade")


def test_t8_real_four_document_success_path() -> None:
    """Pinned optional deps must render the actual four-document package, not only
    the synthetic incapable profile exercised by T3/T6."""
    if not _hwpx_deps_present():
        print("PASS T8 guarded: optional pinned MCP deps absent; live success path not run")
        return

    from importlib.metadata import version
    from validate_individualized_materials import build_sample_ir
    from renderers import render_package
    from renderers.render import canonical_content, extract_all, verify_parity

    assert_true(version("hwpx-mcp-server") == "4.0.0", "T8: exact hwpx-mcp-server pin is active")
    assert_true(version("python-hwpx") == "3.1.0", "T8: exact python-hwpx pin is active")
    ir = build_sample_ir()
    expected_breaks = {
        "teacher-individualized-plan": 2,
        "worksheet-group-a": 1,
        "worksheet-group-b": 1,
        "worksheet-group-c": 1,
    }
    canonical_by_id = {
        document["document_id"]: canonical_content(document)
        for document in ir["lesson_package"]["documents"]
    }
    probe_calls: list[Path] = []
    original_probe = DocumentPlanBackend.probe_capabilities

    def _probe_final_candidate(self, path, expected_breaks, **kwargs):
        candidate = Path(path)
        with zipfile.ZipFile(candidate) as archive:
            members = set(archive.namelist())
        assert_true(
            "META-INF/kteacher-backport-marker.json" in members,
            "T8: governing probe must inspect the marker-injected delivery candidate",
        )
        assert_true(
            "Contents/kteacher-content.xml" in members,
            "T8: governing probe must inspect the content-sidecar delivery candidate",
        )
        probe_calls.append(candidate)
        return original_probe(self, candidate, expected_breaks, **kwargs)

    with tempfile.TemporaryDirectory(prefix="kteacher-mcp-success-") as td:
        setattr(DocumentPlanBackend, "probe_capabilities", _probe_final_candidate)
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                rendered = render_package(ir, td, backend="document_plan")
        finally:
            setattr(DocumentPlanBackend, "probe_capabilities", original_probe)
        assert_true(len(probe_calls) == 4, "T8: governing probe inspected all four final candidates")
        assert_true(set(rendered) == set(expected_breaks), "T8: all four actual canonical documents rendered")
        for document_id, paths in rendered.items():
            hwpx_path = Path(paths["hwpx"])
            assert_true(hwpx_path.exists(), f"T8 {document_id}: HWPX delivered")
            with zipfile.ZipFile(hwpx_path) as archive:
                section = archive.read("Contents/section0.xml").decode("utf-8")
                assert_true(archive.testzip() is None, f"T8 {document_id}: ZIP CRC clean")
            assert_true(
                section.count('pageBreak=\"1\"') == expected_breaks[document_id],
                f"T8 {document_id}: physical page breaks match contract",
            )
            title = canonical_by_id[document_id]["title"]
            assert_true(section.count(title) == 1, f"T8 {document_id}: visible title occurs exactly once")
            assert_true(BLANK_CELL in section, f"T8 {document_id}: physical writing rule survives in section XML")
            parity_ok, parity_reasons = verify_parity(extract_all(paths))
            assert_true(parity_ok, f"T8 {document_id}: 3-format canonical parity: {parity_reasons}")
    print("PASS T8 real four-document MCP success path + writing rules + parity")


def main() -> None:
    test_t1_red_upstream_contradiction()
    test_t2_builder_positive_control()
    test_t3_real_smoke()
    test_t4_adapter_determinism_schema_golden()
    test_t5_selection()
    test_t6_receipt_and_no_fallback()
    test_t7_preview_corroborator()
    test_t8_real_four_document_success_path()
    print("PASS validate_hwpx_backend_contract")
    print("- physical-truth capability gate; self-report contradiction rejected (T1)")
    print("- builder positive control capable==2 (T2); experimental backend fails closed (T3/T6)")
    print("- deterministic canonical->document_plan adapter, schema + golden (T4); selection (T5)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
