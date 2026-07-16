#!/usr/bin/env python3
"""VS1 focused validator: national curriculum provider normalization + fail-closed
read-only lookup + offline `:web` verification overlay.

Uses SYNTHETIC data only (no real GEPAI rows committed). The real GEPAI import runs
against the external non-distributed source in the E2E artifact, not in this test.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.curriculum.importer import normalize_record  # noqa: E402
from providers.curriculum.provider import CurriculumProvider  # noqa: E402
from providers.curriculum import web_verify  # noqa: E402

SYNTH_INDEX = ROOT / "tests" / "golden" / "curriculum-provider" / "normalized-synthetic.jsonl"


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_normalization() -> None:
    # Bracket normalization (audit 5.3) + keywords_absent (5.5).
    rec = normalize_record({"code": "9과99-01", "subject": "과학", "school_level": "중학교", "grade_level": "1~3학년", "curriculum": "2022", "content": "x", "keywords": []})
    assert_true(rec["canonical_code"] == "[9과99-01]", "canonical bracket normalization")
    assert_true("bracket_normalized" in rec["quality_flags"], "bracket flag set")
    assert_true(rec["raw_code"] == "9과99-01", "raw code preserved")
    assert_true("keywords_absent" in rec["quality_flags"], "empty keyword flag")
    assert_true(rec["subject_code"] == "과", "subject code extracted")
    assert_true(rec["source"]["license_status"] == "unverified" and rec["source"]["verified"] is False, "fail-closed provenance default")
    assert_true(rec["status"] == "ok", "well-formed record ok")

    # Grade typo fix (audit 5.4): only the three 3~4 science codes.
    for gl in ("3~5", "3~6", "3~7"):
        r = normalize_record({"code": "[4과03-01]", "subject": "과학", "school_level": "초등학교", "grade_level": gl, "curriculum": "2022", "content": "x", "keywords": []})
        assert_true(r["grade_band"] == "3~4" and "grade_corrected" in r["quality_flags"], f"grade typo {gl}->3~4")

    # Mixed revision (audit 5.1): elementary 5~6 no-bracket -> quarantine, revision downgraded.
    mixed = normalize_record({"code": "6과88-02", "subject": "과학", "school_level": "초등학교", "grade_level": "5~6", "curriculum": "2022", "content": "x", "keywords": []}, mixed_revision_codes={"6과88-02"})
    assert_true(mixed["status"] == "quarantined" and mixed["quarantine_reason"] == "mixed_revision_suspected", "mixed revision quarantined")
    assert_true(mixed["curriculum_revision"] == "unverified", "mixed revision downgraded")


def test_provider_fail_closed() -> None:
    provider = CurriculumProvider(SYNTH_INDEX)

    # ok lookup is downstream-eligible by status, but verify() still fail-closed w/o provenance.
    ok = provider.lookup_standard_by_code("[9과99-01]")
    assert_true(ok.status == "ok" and ok.record is not None, "ok lookup returns record")

    # quarantined record is not resolved (and never downstream-ready).
    q = provider.lookup_standard_by_code("[6과88-02]")
    assert_true(q.status == "quarantined" and not q.is_resolved, "quarantined not resolved")

    # not found on unknown code.
    nf = provider.lookup_standard_by_code("[9과00-99]")
    assert_true(nf.status == "not_found", "unknown code not found")

    # search uses content substring (keywords[] empty in source).
    s = provider.search_standards(school_level="중학교", subject="과학", keyword="현상")
    assert_true(len(s["candidates"]) == 1 and s["candidates"][0]["canonical_code"] == "[9과99-01]", "keyword search by content")

    # list excludes quarantined.
    lst = provider.list_standards(school_level="초등학교", subject="과학")
    codes = {c["canonical_code"] for c in lst["records"]}
    assert_true("[4과03-01]" in codes and "[6과88-02]" not in codes, "list excludes quarantined")

    # verify_standard is fail-closed until provenance+license verified.
    v = provider.verify_standard("[9과99-01]")
    assert_true(v["downstream_ready"] is False and "fail-closed" in (v["reason"] or ""), "verify fail-closed by default")

    # L1: lookup resolution and verify authority cannot DISAGREE on downstream-readiness.
    # LookupResult exposes only is_resolved (a resolution signal), never a downstream_ready
    # property, so no consumer can gate on the wrong (looser) property.
    assert_true(not hasattr(ok, "downstream_ready"), "LookupResult must not expose a downstream_ready trap")
    assert_true(ok.is_resolved is True, "structurally-ok record is resolved")
    # The sole downstream-readiness authority (verify_standard) says False for the same
    # unverified record -> resolution True while downstream-readiness False, and there is
    # no lookup-level 'downstream_ready' that could contradict it.
    assert_true(provider.verify_standard("[9과99-01]")["downstream_ready"] is False, "same record: verify authority is fail-closed")
    assert_true(not q.is_resolved and provider.verify_standard("[6과88-02]")["downstream_ready"] is False, "quarantined: neither resolved nor downstream-ready")


def test_web_overlay_offline() -> None:
    provider = CurriculumProvider(SYNTH_INDEX)
    rec = provider.lookup_standard_by_code("[9과99-01]").record
    assert_true(rec is not None, "synthetic web-overlay record must resolve")

    # Official source + substantive content match -> content_verified (NOT license).
    def fetch_content(url: str) -> str:
        return "공식 고시 문서 ... 어떤 현상을 관찰하여 원리를 설명할 수 있다 ... 9과99-01 예시 성취기준"

    ov = web_verify.verify_via_web(rec["canonical_code"], rec["content"], "https://ncic.re.kr/mock", fetch=fetch_content)
    assert_true(ov["content_verified"] and ov["provenance_grade"] == ":web", "official + content match -> content_verified")
    assert_true(ov["source_anchor"]["locator_value"].startswith("https://ncic.re.kr/mock#retrieved="), "source anchor preserved")

    # content verified WITHOUT license evidence -> content provenance set, license stays fail-closed.
    content_only = web_verify.apply_web_overlay(rec, ov)
    assert_true(content_only["source"]["verified"] is True and content_only["source"]["verification_evidence_type"] == "web-verification", "content provenance recorded")
    assert_true(content_only["source"]["license_status"] == "unverified", "no license evidence -> license stays unverified (fail-closed)")
    assert_true("web_content_verified" in content_only["quality_flags"] and "web_license_confirmed" not in content_only["quality_flags"], "content verified but license NOT confirmed")

    # content verified + independently-supplied verified-compatible license -> license confirmed.
    license_ev = {"status": "verified-compatible", "license_id": "kr-public-curriculum-notice", "license_authority": "public-license"}
    full = web_verify.apply_web_overlay(rec, ov, license_evidence=license_ev)
    assert_true(full["source"]["license_status"] == "verified-compatible" and full["source"]["license_authority"] == "public-license", "valid license evidence -> verified-compatible")
    assert_true(full["source"].get("provenance_grade") == ":web", "web overlay must preserve :web provenance grade")
    with tempfile.TemporaryDirectory() as td:
        index = Path(td) / "index.jsonl"
        index.write_text(json.dumps(full, ensure_ascii=False) + "\n", encoding="utf-8")
        report = CurriculumProvider(index).verify_standard(rec["canonical_code"])
        assert_true(report["downstream_ready"] and report["provenance_grade"] == ":web", "verified web record reports :web, not :provided")

    # M2: index/code-only page (code hit, no content match) must NOT promote to :web.
    def fetch_code_only(url: str) -> str:
        return "성취기준 목록 인덱스 페이지: 9과99-01, 9과99-02, 9과99-03 (본문 없음)"

    code_only = web_verify.verify_via_web(rec["canonical_code"], rec["content"], "https://ncic.re.kr/list", fetch=fetch_code_only)
    assert_true(code_only["code_hit"] and not code_only["content_verified"], "code-string hit alone must NOT promote to :web")

    # M2: non-official source with content match must NOT verify (official anchoring required).
    nonofficial = web_verify.verify_via_web(rec["canonical_code"], rec["content"], "https://random-blog.example/post", fetch=fetch_content)
    assert_true(not nonofficial["content_verified"] and "official" in nonofficial["reason"], "non-official source must not verify")

    # M2: false/invalid license evidence must NOT become verified-compatible.
    false_lic = web_verify.apply_web_overlay(rec, ov, license_evidence={"status": "unknown"})
    assert_true(false_lic["source"]["license_status"] == "unverified", "false/invalid license evidence -> license stays unverified")

    # No content match -> fail-closed on content; unreachable -> honest failure.
    miss = web_verify.verify_via_web(rec["canonical_code"], rec["content"], "https://ncic.re.kr/mock", fetch=lambda u: "전혀 관련 없는 페이지 내용")
    assert_true(not miss["content_verified"] and miss["provenance_grade"] == ":inferred", "no content match stays fail-closed")
    assert_true(web_verify.apply_web_overlay(rec, miss)["source"]["license_status"] == "unverified", "no match keeps unverified")

    def fetch_raise(url: str) -> str:
        raise TimeoutError("network down")

    dead = web_verify.verify_via_web(rec["canonical_code"], rec["content"], "https://ncic.re.kr/mock", fetch=fetch_raise)
    assert_true(not dead["content_verified"] and "unreachable" in dead["reason"], "unreachable source -> honest fail")


def test_quarantine_exclusion_surfaces() -> None:  # RC5
    """A quarantined record is excluded at every read surface (list/search/verify)."""
    provider = CurriculumProvider(SYNTH_INDEX)
    qcode = "[6과88-02]"  # elementary 5~6 no-bracket -> mixed_revision quarantined

    # (a) absent from every page of list_standards; sum(pages) == ok_count.
    seen: set = set()
    total_ok = None
    page = 0
    while True:
        result = provider.list_standards(page=page, page_size=2)
        total_ok = result["total_ok"]
        for row in result["records"]:
            assert_true(row["status"] == "ok", "list_standards may only return ok rows")
            seen.add(row["canonical_code"])
        if not result["records"]:
            break
        page += 1
    assert_true(qcode not in seen, "quarantined code must be absent from list_standards")
    assert_true(len(seen) == total_ok, f"paged list must cover exactly total_ok rows ({len(seen)} != {total_ok})")

    # (b) neither the code nor its content keyword surfaces the quarantined record.
    assert_true(all(c["canonical_code"] != qcode for c in provider.search_standards(keyword=qcode)["candidates"]),
                "search by code must not surface the quarantined record")
    assert_true(all(c["canonical_code"] != qcode for c in provider.search_standards(keyword="비교")["candidates"]),
                "search by content keyword must not surface the quarantined record")

    # (c) verify_standard fail-closed on the quarantined code.
    report = provider.verify_standard(qcode)
    assert_true(report["downstream_ready"] is False and report["status"] == "quarantined",
                "verify_standard must be fail-closed + quarantined for a quarantined code")


def main() -> None:
    test_normalization()
    test_provider_fail_closed()
    test_web_overlay_offline()
    test_quarantine_exclusion_surfaces()
    print("PASS validate_curriculum_provider")
    print("- normalization repairs bracket/grade-typo/mixed-revision; provenance fail-closed by default")
    print("- read-only provider: ok/quarantined/not_found, content-substring search, quarantine excluded from list")
    print("- verify_standard fail-closed until provenance+license verified")
    print("- offline :web overlay verifies-or-fails-honestly and preserves source anchor")
    print("- quarantine excluded at list/search/verify surfaces (paged list covers exactly total_ok)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
