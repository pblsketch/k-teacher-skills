from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = [
    "grill-me-for-k-teacher",
    "grill-with-curriculum",
    "assessment-first-design",
    "diagnose-lesson-failure",
    "improve-lesson-architecture",
]


REQUIRED_TERMS = {
    "privacy": ["개인정보", "민감정보", "실명"],
    "anti_click": ["바로 만들지", "먼저", "즉시 만들지", "새 자료를 만들기 전에"],
    "udl": ["참여", "표현", "장벽"],
}


def assert_frontmatter(skill: str, text: str) -> None:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, f"{skill}: missing YAML frontmatter"
    frontmatter = match.group(1)
    assert re.search(rf"^name:\s*{re.escape(skill)}\s*$", frontmatter, re.M), (
        f"{skill}: frontmatter name mismatch"
    )
    assert re.search(r"^description:\s*\S+", frontmatter, re.M), (
        f"{skill}: missing description"
    )


def assert_contains_any(skill: str, text: str, label: str, terms: list[str]) -> None:
    assert any(term in text for term in terms), f"{skill}: missing {label} guard"


def main() -> None:
    assert (ROOT / "README.md").exists(), "README.md missing"
    assert (ROOT / "LICENSE").exists(), "LICENSE missing"
    assert (ROOT / "tests" / "expected-behaviors.md").exists(), (
        "expected-behaviors.md missing"
    )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Which skill should I use?" in readme, "README missing skill-selection guide"
    assert "Claude" in readme and "Codex" in readme, (
        "README missing Claude/Codex guidance"
    )

    for skill in SKILLS:
        skill_dir = ROOT / "skills" / skill
        skill_md = skill_dir / "SKILL.md"
        sample = skill_dir / "examples" / "sample-dialogue.md"
        assert skill_md.exists(), f"{skill}: SKILL.md missing"
        assert sample.exists(), f"{skill}: sample dialogue missing"

        text = skill_md.read_text(encoding="utf-8")
        assert_frontmatter(skill, text)
        for label, terms in REQUIRED_TERMS.items():
            assert_contains_any(skill, text, label, terms)

    diagnose = (ROOT / "skills" / "diagnose-lesson-failure" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "만약 [원인]이 문제라면" in diagnose, (
        "diagnose-lesson-failure: missing falsifiable hypothesis format"
    )

    architecture = (
        ROOT / "skills" / "improve-lesson-architecture" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "deletion test" in architecture.lower() or "삭제 테스트" in architecture, (
        "improve-lesson-architecture: missing deletion test"
    )
    assert "Strong candidate" in architecture, (
        "improve-lesson-architecture: missing candidate report"
    )

    curriculum = (
        ROOT / "skills" / "grill-with-curriculum" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "CURRICULUM-CONTEXT.md" in curriculum, (
        "grill-with-curriculum: missing context-file rules"
    )
    assert "LESSON-ADR.md" in curriculum, (
        "grill-with-curriculum: missing lesson decision record rules"
    )

    print("VALIDATION_OK")


if __name__ == "__main__":
    main()
