#!/usr/bin/env python3
"""VS-W5 focused validator: the committed owner-authorized-MIT GEPAI 2022 bundle.

- RC3 hermetic counts: every count is recomputed from the COMMITTED normalized.jsonl and
  must equal the manifest; content_sha256 must equal sha256(normalized.jsonl bytes).
- RC4 forbidden-token / provenance-separation: no email/key/URL/official-false-promotion
  leaks; distribution is a copyright fact only (official_source False, records unverified).
- RC5 quarantine exclusion: a known quarantined code is absent from every read surface
  (list/search) and verify_standard() stays fail-closed.

Distribution != authority: owner-authorized MIT redistribution is a copyright fact; it is
NOT official-source verification. Independent implementation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.curriculum.provider import CurriculumProvider  # noqa: E402

BUNDLE_DIR = ROOT / "providers" / "curriculum" / "bundle" / "2022"
INDEX_PATH = BUNDLE_DIR / "normalized.jsonl"
MANIFEST_PATH = BUNDLE_DIR / "manifest.json"

FORBIDDEN_PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    "openai_key": re.compile(r"sk-[A-Za-z0-9]{16,}"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_\-]{10,}"),
    "aws_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github_token": re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    "slack_token": re.compile(r"xox[baprs]-"),
    "url": re.compile(r"https?://"),
    "official_promotion": re.compile(r"교육부\s*공식|공식\s*출처|official\s*source|NCIC\s*verified|verified-compatible"),
}


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def load_bundle() -> tuple[list, dict, bytes]:
    raw = INDEX_PATH.read_bytes()
    records = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return records, manifest, raw


def iter_string_leaves(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from iter_string_leaves(v)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from iter_string_leaves(v)


def scan_record_tokens(rec: dict) -> list:
    violations = []
    for leaf in iter_string_leaves(rec):
        for name, pat in FORBIDDEN_PATTERNS.items():
            if pat.search(leaf):
                violations.append(f"forbidden {name} token: {leaf[:60]!r}")
    return violations


def scan_record_provenance(rec: dict) -> list:
    violations = []
    src = rec.get("source", {})
    if src.get("license_status") != "unverified":
        violations.append(f"record {rec.get('canonical_code')} license_status must stay unverified")
    if src.get("verified") is not False:
        violations.append(f"record {rec.get('canonical_code')} source.verified must be False")
    return violations


def scan_manifest(manifest: dict) -> list:
    violations = []
    if manifest.get("distribution") != "owner-authorized-mit":
        violations.append("manifest.distribution must be owner-authorized-mit")
    if manifest.get("official_source") is not False:
        violations.append("manifest.official_source must be False")
    return violations


def test_hermetic_counts() -> None:  # RC3
    records, manifest, raw = load_bundle()
    line_count = len(records)
    ok = sum(1 for r in records if r["status"] == "ok")
    quarantined = sum(1 for r in records if r["status"] != "ok")
    assert_true(line_count == manifest["record_count"], f"record_count drift: {line_count} != {manifest['record_count']}")
    assert_true(ok == manifest["ok_count"], f"ok_count drift: {ok} != {manifest['ok_count']}")
    assert_true(quarantined == manifest["quarantined_count"], f"quarantined_count drift: {quarantined} != {manifest['quarantined_count']}")
    assert_true(ok + quarantined == line_count, "ok + quarantined must equal record_count")
    content_sha = hashlib.sha256(raw).hexdigest()
    assert_true(content_sha == manifest["content_sha256"], f"content_sha256 drift: {content_sha} != {manifest['content_sha256']}")
    # source SHA is recorded provenance (never re-read here).
    assert_true(bool(manifest.get("source_sha256")), "manifest must record the source_sha256 provenance")
    assert_true(manifest["license_id"] == "MIT" and manifest["license_authority"] == "owner-authorized-mit", "OI-1 license fields")


def test_forbidden_tokens_and_separation() -> None:  # RC4
    records, manifest, _ = load_bundle()
    token_violations = []
    provenance_violations = []
    for rec in records:
        token_violations += scan_record_tokens(rec)
        provenance_violations += scan_record_provenance(rec)
    assert_true(not token_violations, f"committed records must have no forbidden tokens: {token_violations[:3]}")
    assert_true(not provenance_violations, f"every record must stay unverified/unverified: {provenance_violations[:3]}")
    assert_true(not scan_manifest(manifest), "manifest must declare owner-authorized-mit / official_source False")

    # Negatives: token injections must each be detected.
    base = copy.deepcopy(records[0])
    injections = {
        "email": {"content": "문의: teacher@example.com"},
        "openai_key": {"content": "key sk-ABCDEFGHIJKLMNOP12345"},
        "url": {"source": {**base["source"], "url": "https://ncic.re.kr/x"}},
        "official_promotion": {"content": "교육부 공식 성취기준"},
    }
    for name, patch in injections.items():
        bad = copy.deepcopy(base)
        bad.update(patch)
        assert_true(bool(scan_record_tokens(bad)), f"injected {name} must be detected")

    # Negative: a promoted license_status must be flagged.
    bad_lic = copy.deepcopy(base)
    bad_lic["source"] = {**base["source"], "license_status": "verified-compatible", "verified": True}
    assert_true(bool(scan_record_provenance(bad_lic)), "promoted license_status must be flagged")
    assert_true(bool(scan_record_tokens(bad_lic)), "verified-compatible authority claim must be flagged as token")

    # Negative: official_source True must be flagged.
    bad_manifest = {**manifest, "official_source": True}
    assert_true(bool(scan_manifest(bad_manifest)), "official_source True must be flagged")
    bad_dist = {**manifest, "distribution": "public-domain"}
    assert_true(bool(scan_manifest(bad_dist)), "unexpected distribution must be flagged")


def test_quarantine_exclusion() -> None:  # RC5
    records, manifest, _ = load_bundle()
    provider = CurriculumProvider(INDEX_PATH, MANIFEST_PATH)
    quarantined = next(r for r in records if r["status"] != "ok")
    qcode = quarantined["canonical_code"]

    # (a) absent from every page of list_standards; total ok == ok_count.
    seen: set = set()
    page = 0
    total_ok = None
    while True:
        result = provider.list_standards(page=page, page_size=500)
        total_ok = result["total_ok"]
        for row in result["records"]:
            assert_true(row["status"] == "ok", "list_standards must return only ok rows")
            seen.add(row["canonical_code"])
        if not result["records"]:
            break
        page += 1
    assert_true(total_ok == manifest["ok_count"], f"list total_ok {total_ok} != ok_count {manifest['ok_count']}")
    assert_true(qcode not in seen or all(
        provider.lookup_standard_by_code(qcode).status != "ok" for _ in [0]
    ), "quarantined code must never appear as an ok list row")
    assert_true(qcode not in seen, "quarantined canonical_code must be absent from list_standards")

    # (b) search never surfaces the quarantined record.
    search = provider.search_standards(keyword=qcode)
    assert_true(all(c["canonical_code"] != qcode for c in search["candidates"]), "search must not return the quarantined code")
    content_kw = (quarantined.get("content") or "")[:6]
    if content_kw:
        search2 = provider.search_standards(keyword=content_kw)
        assert_true(all(c["status"] == "ok" and c["canonical_code"] != qcode for c in search2["candidates"]),
                    "content-keyword search must not surface the quarantined record")

    # (c) verify_standard fail-closed on the quarantined code.
    report = provider.verify_standard(qcode)
    assert_true(report["downstream_ready"] is False, "quarantined code must not be downstream-ready")
    assert_true(report["status"] == "quarantined", "verify_standard must report quarantined status")

    # A representative ok record is resolvable but still fail-closed (unverified provenance).
    ok_rec = next(r for r in records if r["status"] == "ok")
    ok_report = provider.verify_standard(ok_rec["canonical_code"])
    assert_true(ok_report["downstream_ready"] is False, "even ok bundle records stay fail-closed (unverified)")


def main() -> None:
    assert_true(INDEX_PATH.exists(), f"committed bundle missing: {INDEX_PATH}")
    assert_true(MANIFEST_PATH.exists(), f"committed manifest missing: {MANIFEST_PATH}")
    _, manifest, _ = load_bundle()
    test_hermetic_counts()
    test_forbidden_tokens_and_separation()
    test_quarantine_exclusion()
    print("PASS validate_curriculum_bundle")
    print(f"- hermetic recount from committed bundle: {manifest['record_count']} records = "
          f"{manifest['ok_count']} ok + {manifest['quarantined_count']} quarantined; content_sha256 verified")
    print("- distribution=owner-authorized-mit, official_source=false; every record license_status=unverified/verified=false")
    print("- forbidden email/key/URL/official-promotion tokens absent; injections + license/official flips fail closed")
    print("- quarantine excluded at list/search/verify surfaces; even ok records stay downstream fail-closed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
