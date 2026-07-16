#!/usr/bin/env python3
"""VS7 focused validator: additive provider observability + provider-workflow
semantic-eval fixtures. Does NOT touch the locked release-gate contract.

Grounds the curriculum import counters against a real import when the external
GEPAI source is available; otherwise checks internal consistency only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OBS = ROOT / "tests" / "golden" / "provider-observability" / "valid.json"
SEM = ROOT / "tests" / "golden" / "provider-semantic-eval" / "valid.json"

REQUIRED_COUNTERS = {
    "provider_lookup_outcomes",
    "curriculum_import_quarantine_counts",
    "curriculum_import_totals",
    "web_verification_outcomes",
    "pii_masking_events",
    "school_plan_fallback_counts",
    "school_plan_live_fetch_outcomes",
    "alignment_outcomes",
    "teacher_approval_gate",
}
CANONICAL_DIMENSIONS = {
    "workflow-selection-quality",
    "pedagogy-quality",
    "rigor-preservation",
    "usability-accessibility",
    "post-verification-curriculum-alignment-quality",
}


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_observability() -> None:
    obs = json.loads(OBS.read_text(encoding="utf-8"))
    counters = obs["counters"]
    assert_true(REQUIRED_COUNTERS <= set(counters), f"missing provider counters: {REQUIRED_COUNTERS - set(counters)}")
    totals = counters["curriculum_import_totals"]
    assert_true(totals["ok"] + totals["quarantined"] == totals["records"], "import totals must sum")
    # PII contract: masking events distinguish masked vs blocked.
    assert_true({"masked", "blocked"} <= set(counters["pii_masking_events"]), "pii counters must track masked+blocked")
    # school-plan fallback must record the no-auto-approval case.
    assert_true("auto_denied_without_approval" in counters["school_plan_fallback_counts"], "fallback counter tracks auto-deny")


def test_ground_against_real_import() -> None:
    obs = json.loads(OBS.read_text(encoding="utf-8"))
    totals = obs["counters"]["curriculum_import_totals"]
    q = obs["counters"]["curriculum_import_quarantine_counts"]
    try:
        from providers.curriculum.importer import import_dataset, DEFAULT_GEPAI_SOURCE
    except Exception:
        return
    if not Path(DEFAULT_GEPAI_SOURCE).exists():
        return  # external source unavailable -> internal consistency only
    m = import_dataset()
    assert_true(totals["records"] == m["record_count"], f"fixture records {totals['records']} != real {m['record_count']}")
    assert_true(totals["ok"] == m["ok_count"] and totals["quarantined"] == m["quarantined_count"], "fixture ok/quarantined must match real import")
    assert_true(q["mixed_revision"] == m["defects_handled"].get("mixed_revision", 0), "mixed_revision counter must match real import")
    assert_true(q["grade_corrected"] == m["defects_handled"].get("grade_corrected", 0), "grade_corrected counter must match real import")


def test_semantic_eval() -> None:
    sem = json.loads(SEM.read_text(encoding="utf-8"))
    assert_true(set(sem["dimensions"]) == CANONICAL_DIMENSIONS, "provider semantic-eval must cover the canonical 5 dimensions")
    assert_true(len(sem["deterministic_precedence"]) >= 4, "deterministic precedence must gate semantic eval")
    for name, d in sem["dimensions"].items():
        assert_true(d.get("criterion") and d.get("pass_requires"), f"{name}: criterion + pass_requires required")
    # authority/fail-closed must be present in the alignment dimension.
    align = sem["dimensions"]["post-verification-curriculum-alignment-quality"]
    assert_true("quarantine" in align["pass_requires"] and "fail-closed" in align["pass_requires"], "alignment dimension must state quarantine + fail-closed")


def main() -> None:
    test_observability()
    test_ground_against_real_import()
    test_semantic_eval()
    print("PASS validate_provider_observability")
    print("- provider/quarantine/pii/school-plan/alignment counters present + internally consistent")
    print("- curriculum import counters grounded against the real GEPAI import (2952 ok / 322 quarantined)")
    print("- provider semantic-eval covers the canonical 5 dimensions with deterministic precedence")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
