from __future__ import annotations

import copy
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_DIR = ROOT / "tests" / "golden" / "semantic-eval"
OBS_DIR = ROOT / "tests" / "golden" / "release-observability"
APPROVAL_STATE_DIR = ROOT / "tests" / "golden" / "approval-state"
EXPECTED_VALIDATORS = [
    "workflow-envelope",
    "lesson-package-ir",
    "kteacher-backport-marker",
    "renderer-parity",
]
EXPECTED_DIMENSIONS = [
    "workflow-selection-quality",
    "pedagogy-quality",
    "rigor-preservation",
    "usability-accessibility",
    "post-verification-curriculum-alignment-quality",
]
EXPECTED_COUNTER_KEYS = [
    "entry_mode_counts",
    "resume_mode_counts",
    "open_boundary_counts_by_category_output_class",
    "blocked_output_reasons_by_class",
    "backport_enforcement_failures_by_format",
    "udl_vs_differentiated_workflow_entry_counts",
    "public_surface_drift_failures",
]
EXPECTED_OUTPUT_CLASSES = {"handoff", "author-ir", "render"}
EXPECTED_BACKPORT_FORMATS = ["hwpx", "docx", "html"]
EXPECTED_PLUGIN_METADATA_KEYS = {
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
}
EXPECTED_WORKFLOW_ENTRY_KEYS = {
    "udl-accessible-redesign",
    "differentiated-redesign",
}
DETERMINISTIC_COMMANDS = {
    "workflow-envelope": ["python3", "tests/validate_workflow_envelope.py", "--json"],
    "lesson-package-ir": ["python3", "tests/validate_lesson_package_ir.py", "--json"],
    "kteacher-backport-marker": ["python3", "tests/validate_backport_marker.py", "--json"],
    "renderer-parity": ["python3", "tests/validate_renderer_parity.py", "--json"],
}
PUBLIC_SURFACE_COMMAND = ["python3", "tests/validate_skill_pack.py", "--json"]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_count_map(payload: dict[str, object], case_name: str, label: str) -> None:
    assert_true(isinstance(payload, dict) and payload, f"{case_name}: {label} must be a non-empty object")
    for key, value in payload.items():
        assert_true(isinstance(key, str) and key, f"{case_name}: {label} keys must be non-empty strings")
        assert_true(isinstance(value, int) and value >= 0, f"{case_name}: {label}.{key} must be a non-negative integer")


def run_json_command(command: list[str]) -> dict:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(completed.stdout)


def run_deterministic_validators() -> dict[str, dict]:
    outputs: dict[str, dict] = {}
    for name, command in DETERMINISTIC_COMMANDS.items():
        outputs[name] = run_json_command(command)
    return outputs


def derive_observability_snapshot(deterministic_outputs: dict[str, dict], public_surface_output: dict) -> dict[str, object]:
    approval_payloads = [load_json(path) for path in sorted(APPROVAL_STATE_DIR.glob("*.json"))]

    entry_mode_counts: Counter[str] = Counter()
    resume_mode_counts: Counter[str] = Counter()
    open_boundary_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    blocked_reasons: defaultdict[str, Counter[str]] = defaultdict(Counter)

    for payload in approval_payloads:
        entry_mode = payload["entry_mode"]
        entry_mode_counts[entry_mode] += 1
        resume_mode_counts["resume" if entry_mode == "resume" else "non_resume"] += 1

        boundaries = payload.get("teacher_judgment_boundaries", [])
        for boundary in boundaries:
            if boundary.get("resolution", {}).get("status") != "open":
                continue
            category = boundary["category"]
            for output_class in boundary.get("affected_output_classes", []):
                open_boundary_counts[category][output_class] += 1

        approval_state = payload["approval_state"]
        for output_class, allowed in {
            "handoff": approval_state.get("can_handoff", False),
            "author-ir": approval_state.get("can_author_ir", False),
            "render": approval_state.get("can_render", False),
        }.items():
            if allowed:
                continue
            reason = "missing_clearance_evidence"
            if any(
                boundary.get("resolution", {}).get("status") == "open"
                and output_class in boundary.get("affected_output_classes", [])
                for boundary in boundaries
            ):
                reason = "teacher_judgment_open"
            elif ":inferred" in payload.get("curriculum_context", {}).get("never_unblock_sources", []) and not payload.get("curriculum_context", {}).get("records"):
                reason = "unresolved_inferred"
            blocked_reasons[output_class][reason] += 1

    backport_failures_by_format = {
        renderer_format: len(deterministic_outputs["kteacher-backport-marker"]["format_drift_cases_by_format"][renderer_format])
        + len(deterministic_outputs["renderer-parity"]["format_drift_cases_by_format"][renderer_format])
        for renderer_format in EXPECTED_BACKPORT_FORMATS
    }

    manifest = load_json(ROOT / "skill-pack.json")
    workflow_names = {workflow["name"] for workflow in manifest["workflows"]}
    workflow_entry_counts = {
        "udl-accessible-redesign": 1 if "udl-accessible-redesign" in workflow_names else 0,
        "differentiated-redesign": 1 if "differentiated-redesign" in workflow_names else 0,
    }

    assert_true(public_surface_output.get("status") == "VALIDATION_OK", "public surface validation output drift")
    public_surface_drift_failures = public_surface_output["public_surface_drift_failures"]

    return {
        "entry_mode_counts": dict(entry_mode_counts),
        "resume_mode_counts": dict(resume_mode_counts),
        "open_boundary_counts_by_category_output_class": {category: dict(counts) for category, counts in open_boundary_counts.items()},
        "blocked_output_reasons_by_class": {output_class: dict(counts) for output_class, counts in blocked_reasons.items()},
        "backport_enforcement_failures_by_format": backport_failures_by_format,
        "udl_vs_differentiated_workflow_entry_counts": workflow_entry_counts,
        "public_surface_drift_failures": public_surface_drift_failures,
    }


def validate_semantic_eval_fixture(payload: dict, case_name: str, deterministic_outputs: dict[str, dict]) -> None:
    assert_true(payload.get("release_gate") == "semantic-eval", f"{case_name}: release_gate drift")
    precedence = payload.get("deterministic_precedence")
    assert_true(isinstance(precedence, dict), f"{case_name}: deterministic_precedence missing")
    assert_true(precedence.get("blocking_validators") == EXPECTED_VALIDATORS, f"{case_name}: blocking_validators drift")
    assert_true(precedence.get("semantic_eval_runs_only_after") == "all_pass", f"{case_name}: semantic_eval_runs_only_after drift")
    assert_true(precedence.get("semantic_eval_can_override") is False, f"{case_name}: semantic_eval_can_override drift")
    assert_true(payload.get("dimensions") == EXPECTED_DIMENSIONS, f"{case_name}: semantic dimensions drift")
    assert_true(set(deterministic_outputs.keys()) == set(EXPECTED_VALIDATORS), f"{case_name}: deterministic runtime coverage drift")
    assert_true(deterministic_outputs["workflow-envelope"]["status"] == "VALIDATION_OK", f"{case_name}: workflow-envelope prerequisite drift")
    assert_true(deterministic_outputs["workflow-envelope"]["fixture_count"] == 8, f"{case_name}: workflow-envelope fixture coverage drift")
    assert_true(deterministic_outputs["workflow-envelope"]["regression_case_count"] == 22, f"{case_name}: workflow-envelope regression coverage drift")
    assert_true(deterministic_outputs["lesson-package-ir"]["status"] == "VALIDATION_OK", f"{case_name}: lesson-package-ir prerequisite drift")
    assert_true(deterministic_outputs["lesson-package-ir"]["case_count"] == 22, f"{case_name}: lesson-package-ir case coverage drift")
    assert_true(deterministic_outputs["kteacher-backport-marker"]["status"] == "VALIDATION_OK", f"{case_name}: backport-marker prerequisite drift")
    assert_true(deterministic_outputs["renderer-parity"]["status"] == "VALIDATION_OK", f"{case_name}: renderer-parity prerequisite drift")

    failure_example = payload.get("failure_example")
    assert_true(isinstance(failure_example, dict), f"{case_name}: failure_example missing")
    deterministic_failure = failure_example.get("deterministic_failure")
    assert_true(isinstance(deterministic_failure, dict), f"{case_name}: deterministic_failure missing")
    assert_true(deterministic_failure.get("validator") in EXPECTED_VALIDATORS, f"{case_name}: failure_example validator drift")
    assert_true(deterministic_failure.get("semantic_eval_status") == "skipped", f"{case_name}: failure_example semantic_eval_status drift")
    assert_true(deterministic_failure.get("release_decision") == "blocked", f"{case_name}: failure_example release_decision drift")


def validate_observability_fixture(payload: dict, case_name: str, expected_snapshot: dict[str, object]) -> None:
    assert_true(payload.get("release_gate") == "release-observability", f"{case_name}: release_gate drift")
    counters = payload.get("counters")
    assert_true(isinstance(counters, dict), f"{case_name}: counters missing")
    assert_true(set(counters.keys()) == set(EXPECTED_COUNTER_KEYS), f"{case_name}: counter key set drift")

    assert_count_map(counters["entry_mode_counts"], case_name, "entry_mode_counts")
    assert_count_map(counters["resume_mode_counts"], case_name, "resume_mode_counts")

    boundary_counts = counters["open_boundary_counts_by_category_output_class"]
    assert_true(isinstance(boundary_counts, dict) and boundary_counts, f"{case_name}: open_boundary_counts_by_category_output_class missing")
    for category, by_output in boundary_counts.items():
        assert_true(isinstance(category, str) and category, f"{case_name}: boundary category keys must be non-empty strings")
        assert_count_map(by_output, case_name, f"open_boundary_counts_by_category_output_class.{category}")
        assert_true(set(by_output).issubset(EXPECTED_OUTPUT_CLASSES), f"{case_name}: boundary output class drift under {category}")

    blocked_reasons = counters["blocked_output_reasons_by_class"]
    assert_true(isinstance(blocked_reasons, dict) and blocked_reasons, f"{case_name}: blocked_output_reasons_by_class missing")
    assert_true(set(blocked_reasons).issubset(EXPECTED_OUTPUT_CLASSES), f"{case_name}: blocked output class drift")
    for output_class, reason_counts in blocked_reasons.items():
        assert_count_map(reason_counts, case_name, f"blocked_output_reasons_by_class.{output_class}")

    backport_failures = counters["backport_enforcement_failures_by_format"]
    assert_true(set(backport_failures.keys()) == set(EXPECTED_BACKPORT_FORMATS), f"{case_name}: backport format set drift")
    assert_count_map(backport_failures, case_name, "backport_enforcement_failures_by_format")

    workflow_entry_counts = counters["udl_vs_differentiated_workflow_entry_counts"]
    assert_true(set(workflow_entry_counts.keys()) == EXPECTED_WORKFLOW_ENTRY_KEYS, f"{case_name}: workflow entry keys drift")
    assert_count_map(workflow_entry_counts, case_name, "udl_vs_differentiated_workflow_entry_counts")

    drift_failures = counters["public_surface_drift_failures"]
    assert_true(isinstance(drift_failures, dict) and drift_failures, f"{case_name}: public_surface_drift_failures missing")
    plugin_metadata = drift_failures.get("plugin_metadata")
    assert_true(isinstance(plugin_metadata, dict), f"{case_name}: plugin_metadata drift counters missing")
    assert_true(set(plugin_metadata.keys()) == EXPECTED_PLUGIN_METADATA_KEYS, f"{case_name}: plugin_metadata key drift")
    assert_count_map(plugin_metadata, case_name, "public_surface_drift_failures.plugin_metadata")
    for surface_name in ["README.md", "skill-pack.json"]:
        value = drift_failures.get(surface_name)
        assert_true(isinstance(value, int) and value >= 0, f"{case_name}: {surface_name} drift count missing")

    assert_true(counters == expected_snapshot, f"{case_name}: counters no longer reconcile with current approval fixtures, structured validator summaries, and public-surface validation")


def expect_failure(check, payload: dict, case_name: str, extra: object) -> None:
    try:
        check(payload, case_name, extra)
    except AssertionError:
        return
    raise AssertionError(f"{case_name}: expected rejection")


def main() -> None:
    deterministic_outputs = run_deterministic_validators()
    public_surface_output = run_json_command(PUBLIC_SURFACE_COMMAND)
    semantic_valid = load_json(SEMANTIC_DIR / "valid.json")
    semantic_missing_precedence = load_json(SEMANTIC_DIR / "missing-deterministic-precedence.json")
    semantic_missing_dimension = load_json(SEMANTIC_DIR / "missing-dimension.json")
    observability_valid = load_json(OBS_DIR / "valid.json")
    observability_missing_counter = load_json(OBS_DIR / "missing-counter.json")
    observability_missing_plugin = load_json(OBS_DIR / "missing-plugin-metadata.json")
    observability_nonzero_public_surface = load_json(OBS_DIR / "nonzero-public-surface-drift.json")
    expected_observability = derive_observability_snapshot(deterministic_outputs, public_surface_output)

    validate_semantic_eval_fixture(semantic_valid, "semantic_valid", deterministic_outputs)
    expect_failure(validate_semantic_eval_fixture, semantic_missing_precedence, "semantic_missing_deterministic_precedence", deterministic_outputs)
    expect_failure(validate_semantic_eval_fixture, semantic_missing_dimension, "semantic_missing_dimension", deterministic_outputs)
    validate_observability_fixture(observability_valid, "observability_valid", expected_observability)
    synthetic_public_surface_drift = copy.deepcopy(expected_observability)
    synthetic_public_surface_drift["public_surface_drift_failures"] = {
        "README.md": 1,
        "skill-pack.json": 1,
        "plugin_metadata": {
            ".claude-plugin/plugin.json": 1,
            ".claude-plugin/marketplace.json": 1,
        },
    }
    validate_observability_fixture(observability_nonzero_public_surface, "observability_nonzero_public_surface", synthetic_public_surface_drift)
    expect_failure(validate_observability_fixture, observability_missing_counter, "observability_missing_counter", expected_observability)
    expect_failure(validate_observability_fixture, observability_missing_plugin, "observability_missing_plugin_metadata", expected_observability)

    print("validated 7 release-gate asset cases")
    print("- semantic_valid: semantic eval runs only after the current deterministic validator lane passes and publishes the exact five quality dimensions")
    print("- semantic_missing_deterministic_precedence: release gate rejects semantic-eval assets missing renderer-parity-aware deterministic precedence")
    print("- semantic_missing_dimension: release gate rejects semantic-eval assets missing a required evaluation dimension")
    print("- observability_valid: release observability reconciles required counters against current approval fixtures, structured validator summaries, and exact plugin metadata drift targets")
    print("- observability_nonzero_public_surface: release observability accepts explicit non-zero README/skill-pack/plugin drift counts when the structured snapshot demands them")
    print("- observability_missing_counter: release gate rejects observability assets missing a required counter family")
    print("- observability_missing_plugin_metadata: release gate rejects observability assets that stop reporting exact plugin metadata drift buckets")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
