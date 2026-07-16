#!/usr/bin/env python3
"""VS2 focused validator: schoolinfo evaluation-plan adapter + PII mask-or-block.

Offline: the MCP transport is injected. Uses SYNTHETIC plan fixtures only (no real
PII, no real school data). The real remote fetch is exercised in the E2E artifact.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.school_evaluation import pii  # noqa: E402
from providers.school_evaluation.adapter import (  # noqa: E402
    SchoolEvaluationAdapter,
    structure_plan,
    MIN_USEFUL_MD,
    MAX_ALL_DOCS,
    MAX_DOWNLOAD_BYTES,
)
from providers.school_evaluation.mcp_client import SchoolMcpClient  # noqa: E402

FIX = ROOT / "tests" / "golden" / "school-evaluation"
MASKABLE = (FIX / "plan-maskable.md").read_text(encoding="utf-8")
BLOCKED = (FIX / "plan-blocked.md").read_text(encoding="utf-8")


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def fake_transport(responses: dict):
    """Return a transport(url, payload, timeout) that answers by method/tool name."""

    def transport(url, payload, timeout):
        method = payload["method"]
        if method == "tools/list":
            return {"result": {"tools": [{"name": "find_school"}, {"name": "get_evaluation_plan"}]}, "id": payload["id"]}
        if method == "tools/call":
            tool = payload["params"]["name"]
            args = payload["params"]["arguments"]
            text = responses.get(tool)
            if callable(text):
                text = text(args)
            if text is None:
                return {"result": {"content": [{"type": "text", "text": ""}]}, "id": payload["id"]}
            return {"result": {"content": [{"type": "text", "text": text}]}, "id": payload["id"]}
        return {"result": {}, "id": payload["id"]}

    return transport


def test_pii_mask_or_block() -> None:
    ok = pii.mask_or_block_plan(MASKABLE)
    assert_true(not ok.blocked, "maskable plan must not block")
    assert_true("[MASKED:phone]" in ok.masked_text and "[MASKED:email]" in ok.masked_text, "contact PII masked")
    assert_true("[MASKED:person_name]" in ok.masked_text and "김합성" not in ok.masked_text, "labeled teacher name masked")
    assert_true("10203" not in ok.masked_text, "student number masked")

    # C1: the audit trail must record categories without echoing the PII it removed.
    audit_blob = json.dumps(ok.findings, ensure_ascii=False)
    for raw_pii in ("010-1234-5678", "teacher@example.com", "10203", "김합성"):
        assert_true(raw_pii not in audit_blob, f"audit findings must not re-leak {raw_pii}")
    assert_true(all(f.get("text", "").startswith("[REDACTED:") for f in ok.findings), "audit values are redacted markers")

    blk = pii.mask_or_block_plan(BLOCKED)
    assert_true(blk.blocked, "bare person-column names must block")
    assert_true(any("담당교사" in r for r in blk.block_reasons), "block reason cites person column")


def test_structure_pins_subject() -> None:
    rows = structure_plan(MASKABLE, subject="과학")
    assert_true(len(rows) == 2 and all(r["subject"] == "과학" for r in rows), "structuring pins to 과학")
    allrows = structure_plan(MASKABLE)
    subs = {r["subject"] for r in allrows}
    assert_true({"과학", "수학", "국어"} <= subs, "un-pinned structuring returns all subjects")


def test_adapter_ok_and_block() -> None:
    client = SchoolMcpClient(transport=fake_transport({"get_evaluation_plan": MASKABLE}))
    adp = SchoolEvaluationAdapter(remote=True, client=client)
    res = adp.get_evaluation_plan(sido="서울특별시", sgg="강남구", kind="중학교", name="합성중학교", year=2026, subject="과학")
    assert_true(res.status == "ok", f"maskable plan -> ok, got {res.status}")
    assert_true(res.structured and all(r["subject"] == "과학" for r in res.structured), "pinned science rows")
    blob = json.dumps(res.structured, ensure_ascii=False)
    assert_true("김합성" not in blob and "010-1234-5678" not in blob, "no PII in structured output")
    assert_true(res.anchor and res.anchor["content_sha256"] and res.anchor["retrieved_at"], "anchor has hash + retrieved_at")

    client_b = SchoolMcpClient(transport=fake_transport({"get_evaluation_plan": BLOCKED}))
    adp_b = SchoolEvaluationAdapter(remote=True, client=client_b)
    res_b = adp_b.get_evaluation_plan(sido="서울특별시", sgg="강남구", kind="중학교", name="합성중학교", year=2026, subject="과학")
    assert_true(res_b.status == "blocked_pii", f"unmaskable plan -> blocked_pii, got {res_b.status}")


def test_current_previous_fallback_requires_approval() -> None:
    # current year empty, previous year has the plan.
    def resp(args):
        return MASKABLE if args.get("year") == 2025 else ""

    client = SchoolMcpClient(transport=fake_transport({"get_evaluation_plan": resp}))
    adp = SchoolEvaluationAdapter(remote=True, client=client)

    # No approval -> NO auto fallback.
    no_appr = adp.get_evaluation_plan(sido="서울특별시", sgg="강남구", kind="중학교", name="합성중학교", year=2026, subject="과학")
    assert_true(no_appr.status == "error" and not no_appr.fallback_used, "no auto fallback without approval")

    # Explicit approval -> previous year used.
    appr = adp.get_evaluation_plan(sido="서울특별시", sgg="강남구", kind="중학교", name="합성중학교", year=2026, subject="과학", approve_previous=lambda c, p: True)
    assert_true(appr.status == "ok" and appr.fallback_used and appr.year == 2025, "approved fallback uses previous year")


def test_limits_and_remote_local_separation() -> None:
    # Short text -> needs OCR/manual.
    client = SchoolMcpClient(transport=fake_transport({"get_evaluation_plan": "짧음"}))
    adp = SchoolEvaluationAdapter(remote=True, client=client)
    short = adp.get_evaluation_plan(sido="s", sgg="g", kind="중학교", name="n", year=2026, subject="과학")
    assert_true(short.status in ("needs_ocr_or_manual", "error"), "short/empty -> ocr-manual or error")
    assert_true(MIN_USEFUL_MD == 200 and MAX_ALL_DOCS == 20 and MAX_DOWNLOAD_BYTES == 50 * 1024 * 1024, "limits ported")

    # Remote mode: local file tool disabled.
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(MASKABLE)
        path = fh.name
    remote_res = adp.parse_evaluation_file(path, subject="과학")
    assert_true(remote_res.status == "error" and "remote mode" in (remote_res.warning or ""), "remote mode disables local parse")

    # Local mode: local parse enabled and masked.
    local = SchoolEvaluationAdapter(remote=False, client=client)
    local_res = local.parse_evaluation_file(path, subject="과학")
    assert_true(local_res.status == "ok" and local_res.structured, "local mode parses file")
    assert_true("김합성" not in json.dumps(local_res.structured, ensure_ascii=False), "local parse masked too")


def test_h1_adorned_person_names() -> None:
    """H1: person-role columns fail-closed on ANY residual identity, not just bare names."""
    pad = "이 표는 합성 예시이며 실데이터가 아닙니다. 개인정보 컬럼 처리 검증을 위해 200자 이상을 채웁니다. " * 3
    adorned = (
        f"## 합성 평가 담당표\n\n{pad}\n\n"
        "| 과목 | 영역 | 담당교사 | 반영비율(%) |\n"
        "|------|------|---------|------------|\n"
        "| 과학 | 기권과 날씨 | 홍길동 선생님 | 30 |\n"
        "| 과학 | 힘과 운동 | 김철수 010-1234-5678 | 20 |\n"
        "| 과학 | 물질 | 압둘라만호 | 20 |\n"
        "| 과학 | 생명 | John Smith | 10 |\n"
    )
    r = pii.mask_or_block_plan(adorned)
    assert_true(r.blocked, "adorned person-column names must block (name+honorific, name+phone, 5-char)")
    blocked_findings = [f for f in r.findings if f.get("type") == "person_name_blocked"]
    assert_true(len(blocked_findings) >= 3, "pii_findings records each person-column block")
    for name in ("홍길동", "김철수", "압둘라만호", "John Smith"):
        assert_true(all(name not in f.get("text", "") for f in blocked_findings), f"audit findings must not re-leak {name}")
        assert_true(all(name not in reason for reason in r.block_reasons), f"block reasons must not re-leak {name}")
    assert_true(all(f.get("text") == "[REDACTED:person_identity]" for f in blocked_findings), "blocked identity audit uses a fixed non-reversible marker")
    assert_true("기권과 날씨" in r.masked_text and "반영비율" in r.masked_text, "non-person educational content preserved")

    # Full adapter: blocked_pii and NO raw name anywhere in the returned result (structured or audit).
    client = SchoolMcpClient(transport=fake_transport({"get_evaluation_plan": adorned}))
    adp = SchoolEvaluationAdapter(remote=True, client=client)
    res = adp.get_evaluation_plan(sido="s", sgg="g", kind="중학교", name="합성중", year=2026, subject="과학")
    assert_true(res.status == "blocked_pii", f"adapter must return blocked_pii, got {res.status}")
    blob = json.dumps(res.__dict__, ensure_ascii=False, default=str)
    for name in ("홍길동", "김철수", "압둘라만호", "John Smith"):
        assert_true(name not in blob, f"{name} must not appear anywhere in the adapter result")
    assert_true(res.structured is None, "no structured plan returned when blocked")
    assert_true(any(f.get("type") == "person_name_blocked" for f in (res.pii_findings or [])), "adapter pii_findings records the block")

    # A [MASKED] marker beside a name must NOT be treated as evidence the name was handled.
    single = "| 담당교사 |\n|--|\n| 김철수 [MASKED:phone] |\n" + ("설명 " * 60)
    assert_true(pii.mask_or_block_plan(single).blocked, "[MASKED] marker must not suppress the name block")
    # An empty/dash person cell (no identity) must NOT block.
    dash = "| 담당교사 |\n|--|\n| - |\n" + ("설명 " * 60)
    assert_true(not pii.mask_or_block_plan(dash).blocked, "empty/dash person cell must not over-block")


def main() -> None:
    test_pii_mask_or_block()
    test_structure_pins_subject()
    test_adapter_ok_and_block()
    test_h1_adorned_person_names()
    test_current_previous_fallback_requires_approval()
    test_limits_and_remote_local_separation()
    print("PASS validate_school_evaluation")
    print("- PII: contact/student/labeled-name masked; bare person-column names BLOCK (fail-closed)")
    print("- adapter pins by school/year/subject; anchor has hash+retrieved_at; no PII in structured output")
    print("- current->previous fallback requires explicit approval (no auto)")
    print("- limits ported (20 docs / 50MB / MIN_USEFUL_MD 200); remote mode disables local file tool")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
