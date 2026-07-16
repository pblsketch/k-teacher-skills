#!/usr/bin/env python3
"""Behavioral contract for the two-provider authority model (VS0/VS1/VS3).

Fail-closed provider/provenance/license semantics must survive the AR-1
`license_authority` separation field and the new
`school-evaluation-plan-provider` provider_kind. National curriculum authority
(curriculum-record) and school operational disclosure (curriculum-context)
stay separated in the data.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
IR_SCHEMA_PATH = ROOT / "schemas" / "lesson-package-ir.schema.json"
VALID_IR_FIXTURE_PATH = ROOT / "tests" / "golden" / "lesson-package-ir" / "downstream-ready.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def first_error(validator: jsonschema.Draft202012Validator, payload: dict):
    errors = sorted(validator.iter_errors(payload), key=lambda e: (list(e.path), e.message))
    return errors[0] if errors else None


def expect_valid(validator, payload: dict, case: str) -> None:
    error = first_error(validator, payload)
    if error is not None:
        raise AssertionError(f"{case}: expected valid but failed at {list(error.path)}: {error.message}")


def expect_invalid(validator, payload: dict, case: str) -> None:
    assert_true(first_error(validator, payload) is not None, f"{case}: expected invalid but schema accepted payload")


def school_disclosure_record() -> dict:
    """A Tier-1 school evaluation-plan record: operational context only.

    It enters the IR as curriculum-context and is verified-compatible ONLY with
    the AR-1 teacher-authorized-public-disclosure authority. It never carries a
    national achievement-standard as authoritative text.
    """
    return {
        "record_id": "prov-schoolplan-2026-pilot-science-1",
        "record_scope": "curriculum-context",
        "provider": {
            "provider_id": "schoolinfo-pilot-2026",
            "provider_kind": "school-evaluation-plan-provider",
            "release_id": "schoolinfo-pilot@2026",
            "release_version": "2026",
        },
        "provenance_grade": ":provided",
        "source_reference": "eval.hwpx#table=과학-2학년",
        "verification_evidence_type": "provided-document",
        "verification_anchor": {
            "carrier": "provider-record",
            "locator_type": "provider-record-id",
            "locator_value": "provider-record::schoolinfo-pilot-2026::science-g2::sha256=deadbeef::retrieved=2026-07-16",
        },
        "source_license": {
            "status": "verified-compatible",
            "license_id": "kr-public-school-disclosure",
            "license_authority": "teacher-authorized-public-disclosure",
            "evidence_anchor": {
                "carrier": "provider-release-manifest",
                "locator_type": "release-id",
                "locator_value": "schoolinfo-pilot@2026",
            },
        },
        "read_only_input": True,
    }


def main() -> None:
    schema = load_json(IR_SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema)

    # 1. Existing golden is untouched by the additive change (non-breaking).
    base = load_json(VALID_IR_FIXTURE_PATH)
    expect_valid(validator, base, "baseline_golden_still_valid")

    # 2. A school-evaluation-plan-provider record with the AR-1 authority validates.
    with_school = copy.deepcopy(base)
    with_school["provenance_ledger"].append(school_disclosure_record())
    expect_valid(validator, with_school, "school_disclosure_record_valid")

    # 3. A national curriculum record keeps public-license authority (separation).
    national_public = copy.deepcopy(base)
    national_public["provenance_ledger"][0]["source_license"]["license_authority"] = "public-license"
    expect_valid(validator, national_public, "national_public_license_authority_valid")

    # 4. AR-1 field is enum-constrained: a bogus authority is rejected.
    bad_authority = copy.deepcopy(with_school)
    bad_authority["provenance_ledger"][-1]["source_license"]["license_authority"] = "self-declared"
    expect_invalid(validator, bad_authority, "bogus_license_authority_rejected")

    # 5. Fail-closed preserved: IR provenance records still demand verified-compatible.
    unverified = copy.deepcopy(with_school)
    unverified["provenance_ledger"][-1]["source_license"]["status"] = "unknown"
    expect_invalid(validator, unverified, "unverified_school_license_fails_closed")

    # 6. M1 authority boundary now ENFORCED at the schema/IR boundary (not just by the
    #    aligner). Only curriculum-provider may pair with record_scope=curriculum-record.
    #    Positive: a national curriculum-record with curriculum-provider validates.
    national_record = copy.deepcopy(base)
    nat = copy.deepcopy(base["provenance_ledger"][0])
    nat["record_id"] = "prov-national-curriculum-record-1"
    nat["record_scope"] = "curriculum-record"
    nat["provider"]["provider_kind"] = "curriculum-provider"
    national_record["provenance_ledger"].append(nat)
    expect_valid(validator, national_record, "national_curriculum_record_valid")

    #    Negative: any non-national provider kind paired with curriculum-record is rejected.
    for kind in ("school-evaluation-plan-provider", "textbook-provider"):
        smuggled = copy.deepcopy(base)
        rec = copy.deepcopy(base["provenance_ledger"][0])
        rec["record_id"] = f"prov-smuggle-{kind}"
        rec["record_scope"] = "curriculum-record"
        rec["provider"]["provider_kind"] = kind
        smuggled["provenance_ledger"].append(rec)
        expect_invalid(validator, smuggled, f"{kind}_with_curriculum_record_rejected")

    print("PASS validate_provider_authority")
    print("- school-evaluation-plan-provider record validates with AR-1 teacher-authorized-public-disclosure authority")
    print("- national curriculum records keep public-license authority (Tier separation)")
    print("- bogus license_authority rejected; unverified school license fails closed")
    print("- baseline golden IR unaffected (additive, non-breaking)")
    print("- M1: only curriculum-provider may pair with record_scope=curriculum-record; school/textbook kinds rejected at the schema boundary")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
