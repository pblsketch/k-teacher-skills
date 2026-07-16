#!/usr/bin/env python3
"""VS3 focused validator: school↔national alignment / promotion / quarantine.

Uses the synthetic national index; INV-1..5 enforced at the data-model level.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.curriculum.provider import CurriculumProvider  # noqa: E402
from providers.alignment import align_plan_codes_to_national, extract_codes  # noqa: E402

SYNTH = ROOT / "tests" / "golden" / "curriculum-provider" / "normalized-synthetic.jsonl"


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_extract_codes() -> None:
    rows = [{"subject": "과학", "cells": ["과학", "기권과 날씨", "[9과99-01] 관찰", "30"]}]
    codes = extract_codes(rows)
    assert_true(codes == ["[9과99-01]"], f"extract codes from rows: {codes}")
    text = "성취기준 [9과99-01], [4과03-01] 참고"
    assert_true(set(extract_codes(text)) == {"[9과99-01]", "[4과03-01]"}, "extract from text")


def test_alignment_and_separation() -> None:
    nat = CurriculumProvider(SYNTH)

    # Matching code -> aligned pair with two coexisting, authority-separated records.
    res = align_plan_codes_to_national(["[9과99-01]", "[9과00-99]"], nat, school_level="중학교", subject="과학")
    assert_true(len(res.aligned) == 1 and len(res.quarantined) == 1, "one aligned, one quarantined")

    pair = res.aligned[0]
    # INV-1: school stays curriculum-context; national is a SEPARATE curriculum-record.
    assert_true(pair.school_context["record_scope"] == "curriculum-context", "INV-1 school stays context")
    assert_true(pair.school_context["provider"]["provider_kind"] == "school-evaluation-plan-provider", "school provider kind")
    assert_true(pair.national_record["record_scope"] == "curriculum-record", "national is curriculum-record")
    assert_true(pair.national_record["provider"]["provider_kind"] == "curriculum-provider", "national provider kind")
    # Two coexisting records emitted (additive), never one mutated.
    coex = res.coexisting_records()
    scopes = sorted(r["record_scope"] for r in coex)
    assert_true(scopes == ["curriculum-context", "curriculum-record"], "two coexisting records per pair")

    # INV-2/INV-4: fail-closed until national verified AND teacher approved.
    assert_true(pair.downstream_ready is False, "not downstream-ready without teacher approval + verified national")
    approved = align_plan_codes_to_national(["[9과99-01]"], nat, school_level="중학교", subject="과학", teacher_approved=True)
    # national synthetic record is provenance-unverified -> still fail-closed even with approval.
    assert_true(approved.aligned[0].downstream_ready is False, "fail-closed: unverified national blocks even with approval")

    # INV-3: not_found -> quarantined + teacher_confirm.
    q = res.quarantined[0]
    assert_true(q.code == "[9과00-99]" and q.teacher_confirm is True, "mismatch quarantined w/ teacher_confirm")


def test_national_quarantined_propagates() -> None:
    nat = CurriculumProvider(SYNTH)
    # [6과88-02] is a mixed-revision quarantined national record; alignment must quarantine it.
    res = align_plan_codes_to_national(["[6과88-02]"], nat, school_level="초등학교", subject="과학", revision="unverified")
    assert_true(len(res.aligned) == 0 and len(res.quarantined) == 1, "quarantined national -> alignment quarantine")
    assert_true("quarantin" in res.quarantined[0].reason, "reason cites quarantine")


def main() -> None:
    test_extract_codes()
    test_alignment_and_separation()
    test_national_quarantined_propagates()
    print("PASS validate_alignment")
    print("- alignment emits a separate national curriculum-record; school stays curriculum-context (INV-1)")
    print("- matched code fail-closed until national verified + teacher approved (INV-2/INV-4)")
    print("- mismatch/ambiguity/quarantined-national -> quarantined + teacher_confirm (INV-3)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
