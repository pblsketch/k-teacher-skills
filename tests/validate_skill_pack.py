from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# v2.0: skills are organized into 7 group folders.
SKILL_PATHS = {
    "grill-me-for-k-teacher": "entry/grill-me-for-k-teacher",
    "grill-with-curriculum": "entry/grill-with-curriculum",
    "k-teacher-workflow-router": "entry/k-teacher-workflow-router",
    "lesson-prototype": "lesson-design/lesson-prototype",
    "to-lesson-brief": "lesson-design/to-lesson-brief",
    "improve-lesson-architecture": "lesson-design/improve-lesson-architecture",
    "zoom-out-lesson": "lesson-design/zoom-out-lesson",
    "thinking-routine-selector": "lesson-design/thinking-routine-selector",
    "concept-based-inquiry-designer": "inquiry-pbl/concept-based-inquiry-designer",
    "pbl-design-coach": "inquiry-pbl/pbl-design-coach",
    "assessment-first-design": "assessment/assessment-first-design",
    "rubric-quality-guard": "assessment/rubric-quality-guard",
    "hinge-question-designer": "assessment/hinge-question-designer",
    "differentiate-lesson-pathways": "individualization/differentiate-lesson-pathways",
    "udl-barrier-remover": "individualization/udl-barrier-remover",
    "diagnose-lesson-failure": "diagnostics/diagnose-lesson-failure",
    "ai-resilient-assignment-redesign": "ai-era/ai-resilient-assignment-redesign",
}

SKILLS = list(SKILL_PATHS.keys())


def skill_dir(skill: str) -> Path:
    return ROOT / "skills" / SKILL_PATHS[skill]


REQUIRED_TERMS = {
    "privacy": [
        "개인정보",
        "민감정보",
        "실명",
    ],
    "anti_click": [
        "바로 만들지",
        "먼저",
        "즉시 만들지",
        "새 자료를 만들기 전에",
        "완성",
        "새 질문을 먼저 던지지",
    ],
    "udl": [
        "참여",
        "표현",
        "장벽",
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
    assert (ROOT / "WORKFLOWS.md").exists(), "WORKFLOWS.md missing"
    assert (ROOT / "skill-pack.json").exists(), "skill-pack.json missing"
    assert (ROOT / "LICENSE").exists(), "LICENSE missing"
    for script in [
        "install-codex.ps1",
        "install-claude.ps1",
        "install-antigravity.ps1",
        "install-all.ps1",
    ]:
        assert (ROOT / "scripts" / script).exists(), f"{script} missing"
    assert (ROOT / "tests" / "expected-behaviors.md").exists(), (
        "expected-behaviors.md missing"
    )
    assert (ROOT / "references" / "questioning-style.md").exists(), (
        "questioning-style.md missing"
    )
    assert (ROOT / "references" / "interview-readiness.md").exists(), (
        "interview-readiness.md missing"
    )
    assert (ROOT / "references" / "ai-assignment-templates.md").exists(), (
        "ai-assignment-templates.md missing"
    )
    for reference in [
        "thinking-routines-matrix.md",
        "concept-based-inquiry.md",
        "differentiation-patterns.md",
        "rubric-quality.md",
        "hinge-question-design.md",
        "pbl-design.md",
        "udl-barrier-check.md",
    ]:
        assert (ROOT / "references" / reference).exists(), f"{reference} missing"
    for workflow in [
        "new-lesson-design.md",
        "curriculum-grounded-redesign.md",
        "lesson-failure-recovery.md",
        "material-architecture-improvement.md",
        "ai-resilient-assignment-redesign.md",
        "conceptual-inquiry-lesson.md",
        "differentiated-lesson-redesign.md",
        "assessment-quality-upgrade.md",
        "pbl-design-workflow.md",
        "udl-accessible-lesson-redesign.md",
    ]:
        assert (ROOT / "workflows" / workflow).exists(), f"{workflow} missing"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Which skill should I use?" in readme, "README missing skill-selection guide"
    assert "Quick install" in readme, "README missing quick install guide"
    assert "k-teacher-workflow-router로 내 요청을 분석" in readme, (
        "README missing router-first prompt"
    )
    assert "interview-readiness.md" in readme, "README missing interview readiness guide"
    assert "Claude" in readme and "Codex" in readme, (
        "README missing Claude/Codex guidance"
    )
    for skill in SKILLS:
        assert skill in readme, f"README missing {skill}"

    workflows_md = (ROOT / "WORKFLOWS.md").read_text(encoding="utf-8")
    assert "Router-first rule" in workflows_md, "WORKFLOWS missing router-first rule"
    assert "to-lesson-brief" in workflows_md, "WORKFLOWS missing final handoff"

    manifest = json.loads((ROOT / "skill-pack.json").read_text(encoding="utf-8"))
    assert manifest["entrySkill"] == "k-teacher-workflow-router", (
        "manifest entrySkill mismatch"
    )
    manifest_skills = {item["name"] for item in manifest["skills"]}
    assert manifest_skills == set(SKILLS), "manifest skills do not match SKILLS"
    # v2.0: ensure manifest paths match the hierarchical layout
    for item in manifest["skills"]:
        expected_path = f"skills/{SKILL_PATHS[item['name']]}"
        assert item["path"] == expected_path, (
            f"manifest skill path mismatch for {item['name']}: "
            f"{item['path']} != {expected_path}"
        )
        assert (ROOT / item["path"]).exists(), (
            f"manifest skill path does not exist on disk: {item['path']}"
        )
    assert len(manifest["workflows"]) == 10, "manifest workflow count mismatch"
    for workflow in manifest["workflows"]:
        assert (ROOT / workflow["path"]).exists(), (
            f"manifest workflow path missing: {workflow['path']}"
        )
        for skill in workflow["chain"]:
            assert skill in manifest_skills, (
                f"manifest workflow references unknown skill: {skill}"
            )

    for skill in SKILLS:
        sd = skill_dir(skill)
        skill_md = sd / "SKILL.md"
        sample = sd / "examples" / "sample-dialogue.md"
        assert skill_md.exists(), f"{skill}: SKILL.md missing at {skill_md}"
        assert sample.exists(), f"{skill}: sample dialogue missing"

        text = skill_md.read_text(encoding="utf-8")
        assert_frontmatter(skill, text)
        assert "interview-readiness.md" in text, (
            f"{skill}: missing interview readiness reference"
        )
        for label, terms in REQUIRED_TERMS.items():
            assert_contains_any(skill, text, label, terms)

    diagnose = (skill_dir("diagnose-lesson-failure") / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "만약 [원인]이 문제라면" in diagnose, (
        "diagnose-lesson-failure: missing falsifiable hypothesis format"
    )

    architecture = (
        skill_dir("improve-lesson-architecture") / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "deletion test" in architecture.lower() or "삭제 테스트" in architecture, (
        "improve-lesson-architecture: missing deletion test"
    )
    assert "Strong candidate" in architecture, (
        "improve-lesson-architecture: missing candidate report"
    )

    curriculum = (
        skill_dir("grill-with-curriculum") / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "CURRICULUM-CONTEXT.md" in curriculum, (
        "grill-with-curriculum: missing context-file rules"
    )
    assert "LESSON-ADR.md" in curriculum, (
        "grill-with-curriculum: missing lesson decision record rules"
    )

    zoom_out = (skill_dir("zoom-out-lesson") / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "한 단계 위" in zoom_out, (
        "zoom-out-lesson: missing one-layer-up rule"
    )

    prototype = (skill_dir("lesson-prototype") / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "Prototype A" in prototype and "비교" in prototype, (
        "lesson-prototype: missing prototype comparison structure"
    )

    brief = (skill_dir("to-lesson-brief") / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "미확정" in brief and "추정" in brief, (
        "to-lesson-brief: missing unknown/assumption handling"
    )

    ai_assignment = (
        skill_dir("ai-resilient-assignment-redesign") / "SKILL.md"
    ).read_text(encoding="utf-8")
    for term in [
        "H→AI→H",
        "프롬프트 로그",
        "SHIFT",
        "50%",
        "AI 탐지 도구 단독",
        "ai-assignment-templates.md",
    ]:
        assert term in ai_assignment, (
            f"ai-resilient-assignment-redesign: missing {term}"
        )

    skill_terms = {
        "thinking-routine-selector": ["사고 루틴", "thinking-routines-matrix.md", "평가 증거"],
        "concept-based-inquiry-designer": ["일반화", "개념적", "논쟁적 질문"],
        "differentiate-lesson-pathways": ["기초", "표준", "심화"],
        "rubric-quality-guard": ["평가 준거", "수준 기술", "rubric-quality.md"],
        "hinge-question-designer": ["힌지 질문", "오개념", "교사 대응"],
        "pbl-design-coach": ["driving question", "실제 문제", "과정 평가"],
        "udl-barrier-remover": ["참여", "표상", "행동과 표현"],
    }
    for skill, terms in skill_terms.items():
        text = (skill_dir(skill) / "SKILL.md").read_text(encoding="utf-8")
        for term in terms:
            assert term in text, f"{skill}: missing {term}"

    router = (
        skill_dir("k-teacher-workflow-router") / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "New lesson design" in router and "Lesson failure recovery" in router, (
        "k-teacher-workflow-router: missing workflow routing recipes"
    )
    assert "AI-resilient assignment redesign" in router, (
        "k-teacher-workflow-router: missing AI-resilient workflow"
    )
    for route in [
        "thinking-routine-selector",
        "concept-based-inquiry-designer",
        "differentiate-lesson-pathways",
        "rubric-quality-guard",
        "hinge-question-designer",
        "pbl-design-coach",
        "udl-barrier-remover",
    ]:
        assert route in router, f"k-teacher-workflow-router: missing {route}"
    assert "선택지" in router and "기타" in router, (
        "k-teacher-workflow-router: missing choice-based questioning"
    )
    assert "readiness gate" in router, (
        "k-teacher-workflow-router: missing readiness gate reference"
    )

    for skill in SKILLS:
        text = (skill_dir(skill) / "SKILL.md").read_text(encoding="utf-8")
        assert "선택지" in text or "A." in text, (
            f"{skill}: missing choice-based questioning signal"
        )

    print("VALIDATION_OK")


if __name__ == "__main__":
    main()
