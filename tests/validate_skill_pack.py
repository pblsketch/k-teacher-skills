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
    "zoom-out-lesson",
    "lesson-prototype",
    "to-lesson-brief",
]


REQUIRED_TERMS = {
    "privacy": [
        "\uac1c\uc778\uc815\ubcf4",
        "\ubbfc\uac10\uc815\ubcf4",
        "\uc2e4\uba85",
    ],
    "anti_click": [
        "\ubc14\ub85c \ub9cc\ub4e4\uc9c0",
        "\uba3c\uc800",
        "\uc989\uc2dc \ub9cc\ub4e4\uc9c0",
        "\uc0c8 \uc790\ub8cc\ub97c \ub9cc\ub4e4\uae30 \uc804\uc5d0",
        "\uc644\uc131",
        "\uc0c8 \uc9c8\ubb38\uc744 \uba3c\uc800 \ub358\uc9c0\uc9c0",
    ],
    "udl": [
        "\ucc38\uc5ec",
        "\ud45c\ud604",
        "\uc7a5\ubcbd",
    ],
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
        assert skill in readme, f"README missing {skill}"

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
    assert "\ub9cc\uc57d [\uc6d0\uc778]\uc774 \ubb38\uc81c\ub77c\uba74" in diagnose, (
        "diagnose-lesson-failure: missing falsifiable hypothesis format"
    )

    architecture = (
        ROOT / "skills" / "improve-lesson-architecture" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "deletion test" in architecture.lower() or "\uc0ad\uc81c \ud14c\uc2a4\ud2b8" in architecture, (
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

    zoom_out = (ROOT / "skills" / "zoom-out-lesson" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "\ud55c \ub2e8\uacc4 \uc704" in zoom_out, (
        "zoom-out-lesson: missing one-layer-up rule"
    )

    prototype = (ROOT / "skills" / "lesson-prototype" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "Prototype A" in prototype and "\ube44\uad50" in prototype, (
        "lesson-prototype: missing prototype comparison structure"
    )

    brief = (ROOT / "skills" / "to-lesson-brief" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "\ubbf8\ud655\uc815" in brief and "\ucd94\uc815" in brief, (
        "to-lesson-brief: missing unknown/assumption handling"
    )

    print("VALIDATION_OK")


if __name__ == "__main__":
    main()
