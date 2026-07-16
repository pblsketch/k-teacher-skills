from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SURFACE_MATRIX_PATH = ROOT / "tests" / "public-surface-validation-matrix.json"
SAMPLE_DIALOGUE_GATE_V2_PATH = (
    ROOT
    / "skills"
    / "entry"
    / "grill-me-for-k-teacher"
    / "examples"
    / "sample-dialogue-gate-v2.md"
)


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

def validate_readiness_gate_contract(text: str) -> None:
    assert_all_terms(
        text,
        [
            "Readiness profile: {Quick|Standard|Deep} | threshold: {0.30|0.20|0.15} | source: {explicit|router-inferred|skill-default}",
            "Stage 1의 어떤 차원이라도 weak(≥0.6)이면 Stage 2 질문으로 넘어가지 않는다.",
            "§4 mandatory gate 5개 모두 통과",
        ],
        "interview-readiness.md gate contract drift",
    )


def validate_readiness_stateless_resume_fields(text: str) -> None:
    assert_all_terms(
        text,
        [
            "저는 영구 메모리가 없어 이전 인터뷰 상태를 자동 복원하지 못합니다.",
            "{프로파일, 잠금 단위, 직전 약점 dimension, 직전 답변 요약}",
        ],
        "interview-readiness.md stateless resume contract drift",
    )


def validate_readiness_transcript_handoff(text: str) -> None:
    assert_all_terms(
        text,
        [
            "`to-lesson-brief` 핸드오프 시에는 transcript의 마지막 §12 출력 블록 + topology 잠금 결과를 named context block으로 인계한다.",
            "이건 *transcript-기반 인계*이지 별도 snapshot 저장소가 아니다.",
        ],
        "interview-readiness.md transcript handoff contract drift",
    )


def validate_readiness_provenance_no_unblock(text: str) -> None:
    assert_all_terms(
        text,
        [
            "unresolved `:inferred` 사실이 하나라도 남아 있으면 provenance가 아직 풀리지 않은 상태로 본다.",
            "`to-lesson-brief` downstream-ready handoff, `author-ir`, `render`를 unblock하지 않는다.",
            "provider가 제공한 원문·응답은 read-only input으로만 취급한다.",
            "`provider` · `provenance_grade` · `source_reference` · `verification_evidence_type` · `verification_anchor` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input`이 모두 맞아야 clearance 근거가 된다.",
            "`source_license.status`가 `verified-compatible`이 아니면 downstream-ready를 열지 않는다.",
            "`provider` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input` evidence가 계속 필요하다.",
            "provider record는 `quarantined`로 격리한다.",
        ],
        "interview-readiness.md provenance no-unblock contract drift",
    )


def validate_expected_behaviors_topology_lock(text: str) -> None:
    assert_all_terms(
        text,
        [
            "**Topology lock acknowledgement**",
            "Tier 3 enabled 스킬은 Round 0 topology 결과를 `to-lesson-brief` 핸드오프 named context block에 포함.",
        ],
        "expected-behaviors.md topology-lock contract drift",
    )


def validate_expected_behaviors_stateless_resume_guidance(text: str) -> None:
    assert_all_terms(
        text,
        [
            "**Stateless transparency**",
            "사용자 resume 요청 시 transcript 기반 인계임을 명시.",
        ],
        "expected-behaviors.md stateless transparency drift",
    )


def validate_expected_behaviors_bucket_separation(text: str) -> None:
    assert_all_terms(
        text,
        [
            "- 대화에 없는 정보는 `미확정`으로 표시한다.",
            "- 확정/추정/교사 판단 필요 항목을 분리한다.",
        ],
        "expected-behaviors.md to-lesson-brief bucket separation drift",
    )


def validate_expected_behaviors_provenance_no_unblock(text: str) -> None:
    assert_all_terms(
        text,
        [
            "**Downstream-ready no-unblock (`:inferred`)**",
            "downstream-ready handoff, `author-ir`, `render`로 넘기지 않는다.",
            "**Provider output read-only 입력**",
            "`provider` record로만 들고 가며 `read_only_input: true`를 유지한 채 provenance를 우회해 ready 상태를 만들지 않는다.",
            "**Per-record clearance evidence**",
            "`provider` · `provenance_grade` · `source_reference` · `verification_evidence_type` · `verification_anchor` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input`",
            "**Provider/provenance/license fail-closed**",
            "`source_license.status`가 `verified-compatible`이 아니면 downstream-ready가 아니다.",
            "`provider` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input` evidence 없이는 downstream-ready가 아니다.",
            "**Provider quarantine fail-closed**",
            "provider record는 `quarantined`로 격리한다.",
        ],
        "expected-behaviors.md provenance no-unblock contract drift",
    )


def validate_readme_provider_contract(text: str) -> None:
    assert_all_terms(
        text,
        [
            "provider 출력은 read-only input으로만 취급합니다.",
            "`provider` · `provenance_grade` · `source_reference` · `verification_evidence_type` · `verification_anchor` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input`이 모두 맞아야 clearance 근거가 됩니다.",
            "`source_license.status`가 `verified-compatible`이 아니면 downstream-ready가 아닙니다.",
            "unresolved `:inferred`는 `to-lesson-brief` downstream-ready handoff, `author-ir`, `render`를 unblock하지 않습니다.",
            "`provider`, `source_license.status`, `source_license.license_id`, `source_license.evidence_anchor`, `read_only_input` evidence 없이는 downstream-ready가 아닙니다.",
            "provider record는 `quarantined`로 격리하며 downstream-ready handoff, `author-ir`, `render`를 열지 않습니다.",
        ],
        "README provider contract drift",
    )



def validate_readme_release_gate_semantic_precedence(text: str) -> None:
    assert_all_terms(
        text,
        [
            "release-gate fixtures: `tests/golden/semantic-eval/valid.json`, `tests/golden/release-observability/valid.json`",
            "semantic eval은 `workflow-envelope`, `lesson-package-ir`, `kteacher-backport-marker`, `renderer-parity` deterministic validator가 모두 통과된 뒤에만 실행되며, deterministic 실패를 override하지 않습니다.",
        ],
        "README semantic precedence drift",
    )



def validate_readme_release_gate_semantic_dimensions(text: str) -> None:
    assert_all_terms(
        text,
        [
            "semantic eval dimensions: `workflow-selection-quality`, `pedagogy-quality`, `rigor-preservation`, `usability-accessibility`, `post-verification-curriculum-alignment-quality`",
        ],
        "README semantic dimensions drift",
    )



def validate_readme_release_gate_observability_counters(text: str) -> None:
    assert_all_terms(
        text,
        [
            "observability counters: `entry_mode_counts`, `resume_mode_counts`, `open_boundary_counts_by_category_output_class`, `blocked_output_reasons_by_class`, `backport_enforcement_failures_by_format`, `udl_vs_differentiated_workflow_entry_counts`, `public_surface_drift_failures` (README / `skill-pack.json` / `.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` 포함)",
        ],
        "README observability counter drift",
    )



def validate_manifest_entry_skill_exact(text: str) -> None:
    assert '"entrySkill": "k-teacher-workflow-router"' in text, (
        "skill-pack.json entry skill drift"
    )



def validate_manifest_validation_lane_exact(text: str) -> None:
    assert (
        '"validationCommand": "python tests/validate_skill_pack.py && python tests/validate_workflow_envelope.py && python tests/validate_lesson_package_ir.py && python tests/validate_backport_marker.py && python tests/validate_renderer_parity.py && python tests/validate_release_gate_assets.py && python tests/validate_public_surface_regressions.py && python tests/validate_provider_skills.py"'
        in text
    ), "skill-pack.json validation lane drift"



def validate_manifest_semantic_eval_release_gate_assets(text: str) -> None:
    assert_all_terms(
        text,
        [
            '"semanticEvalFixture": "tests/golden/semantic-eval/valid.json"',
            '"deterministicValidatorPrecedence": [',
            '"workflow-envelope"',
            '"lesson-package-ir"',
            '"kteacher-backport-marker"',
            '"renderer-parity"',
            '"workflow-selection-quality"',
            '"pedagogy-quality"',
            '"rigor-preservation"',
            '"usability-accessibility"',
            '"post-verification-curriculum-alignment-quality"',
        ],
        "skill-pack.json semantic-eval asset drift",
    )



def validate_manifest_observability_counter_contract(text: str) -> None:
    assert_all_terms(
        text,
        [
            '"observabilityFixture": "tests/golden/release-observability/valid.json"',
            '"entry_mode_counts"',
            '"resume_mode_counts"',
            '"open_boundary_counts_by_category_output_class"',
            '"blocked_output_reasons_by_class"',
            '"backport_enforcement_failures_by_format"',
            '"udl_vs_differentiated_workflow_entry_counts"',
            '"public_surface_drift_failures"',
            '".claude-plugin/plugin.json"',
            '".claude-plugin/marketplace.json"',
        ],
        "skill-pack.json observability contract drift",
    )



def validate_research_semantic_eval_deterministic_precedence(text: str) -> None:
    assert_all_terms(
        text,
        [
            "`tests/golden/semantic-eval/valid.json`은 semantic eval이 `workflow-envelope`·`lesson-package-ir`·`kteacher-backport-marker`·`renderer-parity` deterministic validator 실패 뒤에서만 실행되고, 그 실패를 override하지 못함을 고정합니다.",
        ],
        "research-evaluation.md semantic precedence drift",
    )



def validate_research_semantic_eval_dimensions(text: str) -> None:
    assert_all_terms(
        text,
        [
            "semantic eval 차원은 `workflow-selection-quality`, `pedagogy-quality`, `rigor-preservation`, `usability-accessibility`, `post-verification-curriculum-alignment-quality` 5개로 고정합니다.",
        ],
        "research-evaluation.md semantic dimensions drift",
    )



def validate_research_observability_and_plugin_metadata(text: str) -> None:
    assert_all_terms(
        text,
        [
            "`tests/golden/release-observability/valid.json`은 `entry_mode_counts`, `resume_mode_counts`, `open_boundary_counts_by_category_output_class`, `blocked_output_reasons_by_class`, `backport_enforcement_failures_by_format`, `udl_vs_differentiated_workflow_entry_counts`, `public_surface_drift_failures`를 공개 counter 계약으로 고정하며 `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` drift를 포함합니다.",
        ],
        "research-evaluation.md observability drift",
    )


def load_routing_registry() -> dict:
    return json.loads(
        (ROOT / "registry" / "routing-gate-registry.json").read_text(encoding="utf-8")
    )


def assert_projection_equal(actual: object, expected: object, label: str) -> None:
    """Closed-world deep equality with ordered object-key comparison at every level."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{label}: expected object, got {type(actual).__name__}"
        assert list(actual.keys()) == list(expected.keys()), (
            f"{label}: key set/order drift; expected {list(expected.keys())}, got {list(actual.keys())}"
        )
        for key in expected:
            assert_projection_equal(actual[key], expected[key], f"{label}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list), f"{label}: expected array, got {type(actual).__name__}"
        assert len(actual) == len(expected), (
            f"{label}: array length drift; expected {len(expected)}, got {len(actual)}"
        )
        for index, item in enumerate(expected):
            assert_projection_equal(actual[index], item, f"{label}[{index}]")
    else:
        assert actual == expected, f"{label}: value drift; expected {expected!r}, got {actual!r}"


def expected_plugin_json_projection(registry: dict) -> dict:
    projection = registry["plugin_projection"]["plugin_json"]
    order = projection["top_level_key_order"]
    return {key: projection[key] for key in order}


def expected_marketplace_json_projection(registry: dict) -> dict:
    projection = registry["plugin_projection"]["marketplace_json"]
    top_order = projection["top_level_key_order"]
    entry_order = projection["plugin_entry_key_order"]
    expected: dict = {}
    for key in top_order:
        if key == "plugins":
            expected["plugins"] = [
                {entry_key: entry[entry_key] for entry_key in entry_order}
                for entry in projection["plugins"]
            ]
        else:
            expected[key] = projection[key]
    return expected


def validate_plugin_json_registry_projection(text: str) -> None:
    registry = load_routing_registry()
    expected = expected_plugin_json_projection(registry)
    actual = json.loads(text)
    assert_projection_equal(actual, expected, ".claude-plugin/plugin.json")
    skills = actual["skills"]
    assert len(skills) == 17, (
        f".claude-plugin/plugin.json: skills must list 17 canonical paths, got {len(skills)}"
    )
    for skill_path in skills:
        rel = skill_path.lstrip("./")
        assert (ROOT / rel).exists(), (
            f".claude-plugin/plugin.json: skill path does not exist on disk: {skill_path}"
        )


def validate_marketplace_json_registry_projection(text: str) -> None:
    registry = load_routing_registry()
    expected = expected_marketplace_json_projection(registry)
    actual = json.loads(text)
    assert_projection_equal(actual, expected, ".claude-plugin/marketplace.json")


SURFACE_VALIDATORS = {
    "README.md": {
        "provider_contract_present": validate_readme_provider_contract,
        "release_gate_semantic_precedence_present": validate_readme_release_gate_semantic_precedence,
        "release_gate_semantic_dimensions_present": validate_readme_release_gate_semantic_dimensions,
        "release_gate_observability_counters_present": validate_readme_release_gate_observability_counters,
    },
    "references/interview-readiness.md": {
        "gate_contract_registry_aligned": validate_readiness_gate_contract,
        "stateless_resume_fields_present": validate_readiness_stateless_resume_fields,
        "transcript_handoff_is_last_section12_plus_topology": validate_readiness_transcript_handoff,
        "provenance_no_unblock_contract_present": validate_readiness_provenance_no_unblock,
    },
    "tests/expected-behaviors.md": {
        "topology_lock_acknowledged": validate_expected_behaviors_topology_lock,
        "stateless_resume_guidance_present": validate_expected_behaviors_stateless_resume_guidance,
        "lesson_brief_bucket_separation_present": validate_expected_behaviors_bucket_separation,
        "provenance_no_unblock_contract_present": validate_expected_behaviors_provenance_no_unblock,
    },
    "skill-pack.json": {
        "entry_skill_exact": validate_manifest_entry_skill_exact,
        "validation_lane_exact": validate_manifest_validation_lane_exact,
        "semantic_eval_release_gate_assets_present": validate_manifest_semantic_eval_release_gate_assets,
        "observability_counter_contract_present": validate_manifest_observability_counter_contract,
    },
    "research-evaluation.md": {
        "semantic_eval_deterministic_precedence_present": validate_research_semantic_eval_deterministic_precedence,
        "semantic_eval_dimensions_present": validate_research_semantic_eval_dimensions,
        "observability_and_plugin_metadata_present": validate_research_observability_and_plugin_metadata,
    },
    ".claude-plugin/plugin.json": {
        "plugin_json_registry_projection_exact": validate_plugin_json_registry_projection,
    },
    ".claude-plugin/marketplace.json": {
        "marketplace_json_registry_projection_exact": validate_marketplace_json_registry_projection,
    },
}


def load_public_surface_matrix() -> dict[str, dict[str, object]]:
    assert PUBLIC_SURFACE_MATRIX_PATH.exists(), (
        "tests/public-surface-validation-matrix.json missing"
    )
    matrix = json.loads(PUBLIC_SURFACE_MATRIX_PATH.read_text(encoding="utf-8"))
    surfaces = {
        entry["surface"]: entry
        for entry in matrix["surfaces"]
    }
    for surface, validators in SURFACE_VALIDATORS.items():
        assert surface in surfaces, f"public surface matrix missing {surface}"
        entry = surfaces[surface]
        assert "never independent authority" in str(entry["canonical_source"]), (
            f"{surface}: matrix canonical_source must stay derivative-only"
        )
        validator_keys = entry.get("validator_keys")
        assert isinstance(validator_keys, list) and validator_keys, (
            f"{surface}: matrix must provide non-empty validator_keys"
        )
        assert all(isinstance(key, str) for key in validator_keys), (
            f"{surface}: validator_keys must be strings"
        )
        assert len(set(validator_keys)) == len(validator_keys), (
            f"{surface}: validator_keys must be unique"
        )
        requirement_count = len(entry["validation_requirements"])
        assert requirement_count == len(validator_keys), (
            f"{surface}: validation_requirements and validator_keys must stay aligned"
        )
        unknown_keys = [key for key in validator_keys if key not in validators]
        assert not unknown_keys, (
            f"{surface}: unsupported validator_keys {unknown_keys}"
        )
    return surfaces


def assert_all_terms(text: str, terms: list[str], message: str) -> None:
    missing = [term for term in terms if term not in text]
    assert not missing, f"{message}: missing {missing}"


def validate_matrix_bound_public_surfaces(
    surfaces: dict[str, dict[str, object]],
    readme: str,
    readiness: str,
    expected_behaviors: str,
    manifest_text: str,
    research_evaluation: str,
) -> None:
    surface_texts = {
        "README.md": readme,
        "references/interview-readiness.md": readiness,
        "tests/expected-behaviors.md": expected_behaviors,
        "skill-pack.json": manifest_text,
        "research-evaluation.md": research_evaluation,
        ".claude-plugin/plugin.json": (
            (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        ),
        ".claude-plugin/marketplace.json": (
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        ),
    }
    for surface, text in surface_texts.items():
        validator_keys = surfaces[surface]["validator_keys"]
        assert isinstance(validator_keys, list), (
            f"{surface}: validator_keys must be a list"
        )
        for validator_key in validator_keys:
            assert isinstance(validator_key, str), (
                f"{surface}: validator key must be a string"
            )
            SURFACE_VALIDATORS[surface][validator_key](text)


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
    assert (ROOT / "research-evaluation.md").exists(), "research-evaluation.md missing"
    assert (ROOT / "tests" / "validate_release_gate_assets.py").exists(), (
        "validate_release_gate_assets.py missing"
    )
    assert (ROOT / ".claude-plugin" / "plugin.json").exists(), (
        ".claude-plugin/plugin.json missing"
    )
    assert (ROOT / ".claude-plugin" / "marketplace.json").exists(), (
        ".claude-plugin/marketplace.json missing"
    )
    public_surface_matrix = load_public_surface_matrix()
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
    manifest_text = (ROOT / "skill-pack.json").read_text(encoding="utf-8")
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
    assert "`new-lesson-package`" in readme, (
        "README missing canonical new-lesson-package workflow id"
    )
    assert "workflows/new-lesson-design.md" in readme, (
        "README missing canonical new-lesson workflow path"
    )
    assert " ".join(["new", "lesson", "design"]) not in readme.lower(), (
        "README still contains legacy new-lesson public label"
    )
    validate_readme_provider_contract(readme)
    assert "grill-me-for-k-teacher\n→ assessment-first-design\n→ lesson-prototype\n→ to-lesson-brief" in readme, (
        "README missing exact canonical new-lesson-package chain"
    )

    workflows_md = (ROOT / "WORKFLOWS.md").read_text(encoding="utf-8")
    assert "Router-first rule" in workflows_md, "WORKFLOWS missing router-first rule"
    assert "to-lesson-brief" in workflows_md, "WORKFLOWS missing final handoff"
    assert "`new-lesson-package`" in workflows_md, (
        "WORKFLOWS missing canonical new-lesson-package workflow id"
    )
    assert "workflows/new-lesson-design.md" in workflows_md, (
        "WORKFLOWS missing canonical new-lesson workflow path"
    )
    assert " ".join(["new", "lesson", "design"]) not in workflows_md.lower(), (
        "WORKFLOWS still contains legacy new-lesson public label"
    )
    for term in [
        "`new-lesson-package`",
        "grill-me-for-k-teacher",
        "assessment-first-design",
        "lesson-prototype",
        "to-lesson-brief",
    ]:
        assert term in workflows_md, f"WORKFLOWS missing canonical new-lesson chain term: {term}"
    assert "grill-me-for-k-teacher\n→ assessment-first-design\n→ lesson-prototype\n→ to-lesson-brief" in workflows_md, (
        "WORKFLOWS missing exact canonical new-lesson-package chain"
    )
    for term in [
        "1. 요청 유형",
        "2. 선택한 workflow",
        "3. 선택 이유",
        "4. 시작할 skill",
        "5. 다음 skill 후보",
        "6. 참여/표상/표현 장벽에 대한 주의점",
        "7. 교사에게 던질 첫 질문",
        "8. readiness 상태 또는 막힌 gate",
    ]:
        assert term in workflows_md, f"WORKFLOWS missing router contract term: {term}"
    new_lesson_workflow = (ROOT / "workflows" / "new-lesson-design.md").read_text(encoding="utf-8")
    for term in [
        "# Workflow: new-lesson-package",
        "lesson-prototype",
        "to-lesson-brief",
        "workflow envelope",
        "lesson-package IR",
    ]:
        assert term in new_lesson_workflow, f"new-lesson workflow doc missing {term}"
    assert "grill-me-for-k-teacher\n→ assessment-first-design\n→ lesson-prototype\n→ to-lesson-brief" in new_lesson_workflow, (
        "new-lesson workflow doc missing exact canonical chain"
    )
    new_lesson_command = (ROOT / "commands" / "new-lesson.md").read_text(encoding="utf-8")
    for term in [
        "# New lesson package",
        "canonical workflow id `new-lesson-package`",
        "lesson-prototype",
        "to-lesson-brief",
    ]:
        assert term in new_lesson_command, f"new-lesson command missing {term}"
    assert "`grill-me-for-k-teacher` → `assessment-first-design` → `lesson-prototype` → `to-lesson-brief`" in new_lesson_command, (
        "new-lesson command missing exact canonical chain"
    )
    manifest = json.loads((ROOT / "skill-pack.json").read_text(encoding="utf-8"))
    assert manifest["entrySkill"] == "k-teacher-workflow-router", (
        "manifest entrySkill mismatch"
    )
    assert (
        manifest["validationCommand"]
        == "python tests/validate_skill_pack.py && python tests/validate_workflow_envelope.py && python tests/validate_lesson_package_ir.py && python tests/validate_backport_marker.py && python tests/validate_renderer_parity.py && python tests/validate_release_gate_assets.py && python tests/validate_public_surface_regressions.py && python tests/validate_provider_skills.py"
    ), "manifest validation command drift"
    release_gate_assets = manifest["releaseGateAssets"]
    assert release_gate_assets["semanticEvalFixture"] == "tests/golden/semantic-eval/valid.json", (
        "manifest semantic-eval fixture drift"
    )
    assert release_gate_assets["semanticEvalDimensions"] == [
        "workflow-selection-quality",
        "pedagogy-quality",
        "rigor-preservation",
        "usability-accessibility",
        "post-verification-curriculum-alignment-quality",
    ], "manifest semantic-eval dimensions drift"
    assert release_gate_assets["deterministicValidatorPrecedence"] == [
        "workflow-envelope",
        "lesson-package-ir",
        "kteacher-backport-marker",
        "renderer-parity",
    ], "manifest deterministic validator precedence drift"
    assert release_gate_assets["observabilityFixture"] == "tests/golden/release-observability/valid.json", (
        "manifest observability fixture drift"
    )
    assert release_gate_assets["observabilityCounters"] == [
        "entry_mode_counts",
        "resume_mode_counts",
        "open_boundary_counts_by_category_output_class",
        "blocked_output_reasons_by_class",
        "backport_enforcement_failures_by_format",
        "udl_vs_differentiated_workflow_entry_counts",
        "public_surface_drift_failures",
    ], "manifest observability counters drift"
    assert release_gate_assets["publicSurfaceDriftPluginMetadata"] == [
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
    ], "manifest plugin metadata drift targets mismatch"
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
    manifest_workflows = {workflow["name"]: workflow for workflow in manifest["workflows"]}
    assert "new-lesson-package" in manifest_workflows, (
        "manifest missing canonical new-lesson-package workflow"
    )
    assert manifest_workflows["new-lesson-package"]["path"] == "workflows/new-lesson-design.md", (
        "manifest new-lesson-package path mismatch"
    )
    assert manifest_workflows["new-lesson-package"]["chain"] == [
        "grill-me-for-k-teacher",
        "assessment-first-design",
        "lesson-prototype",
        "to-lesson-brief",
    ], "manifest new-lesson-package chain mismatch"
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
    assert "new-lesson-package" in router and "Lesson failure recovery" in router, (
        "k-teacher-workflow-router: missing workflow routing recipes"
    )
    assert " ".join(["new", "lesson", "design"]) not in router.lower(), (
        "k-teacher-workflow-router: stale legacy new-lesson public label"
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
    expected_router_workflows = {
        "new-lesson-package": "grill-me-for-k-teacher",
        "verified-curriculum-redesign": "grill-with-curriculum",
        "failure-recovery": "diagnose-lesson-failure",
        "material-architecture-improvement": "improve-lesson-architecture",
        "ai-resilient-assignment": "ai-resilient-assignment-redesign",
        "conceptual-inquiry": "grill-with-curriculum",
        "differentiated-redesign": "diagnose-lesson-failure",
        "assessment-upgrade": "assessment-first-design",
        "pbl-design": "zoom-out-lesson",
        "udl-accessible-redesign": "improve-lesson-architecture",
    }
    for route_name, start_skill in expected_router_workflows.items():
        pattern = rf"Route:\n\n```text\n{re.escape(route_name)}\n```.*?Start:\n\n```text\n{re.escape(start_skill)}\n```"
        assert re.search(pattern, router, re.S), (
            f"k-teacher-workflow-router: missing canonical route/start pair {route_name} -> {start_skill}"
        )
    routing_registry = json.loads(
        (ROOT / "registry" / "routing-gate-registry.json").read_text(encoding="utf-8")
    )
    authority_scope = routing_registry.get("canonical_owner", {}).get("authority_scope", [])
    assert "direct-entry-parity-bootstrap" in authority_scope, (
        "routing-gate-registry: missing direct-entry parity bootstrap authority scope"
    )
    registry_skills = routing_registry["skills"]
    grill_me_direct_entry = registry_skills["grill-me-for-k-teacher"]["direct_entry"]
    assert grill_me_direct_entry["parity_bootstrap_required"], (
        "grill-me-for-k-teacher: direct entry must require parity bootstrap"
    )
    assert grill_me_direct_entry["allowed_workflow_ids"] == ["new-lesson-package"], (
        "grill-me-for-k-teacher: direct entry workflow set drift"
    )
    assert grill_me_direct_entry["selected_workflow_id"] == "new-lesson-package", (
        "grill-me-for-k-teacher: direct entry selected workflow drift"
    )
    curriculum_direct_entry = registry_skills["grill-with-curriculum"]["direct_entry"]
    assert curriculum_direct_entry["parity_bootstrap_required"], (
        "grill-with-curriculum: direct entry must require parity bootstrap"
    )
    assert curriculum_direct_entry["allowed_workflow_ids"] == [
        "verified-curriculum-redesign",
        "conceptual-inquiry",
    ], "grill-with-curriculum: curriculum-grounded direct entry workflow set drift"
    assert curriculum_direct_entry["selected_workflow_id"] is None, (
        "grill-with-curriculum: direct entry must stay disambiguation-bound until workflow attachment"
    )
    assert expected_router_workflows["verified-curriculum-redesign"] == "grill-with-curriculum", (
        "verified-curriculum-redesign: router/direct-entry start skill drift"
    )
    for workflow_id in curriculum_direct_entry["allowed_workflow_ids"]:
        assert expected_router_workflows[workflow_id] == "grill-with-curriculum", (
            f"{workflow_id}: direct entry must share the router-equivalent start skill"
        )
    assert "Route:\n\n```text\nnew-lesson-package" in router, (
        "k-teacher-workflow-router: missing canonical new-lesson route block"
    )
    assert "Start:\n\n```text\ngrill-me-for-k-teacher" in router, (
        "k-teacher-workflow-router: missing canonical new-lesson first hop"
    )
    for term in [
        "## Output format",
        "1. 요청 유형",
        "2. 선택한 workflow",
        "3. 선택 이유",
        "4. 시작할 skill",
        "5. 다음 skill 후보",
        "6. 참여/표상/표현 장벽에 대한 주의점",
        "7. 교사에게 던질 첫 질문",
        "8. readiness 상태 또는 막힌 gate",
    ]:
        assert term in router, f"k-teacher-workflow-router: missing output contract term {term}"
    router_sample = (
        skill_dir("k-teacher-workflow-router") / "examples" / "sample-dialogue.md"
    ).read_text(encoding="utf-8")
    for term in [
        "요청 유형:",
        "선택한 workflow: new-lesson-package",
        "선택 이유:",
        "다음 skill 후보:",
        "참여/표상/표현 장벽에 대한 주의점:",
        "교사에게 던질 첫 질문:",
        "readiness 상태 또는 막힌 gate:",
        "assessment-first-design` → `lesson-prototype` → `to-lesson-brief",
    ]:
        assert term in router_sample, f"k-teacher-workflow-router sample: missing {term}"
    assert "시작할 skill: `grill-me-for-k-teacher`" in router_sample, (
        "k-teacher-workflow-router sample: missing canonical first hop"
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
    validate_readiness_provenance_no_unblock(readiness)
    expected_behaviors = (ROOT / "tests" / "expected-behaviors.md").read_text(
        encoding="utf-8"
    )
    validate_expected_behaviors_provenance_no_unblock(expected_behaviors)
    research_evaluation = (ROOT / "research-evaluation.md").read_text(encoding="utf-8")
    validate_matrix_bound_public_surfaces(
        public_surface_matrix,
        readme,
        readiness,
        expected_behaviors,
        manifest_text,
        research_evaluation,
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

    # Loop ε (M1) — the readiness gate mapping and each SKILL.md v2 block are
    # verified as exact projections of the canonical registry.skills[].gate owner,
    # making the registry the load-bearing source of the gate-profile mapping.
    gate_projection = {}
    for skill_id, entry in registry_skills.items():
        gate = entry["gate"]
        gate_projection[skill_id] = {
            "profile": gate["profile"],
            "stage": gate["active_stage"],
            "labels": ", ".join(gate["fact_routing_labels"]),
            "tier3": gate["tier3_mode"],
        }
    assert set(gate_projection.keys()) == set(SKILLS), (
        "registry.skills gate projection skill set mismatch: "
        f"missing {set(SKILLS) - set(gate_projection.keys())}, "
        f"extra {set(gate_projection.keys()) - set(SKILLS)}"
    )
    for skill in SKILLS:
        assert mapping[skill] == gate_projection[skill], (
            f"{skill}: readiness_gate_v2_mapping.json drifted from canonical registry.skills[].gate\n"
            f"  registry: {gate_projection[skill]}\n"
            f"  mapping:  {mapping[skill]}"
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
        assert actual == gate_projection[skill], (
            f"{skill}: v2 block drifted from canonical registry.skills[].gate\n"
            f"  registry: {gate_projection[skill]}\n"
            f"  actual:   {actual}"
        )

    sample_dialogue_gate_v2 = SAMPLE_DIALOGUE_GATE_V2_PATH.read_text(encoding="utf-8")
    inferred_prompt_match = re.search(
        r"> \*\*추정입니다\.\*\*(?P<body>.*?)> `\[from-curriculum:inferred\]`",
        sample_dialogue_gate_v2,
        re.S,
    )
    assert inferred_prompt_match, (
        "sample-dialogue-gate-v2: missing inferred provenance prompt block"
    )
    inferred_prompt = inferred_prompt_match.group("body")
    assert "신뢰도는 낮습니다" in inferred_prompt, (
        "sample-dialogue-gate-v2: inferred prompt missing low-confidence warning"
    )
    assert "원문 한 줄만 알려주실 수 있을까요?" in inferred_prompt, (
        "sample-dialogue-gate-v2: inferred prompt missing source confirmation request"
    )
    assert not re.search(r">\s+[A-D]\.", inferred_prompt), (
        "sample-dialogue-gate-v2: inferred provenance prompt must not use multiple-choice options"
    )
    assert sample_dialogue_gate_v2.index("[from-curriculum:inferred]") < sample_dialogue_gate_v2.index(
        "[from-curriculum:provided]"
    ), "sample-dialogue-gate-v2: escalation order must remain inferred -> provided"
    assert (
        "`[from-curriculum:inferred]`가 unresolved인 동안에는 downstream-ready handoff / `author-ir` / `render`가 계속 blocked입니다."
        in sample_dialogue_gate_v2
    ), "sample-dialogue-gate-v2: unresolved inferred state must block downstream-ready flow"
    assert (
        "provider가 제공한 원문은 `provider` record에 묶인 read-only input으로만 취급합니다."
        in sample_dialogue_gate_v2
    ), "sample-dialogue-gate-v2: provider input must stay read-only"
    assert (
        "`read_only_input: true`를 유지한 채 provider / provenance / license 중 하나라도 unresolved면 fail-closed로 유지합니다."
        in sample_dialogue_gate_v2
    ), "sample-dialogue-gate-v2: provider contract must stay fail-closed"
    assert (
        "`provider` · `provenance_grade` · `source_reference` · `verification_evidence_type` · `verification_anchor` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input`이 없는 summary 상태만으로는 열지 않습니다."
        in sample_dialogue_gate_v2
    ), "sample-dialogue-gate-v2: clearance evidence must stay record-backed"
    assert (
        "Clearance evidence record: none (`provider` / `provenance_grade` / `source_reference` / `verification_evidence_type` / `verification_anchor` / `source_license.status` / `source_license.license_id` / `source_license.evidence_anchor` / `read_only_input` 없이 summary 상태만으로 downstream-ready를 열지 않음)"
        in sample_dialogue_gate_v2
    ), "sample-dialogue-gate-v2: named context must publish missing clearance evidence"
    assert (
        "curriculum fact의 provenance는 해결되었지만, `provider` · `source_license.status = verified-compatible` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input: true` record를 아직 수집하지 않았으므로 downstream-ready handoff / `author-ir` / `render`는 여전히 blocked입니다."
        in sample_dialogue_gate_v2
    ), "sample-dialogue-gate-v2: provider/license evidence block must remain after provenance escalation"
    assert_all_terms(
        sample_dialogue_gate_v2,
        [
            "Provenance 상태: curriculum/textbook 직접 인용 없음 (unresolved `:inferred` fact 0건)",
            "Downstream-ready 상태: blocked — 이 named context는 transcript handoff 전용이며 `provider` · `provenance_grade` · `source_reference` · `verification_evidence_type` · `verification_anchor` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input` record가 아직 없음",
            "Clearance evidence record: none (`provider` / `provenance_grade` / `source_reference` / `verification_evidence_type` / `verification_anchor` / `source_license.status` / `source_license.license_id` / `source_license.evidence_anchor` / `read_only_input` 없이 summary 상태만으로 downstream-ready를 열지 않음)",
            "Provider cleanup 상태: mixed-revision 또는 source/version/raw→normalized trace 미정리 record는 `quarantined`로 격리하며 downstream-ready handoff / `author-ir` / `render`를 열지 않음",
        ],
        "sample-dialogue-gate-v2 handoff provenance state drift",
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
    # .claude-plugin/plugin.json and marketplace.json are validated for
    # closed-world registry.plugin_projection deep equality (top-level key
    # set/order, every value, author/owner records, keywords/skills/tags
    # order, single-plugin cardinality, source/category, and on-disk skill
    # existence) by the matrix-bound projection validators invoked from
    # validate_matrix_bound_public_surfaces above.
    # ========================================================================

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

    json_mode = "--json" in sys.argv[1:]
    if json_mode:
        print(json.dumps({
            "status": "VALIDATION_OK",
            "public_surface_drift_failures": {
                "README.md": 0,
                "skill-pack.json": 0,
                "plugin_metadata": {
                    ".claude-plugin/plugin.json": 0,
                    ".claude-plugin/marketplace.json": 0,
                },
            },
        }, ensure_ascii=False))
    else:
        print("VALIDATION_OK")


if __name__ == "__main__":
    main()
