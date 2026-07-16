#!/usr/bin/env python3
"""Closed-world validator for the provider-orchestration skill class (G010).

This second skill class is SEPARATE from the 17 Gate-v2 interview/design skills:
- registry.skills stays exactly 17 and its Gate-v2 projection is unchanged;
- registry.provider_skills + skill-pack.json providerSkills + on-disk
  skills/school-materials/* form a closed-world triad for the new class.

Includes negative mutation regressions: drift any surface and the class must fail closed.
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

    # 2. Closed-world triad: registry == manifest == on-disk == EXPECTED.
    assert_true(reg_ids == EXPECTED, f"registry provider_skills set drift: {reg_ids ^ EXPECTED}")
    assert_true(man_ids == EXPECTED, f"skill-pack providerSkills set drift: {man_ids ^ EXPECTED}")
    assert_true(disk_ids == EXPECTED, f"on-disk school-materials set drift: {disk_ids ^ EXPECTED}")

    # 3. Per-skill contract + path existence + SKILL.md.
    orchestrators = 0
    for sid, entry in ps["skills"].items():
        assert_true(REQUIRED_FIELDS <= set(entry), f"{sid}: missing contract fields {REQUIRED_FIELDS - set(entry)}")
        assert_true((ROOT / entry["skill_path"] / "SKILL.md").exists(), f"{sid}: SKILL.md missing on disk")
        assert_true(len(entry["fail_closed_boundaries"]) >= 1, f"{sid}: must declare fail-closed boundaries")
        if entry["type"] == "orchestrator":
            orchestrators += 1
    assert_true(orchestrators == 1, "exactly one orchestrator in the provider class")

    # 4. Orchestrator depends on all specialists (workflow coherence).
    orch = ps["skills"]["school-evaluation-plan-to-materials"]
    specialists = EXPECTED - {"school-evaluation-plan-to-materials"}
    assert_true(set(orch["dependencies"]) == specialists, "orchestrator must depend on all specialists")

    # 5. Manifest paths match registry paths.
    man_paths = {s["name"]: s["path"] for s in manifest["providerSkills"]}
    for sid, entry in ps["skills"].items():
        assert_true(man_paths[sid] == entry["skill_path"], f"{sid}: manifest path != registry path")

    # 6. Gate-v2 projection untouched: 17 interview skills, repo_facts.skill_count == 17.
    assert_true(registry["repo_facts"]["skill_count"] == 17, "repo_facts.skill_count must stay 17 (interview class)")
    assert_true(len(registry["skills"]) == 17, "registry.skills must stay exactly 17")
    assert_true(len(registry["plugin_projection"]["plugin_json"]["skills"]) == 17, "plugin projection must stay 17-skill")


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

    # drop a provider skill from the registry
    expect_fail(_mutated(registry, lambda r: r["provider_skills"]["skills"].pop("material-rubric-qa")), manifest, "registry_drop_skill")
    # drop a provider skill from the manifest
    expect_fail(registry, _mutated(manifest, lambda m: m["providerSkills"].pop()), "manifest_drop_skill")
    # drift a registry skill_path
    expect_fail(_mutated(registry, lambda r: r["provider_skills"]["skills"]["school-plan-grounding"].__setitem__("skill_path", "skills/entry/grill-me-for-k-teacher")), manifest, "registry_path_drift")
    # bump interview skill_count (Gate-v2 class must stay 17)
    expect_fail(_mutated(registry, lambda r: r["repo_facts"].__setitem__("skill_count", 23)), manifest, "interview_count_drift")
    # two orchestrators
    expect_fail(_mutated(registry, lambda r: r["provider_skills"]["skills"]["material-rubric-qa"].__setitem__("type", "orchestrator")), manifest, "two_orchestrators")


def main() -> None:
    registry = load(REGISTRY)
    manifest = load(SKILL_PACK)
    validate_class(registry, manifest)
    negative_regressions(registry, manifest)
    print("PASS validate_provider_skills")
    print("- provider-orchestration class closed-world: registry.provider_skills == skill-pack.providerSkills == on-disk (6)")
    print("- per-skill contract (type/direct_entry/deps/outputs/fail_closed/workflow) + SKILL.md present")
    print("- Gate-v2 interview class untouched: registry.skills==17, repo_facts.skill_count==17, plugin projection 17")
    print("- negative mutation regressions fail closed (drop/path-drift/count-bump/two-orchestrators)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
