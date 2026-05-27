from __future__ import annotations

import json
import re
import sys
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

    # ========================================================================
    # Readiness Gate v2 (v2.5.1+) validation — 4 new loops
    # ========================================================================

    readiness = (ROOT / "references" / "interview-readiness.md").read_text(
        encoding="utf-8"
    )

    # Loop α — gate-vocabulary (17 markers; +3 provenance grades from v2.5.2)
    for marker in [
        "Readiness Gate v2",
        "intent·0.30",
        "Stage 1",
        "Stage 2",
        "Stage 3",
        "Pressure Ladder",
        "from-curriculum",
        "from-textbook",
        "from-class-context",
        "from-teacher-judgment",
        "Round 0",
        "Contrarian",
        "Simplifier",
        "Ontologist",
        ":provided",
        ":web",
        ":inferred",
    ]:
        assert marker in readiness, (
            f"interview-readiness.md missing v2 marker: {marker}"
        )

    # Loop β — per-skill block presence
    for skill in SKILLS:
        text = (skill_dir(skill) / "SKILL.md").read_text(encoding="utf-8")
        assert "## Readiness gate v2" in text, (
            f"{skill}: missing v2 readiness-gate block"
        )

    # Loop γ — section order (must be [1..12] in document order)
    section_nums = [
        int(m.group(1)) for m in re.finditer(r"^##\s*§(\d+)", readiness, re.M)
    ]
    assert section_nums == list(range(1, 13)), (
        f"interview-readiness.md section order mismatch: "
        f"{section_nums} != [1..12]"
    )

    # Loop δ — per-skill mapping match against JSON SSOT
    mapping_path = ROOT / "tests" / "readiness_gate_v2_mapping.json"
    assert mapping_path.exists(), (
        "tests/readiness_gate_v2_mapping.json missing"
    )
    mapping_raw = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping = {k: v for k, v in mapping_raw.items() if not k.startswith("_")}
    assert set(mapping.keys()) == set(SKILLS), (
        f"mapping JSON skill set mismatch: "
        f"missing {set(SKILLS) - set(mapping.keys())}, "
        f"extra {set(mapping.keys()) - set(SKILLS)}"
    )

    block_re = re.compile(
        r"##\s*Readiness gate v2[^\n]*\n"
        r"-\s*Default profile:\s*(?P<profile>[^\n]+)\n"
        r"-\s*Active stage:\s*(?P<stage>[^\n]+)\n"
        r"-\s*Fact routing in this skill:\s*(?P<labels>[^\n]+)\n"
        r"-\s*Tier 3[^:]*:\s*(?P<tier3>[^\n]+)\n",
        re.M,
    )
    for skill in SKILLS:
        text = (skill_dir(skill) / "SKILL.md").read_text(encoding="utf-8")
        m = block_re.search(text)
        assert m, f"{skill}: v2 block missing canonical 4 fields"
        actual = {
            "profile": m.group("profile").strip(),
            "stage": m.group("stage").strip(),
            "labels": m.group("labels").strip(),
            "tier3": m.group("tier3").strip(),
        }
        expected = mapping[skill]
        assert actual == expected, (
            f"{skill}: v2 block does not match mapping JSON\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}"
        )

    # Skill-pack version check
    manifest_v = json.loads(
        (ROOT / "skill-pack.json").read_text(encoding="utf-8")
    )["version"]
    assert manifest_v == "2.5.3", (
        f"skill-pack.json version must be 2.5.3, got {manifest_v}"
    )

    # ========================================================================
    # Claude Cowork / Claude Code plugin manifest (v2.5.3+)
    # ========================================================================

    plugin_path = ROOT / ".claude-plugin" / "plugin.json"
    assert plugin_path.exists(), ".claude-plugin/plugin.json missing"
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))

    assert plugin.get("name") == "k-teacher-skills", (
        f"plugin.json name must be 'k-teacher-skills', got {plugin.get('name')}"
    )
    assert plugin.get("version") == "2.5.3", (
        f"plugin.json version must be 2.5.3, got {plugin.get('version')}"
    )
    plugin_skills = plugin.get("skills", [])
    assert len(plugin_skills) == 17, (
        f"plugin.json skills array must have 17 entries, got {len(plugin_skills)}"
    )
    for skill_path in plugin_skills:
        rel = skill_path.lstrip("./")
        full = ROOT / rel
        assert full.exists(), (
            f"plugin.json skill path does not exist: {skill_path}"
        )

    market_path = ROOT / ".claude-plugin" / "marketplace.json"
    assert market_path.exists(), ".claude-plugin/marketplace.json missing"
    market = json.loads(market_path.read_text(encoding="utf-8"))
    assert market.get("version") == "2.5.3", (
        f"marketplace.json version must be 2.5.3, got {market.get('version')}"
    )
    market_plugins = market.get("plugins", [])
    assert len(market_plugins) == 1, (
        f"marketplace.json plugins array must have 1 entry, got {len(market_plugins)}"
    )
    assert market_plugins[0].get("name") == "k-teacher-skills", (
        "marketplace.json plugin[0].name mismatch"
    )
    assert market_plugins[0].get("version") == "2.5.3", (
        "marketplace.json plugin[0].version must be 2.5.3"
    )

    # Commands directory: 11 slash commands
    commands_dir = ROOT / "commands"
    assert commands_dir.is_dir(), "commands/ directory missing"
    expected_commands = {
        "k-teacher",
        "new-lesson",
        "redesign",
        "failure",
        "architecture",
        "ai-assignment",
        "inquiry",
        "differentiate",
        "assessment",
        "pbl",
        "udl",
    }
    actual_commands = {p.stem for p in commands_dir.glob("*.md")}
    assert expected_commands == actual_commands, (
        f"commands/ mismatch.\n"
        f"  expected: {sorted(expected_commands)}\n"
        f"  actual:   {sorted(actual_commands)}\n"
        f"  missing:  {sorted(expected_commands - actual_commands)}\n"
        f"  extra:    {sorted(actual_commands - expected_commands)}"
    )

    # Each command file has YAML frontmatter with description
    for cmd in expected_commands:
        cmd_path = commands_dir / f"{cmd}.md"
        cmd_text = cmd_path.read_text(encoding="utf-8")
        assert re.match(r"^---\n(.*?)\n---\n", cmd_text, re.S), (
            f"commands/{cmd}.md: missing YAML frontmatter"
        )
        m = re.search(r"^description:\s*\S+", cmd_text[: cmd_text.index("---", 3) + 3], re.M)
        assert m, f"commands/{cmd}.md: missing description in frontmatter"

    print("VALIDATION_OK")


if __name__ == "__main__":
    main()
