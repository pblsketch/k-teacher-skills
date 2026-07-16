#!/usr/bin/env python3
"""VS5 focused validator: Axis D authored assets (independent implementation).

Checks THIRD_PARTY_NOTICES attribution, the 6 school-materials skill docs, and the
subject pedagogy references (observable failures, misconception what+why+response,
rigor preservation, hardest-case exit ticket, and NO US standards).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKILLS = [
    "school-evaluation-plan-to-materials",
    "school-plan-grounding",
    "standard-alignment-verify",
    "assessment-evidence-builder",
    "secondary-material-builder",
    "material-rubric-qa",
]
SUBJECT_REFS = ["science.md", "korean-language.md", "social-studies.md", "math.md"]
US_STANDARD_TERMS = ["Common Core", "NGSS", "C3 Framework", "WIDA", "state standards"]


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_third_party_notices() -> None:
    p = ROOT / "THIRD_PARTY_NOTICES.md"
    assert_true(p.exists(), "THIRD_PARTY_NOTICES.md must exist")
    t = p.read_text(encoding="utf-8")
    assert_true("Apache License 2.0" in t or "Apache-2.0" in t, "Apache-2.0 attribution present")
    assert_true("MIT" in t, "MIT attribution present")
    assert_true("no" in t.lower() and "copied" in t.lower(), "explicit no-code-copied notice")
    assert_true("Change notice" in t, "Apache change-notice clause present")
    assert_true("owner-authorized MIT" in t or "owner-authorized-mit" in t, "GEPAI owner-authorized-MIT distribution recorded")
    assert_true("NOT an official Ministry" in t, "GEPAI not-official-source (distribution != authority) recorded")
    assert_true("provenance-unverified" in t and "fail-closed" in t, "GEPAI records provenance-unverified / fail-closed recorded")
    # US standards mentioned only in the 'NOT taken' context.
    assert_true("no United States standards" in t or "NOT ... standards" in t or "no ... standards" in t.replace("**", "") or "no **United States standards" in t or "not take" in t.lower(), "US standards explicitly excluded")
    # L2: the notices file must end with exactly one trailing newline (no missing/duplicate EOL).
    raw = p.read_bytes()
    assert_true(raw.endswith(b"\n") and not raw.endswith(b"\n\n"),
                "THIRD_PARTY_NOTICES.md must end with exactly one trailing newline")


def test_skill_docs() -> None:
    base = ROOT / "skills" / "school-materials"
    assert_true((base / "README.md").exists(), "school-materials README present")
    for s in SKILLS:
        md = base / s / "SKILL.md"
        assert_true(md.exists(), f"{s}: SKILL.md missing")
        t = md.read_text(encoding="utf-8")
        assert_true(t.startswith("---") and "name:" in t, f"{s}: frontmatter present")
        assert_true("Observable failure" in t or "관찰 가능한 실패" in t, f"{s}: observable failure conditions")
        assert_true("independent_implementation" in t, f"{s}: independent-implementation marker")
    # orchestrator asserts authority order + fail-closed.
    orch = (base / "school-evaluation-plan-to-materials" / "SKILL.md").read_text(encoding="utf-8")
    assert_true("국가" in orch and "override" in orch and "교사" in orch, "orchestrator states authority + teacher-final")
    assert_true("Fail-closed" in orch or "fail-closed" in orch, "orchestrator fail-closed")
    # assessment-evidence-builder: misconception 3-part + hardest-case exit ticket + rigor.
    aeb = (base / "assessment-evidence-builder" / "SKILL.md").read_text(encoding="utf-8")
    assert_true("what + why + response" in aeb or ("무엇을 틀리는가" in aeb and "왜 생기는가" in aeb and "교사 대응" in aeb), "misconception what+why+response")
    assert_true("exit ticket" in aeb.lower() or "출구표" in aeb, "hardest-case exit ticket")
    assert_true("Rigor" in aeb or "rigor" in aeb, "rigor preservation")


def test_subject_references() -> None:
    base = ROOT / "references" / "subject"
    for ref in SUBJECT_REFS:
        p = base / ref
        assert_true(p.exists(), f"subject ref {ref} missing")
        t = p.read_text(encoding="utf-8")
        assert_true("Observable failure" in t or "관찰 가능한 실패" in t, f"{ref}: observable failures")
        assert_true("what + why + response" in t or ("what:" in t and "why:" in t and "response:" in t), f"{ref}: misconception what+why+response")
        assert_true("Rigor" in t or "rigor" in t or "엄밀성 보존" in t, f"{ref}: rigor preservation")
        assert_true("exit ticket" in t.lower() or "출구표" in t, f"{ref}: hardest-case exit ticket")
        for us in US_STANDARD_TERMS:
            assert_true(us not in t, f"{ref}: US standard term '{us}' must not be adopted")


def main() -> None:
    test_third_party_notices()
    test_skill_docs()
    test_subject_references()
    print("PASS validate_axisd_assets")
    print("- THIRD_PARTY_NOTICES: Apache-2.0 (ideas-only) + MIT + change-notice + GEPAI owner-authorized-MIT (NOT official, fail-closed)")
    print("- 6 school-materials skills authored (independent, observable failures, fail-closed authority)")
    print("- 4 subject references: observable failures, misconception what+why+response, rigor, exit ticket, no US standards")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
