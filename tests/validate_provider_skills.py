#!/usr/bin/env python3
"""Closed-world validator for the provider-orchestration skill class (G010).

This second skill class is SEPARATE from the 17 Gate-v2 interview/design skills:
- registry.skills stays exactly 17 and its Gate-v2 projection is unchanged;
- registry.provider_skills + skill-pack.json providerSkills + on-disk
  skills/school-materials/* form a closed-world triad for the new class.

The class holds TWO direct-entry orchestrators, each declaring its OWN dependency
subset. Includes negative mutation regressions: drift any surface or violate the
per-orchestrator dependency contract and the class must fail closed.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "routing-gate-registry.json"
REGISTRY_SCHEMA = ROOT / "schemas" / "routing-gate-registry.schema.json"
SKILL_PACK = ROOT / "skill-pack.json"
SM_DIR = ROOT / "skills" / "school-materials"

EXPECTED = {
    "school-evaluation-plan-to-materials",
    "school-plan-grounding",
    "standard-alignment-verify",
    "assessment-evidence-builder",
    "secondary-material-builder",
    "material-rubric-qa",
    "student-worksheet-builder",
    "individualized-material-package-builder",
}
# Each orchestrator declares its OWN dependency subset (not a shared union).
ORCHESTRATOR_DEPS = {
    "school-evaluation-plan-to-materials": {
        "school-plan-grounding",
        "standard-alignment-verify",
        "assessment-evidence-builder",
        "secondary-material-builder",
        "material-rubric-qa",
    },
    "student-worksheet-builder": {
        "standard-alignment-verify",
        "secondary-material-builder",
        "material-rubric-qa",
    },
    "individualized-material-package-builder": {
        "standard-alignment-verify",
        "secondary-material-builder",
        "material-rubric-qa",
    },
}
REQUIRED_FIELDS = {"skill_id", "skill_path", "type", "direct_entry", "dependencies", "outputs", "fail_closed_boundaries", "workflow_membership"}


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_class(registry: dict, manifest: dict) -> None:
    # 1. registry validates against its schema (provider_skills subschema included).
    schema = load(REGISTRY_SCHEMA)
    errs = sorted(jsonschema.Draft202012Validator(schema).iter_errors(registry), key=lambda e: list(e.path))
    assert_true(not errs, f"registry schema invalid: {errs[0].message if errs else ''}")

    ps = registry["provider_skills"]
    assert_true(ps["ownership"] == "canonical" and ps["skill_class"] == "provider-orchestration", "provider_skills class metadata")

    reg_ids = set(ps["skills"].keys())
    man_ids = {s["name"] for s in manifest["providerSkills"]}
    disk_ids = {p.name for p in SM_DIR.iterdir() if p.is_dir()}

    # 2. Closed-world triad: registry == manifest == on-disk == EXPECTED (now 8).
    assert_true(reg_ids == EXPECTED, f"registry provider_skills set drift: {reg_ids ^ EXPECTED}")
    assert_true(man_ids == EXPECTED, f"skill-pack providerSkills set drift: {man_ids ^ EXPECTED}")
    assert_true(disk_ids == EXPECTED, f"on-disk school-materials set drift: {disk_ids ^ EXPECTED}")

    # 3. Per-skill contract + path existence + SKILL.md; generalized orchestrator handling.
    orchestrators = []
    for sid, entry in ps["skills"].items():
        assert_true(REQUIRED_FIELDS <= set(entry), f"{sid}: missing contract fields {REQUIRED_FIELDS - set(entry)}")
        assert_true((ROOT / entry["skill_path"] / "SKILL.md").exists(), f"{sid}: SKILL.md missing on disk")
        assert_true(len(entry["fail_closed_boundaries"]) >= 1, f"{sid}: must declare fail-closed boundaries")
        if entry["type"] == "orchestrator":
            orchestrators.append(sid)
    assert_true(len(orchestrators) >= 1, "the provider class must have at least one orchestrator")
    for sid in orchestrators:
        assert_true(ps["skills"][sid]["direct_entry"] is True, f"{sid}: an orchestrator must be direct_entry")

    # 4. Per-orchestrator-own-deps: non-empty, no self-dep, each dep is a class id, deps subset of class-minus-self.
    for sid in orchestrators:
        deps = ps["skills"][sid]["dependencies"]
        assert_true(bool(deps), f"{sid}: orchestrator must declare non-empty dependencies")
        assert_true(sid not in deps, f"{sid}: orchestrator may not depend on itself")
        for dep in deps:
            assert_true(dep in EXPECTED, f"{sid}: dependency '{dep}' is not a provider-class skill id")
        assert_true(set(deps) <= (EXPECTED - {sid}), f"{sid}: dependencies must be a subset of the class minus itself")
    # Pin each known orchestrator's exact declared subset (original keeps 5 specialists; worksheet keeps its 3).
    for sid, expected_deps in ORCHESTRATOR_DEPS.items():
        assert_true(sid in orchestrators, f"{sid} must be an orchestrator")
        assert_true(set(ps["skills"][sid]["dependencies"]) == expected_deps, f"{sid}: declared dependency subset drift")

    # 5. Manifest paths match registry paths.
    man_paths = {s["name"]: s["path"] for s in manifest["providerSkills"]}
    for sid, entry in ps["skills"].items():
        assert_true(man_paths[sid] == entry["skill_path"], f"{sid}: manifest path != registry path")

    # 6. Gate-v2 projection untouched: 17 interview skills, repo_facts.skill_count == 17.
    assert_true(registry["repo_facts"]["skill_count"] == 17, "repo_facts.skill_count must stay 17 (interview class)")
    assert_true(len(registry["skills"]) == 17, "registry.skills must stay exactly 17")
    assert_true(len(registry["plugin_projection"]["plugin_json"]["skills"]) == 17, "plugin projection must stay 17-skill")


def positive_orchestrator_case(registry: dict, manifest: dict) -> None:
    """The real registry has exactly three valid own-subset orchestrators and PASSES."""
    validate_class(registry, manifest)
    ps = registry["provider_skills"]["skills"]
    orchestrators = [sid for sid, e in ps.items() if e["type"] == "orchestrator"]
    assert_true(len(orchestrators) == 3, f"expected exactly 3 orchestrators, found {orchestrators}")
    assert_true(set(orchestrators) == set(ORCHESTRATOR_DEPS), "the three orchestrators must be the known set")


def _mutated(base: dict, mutate) -> dict:
    clone = json.loads(json.dumps(base))
    mutate(clone)
    return clone


def negative_regressions(registry: dict, manifest: dict) -> None:
    def expect_fail(reg, man, name):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                validate_class(reg, man)
        except AssertionError:
            return
        raise AssertionError(f"negative regression '{name}' did not fail closed")

    # --- kept surface-drift regressions ---
    expect_fail(_mutated(registry, lambda r: r["provider_skills"]["skills"].pop("material-rubric-qa")), manifest, "registry_drop_skill")
    expect_fail(registry, _mutated(manifest, lambda m: m["providerSkills"].pop()), "manifest_drop_skill")
    expect_fail(_mutated(registry, lambda r: r["provider_skills"]["skills"]["school-plan-grounding"].__setitem__("skill_path", "skills/entry/grill-me-for-k-teacher")), manifest, "registry_path_drift")
    expect_fail(_mutated(registry, lambda r: r["repo_facts"].__setitem__("skill_count", 23)), manifest, "interview_count_drift")

    # --- redesigned per-orchestrator dependency regressions (replaces two_orchestrators, now a valid state) ---
    # 2nd orchestrator declares a dependency that is not a class skill id.
    expect_fail(_mutated(registry, lambda r: r["provider_skills"]["skills"]["student-worksheet-builder"]["dependencies"].append("does-not-exist-skill")), manifest, "orchestrator_declares_nonexistent_dep")
    # An orchestrator with no dependencies at all.
    expect_fail(_mutated(registry, lambda r: r["provider_skills"]["skills"]["student-worksheet-builder"].__setitem__("dependencies", [])), manifest, "orchestrator_missing_deps")
    # A dependency id that no longer matches any class skill after a rename/path drift.
    expect_fail(_mutated(registry, lambda r: r["provider_skills"]["skills"]["student-worksheet-builder"].__setitem__("dependencies", ["standard-alignment-verify", "secondary-material-builder", "material-rubric-qa-renamed"])), manifest, "orchestrator_dependency_drift")
    # An orchestrator listing itself as a dependency.
    expect_fail(_mutated(registry, lambda r: r["provider_skills"]["skills"]["student-worksheet-builder"]["dependencies"].append("student-worksheet-builder")), manifest, "orchestrator_self_dependency")


def main() -> None:
    registry = load(REGISTRY)
    manifest = load(SKILL_PACK)
    validate_class(registry, manifest)
    positive_orchestrator_case(registry, manifest)
    negative_regressions(registry, manifest)
    print("PASS validate_provider_skills")
    print("- provider-orchestration class closed-world: registry.provider_skills == skill-pack.providerSkills == on-disk (8)")
    print("- three direct-entry orchestrators, each with its OWN dependency subset (own-subset validation)")
    print("- per-skill contract (type/direct_entry/deps/outputs/fail_closed/workflow) + SKILL.md present")
    print("- Gate-v2 interview class untouched: registry.skills==17, repo_facts.skill_count==17, plugin projection 17")
    print("- positive 3-orchestrator case passes; negatives fail closed (drop/path-drift/count-bump +")
    print("  nonexistent-dep / missing-deps / dependency-drift / self-dependency)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
