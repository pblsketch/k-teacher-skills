from __future__ import annotations

import copy
import json
import sys
from datetime import datetime
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "workflow-envelope.schema.json"
FIXTURE_DIR = ROOT / "tests" / "golden" / "approval-state"
EXPECTED_FIXTURE_BASELINES = {
    "context_only.json": {
        "handoff_mode": "context-only",
        "can_continue_judgment_only": True,
        "can_handoff": True,
        "can_author_ir": False,
        "can_render": False,
    },
    "blocked_handoff.json": {
        "handoff_mode": "blocked",
        "can_continue_judgment_only": False,
        "can_handoff": False,
        "can_author_ir": False,
        "can_render": False,
    },
    "downstream_ready.json": {
        "handoff_mode": "downstream-ready",
        "can_continue_judgment_only": False,
        "can_handoff": True,
        "can_author_ir": True,
        "can_render": True,
    },
}
DIRECT_ENTRY_GATE_PARITY = {
    "new-lesson-package": {
        "profile": "Standard",
        "threshold": 0.2,
        "threshold_source": "skill-default",
        "active_stage": "Stage 1 · Intent-first",
        "fact_routing_labels": [
            "from-curriculum",
            "from-textbook",
            "from-class-context",
            "from-teacher-judgment",
        ],
        "tier3_mode": "enabled",
    },
    "verified-curriculum-redesign": {
        "profile": "Deep",
        "threshold": 0.15,
        "threshold_source": "skill-default",
        "active_stage": "Stage 1+3 · Curriculum-grounded",
        "fact_routing_labels": [
            "from-curriculum",
            "from-textbook",
            "from-teacher-judgment",
        ],
        "tier3_mode": "enabled",
    },
    "conceptual-inquiry": {
        "profile": "Deep",
        "threshold": 0.15,
        "threshold_source": "skill-default",
        "active_stage": "Stage 1+3 · Curriculum-grounded",
        "fact_routing_labels": [
            "from-curriculum",
            "from-textbook",
            "from-teacher-judgment",
        ],
        "tier3_mode": "enabled",
    },
}
CURRICULUM_GROUNDED_WORKFLOWS = {"verified-curriculum-redesign", "conceptual-inquiry"}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_schema_contract(schema: dict) -> None:
    comment = schema.get("$comment", "")
    assert_true("only owner" in comment and "No separate approval schema owner" in comment, "schema freeze comment missing approval ownership rule")

    defs = schema.get("$defs", {})
    approval_state = defs.get("approvalState", {})
    handoff_enum = approval_state.get("properties", {}).get("handoff_mode", {}).get("enum")
    assert_true(handoff_enum == ["context-only", "downstream-ready", "blocked"], "handoff_mode enum mismatch")
    revision_schema = schema.get("properties", {}).get("workflow_envelope_revision_id", {})
    assert_true(revision_schema.get("pattern") == "^env-[0-9]{4,}$", "workflow_envelope_revision_id pattern mismatch")

    provider_status_enum = defs.get("providerCapabilityContract", {}).get("properties", {}).get("provider_status", {}).get("enum")
    assert_true(
        provider_status_enum == ["available", "quarantined", "unavailable", "unknown"],
        "provider_status enum must publish explicit quarantine state",
    )
    verification_status_enum = defs.get("providerCapabilityContract", {}).get("properties", {}).get("verification_status", {}).get("enum")
    assert_true(
        verification_status_enum == ["complete", "quarantined", "missing"],
        "verification_status enum must publish explicit quarantine state",
    )
    provider_contract_state_enum = defs.get("envelopeAuthority", {}).get("properties", {}).get("provider_contract_state", {}).get("enum")
    assert_true(
        provider_contract_state_enum == ["available", "quarantined", "unavailable", "unknown"],
        "approval_state.envelope_authority.provider_contract_state must publish explicit quarantine state",
    )
    curriculum_context = schema.get("properties", {}).get("curriculum_context", {}).get("properties", {})
    assert_true(
        curriculum_context.get("unblock_sources_allowed", {}).get("$ref") == "#/$defs/registryOwnedUnblockSourcesAllowed",
        "curriculum_context.unblock_sources_allowed must be registry-owned",
    )
    assert_true(
        curriculum_context.get("never_unblock_sources", {}).get("$ref") == "#/$defs/registryOwnedNeverUnblockSet",
        "curriculum_context.never_unblock_sources must be registry-owned",
    )
    record_items = curriculum_context.get("records", {}).get("items", {})
    assert_true(
        record_items.get("$ref") == "#/$defs/curriculumProviderRecord",
        "curriculum_context.records must use the canonical curriculumProviderRecord interface",
    )
    provider_record_required = set(defs.get("curriculumProviderRecord", {}).get("required", []))
    assert_true(
        {"provider", "provenance_grade", "verification_status", "source_license", "read_only_input"}.issubset(provider_record_required),
        "curriculumProviderRecord must require provider/provenance/license/read-only fields",
    )

    approval_record = defs.get("approvalRecord", {})
    approval_required = set(approval_record.get("required", []))
    assert_true(
        {"approval_id", "boundary_id", "decision", "decided_by", "decided_at", "confirmation_anchor", "supporting_evidence"}.issubset(approval_required),
        "approval record minimum fields are incomplete",
    )

    approval_comment = approval_record.get("$comment", "")
    assert_true("no separate approval artifact namespace" in approval_comment, "approval record namespace freeze missing")

    confirmation_anchor = defs.get("teacherConfirmationAnchor", {})
    anchor_comment = confirmation_anchor.get("$comment", "")
    assert_true("transcript or handoff references" in anchor_comment, "teacher confirmation anchor contract drift")

    approvals_comment = schema.get("properties", {}).get("approvals", {}).get("$comment", "")
    assert_true(
        "temporal supersession" in approvals_comment and "semantic validator" in approvals_comment,
        "approvals property must document the schema/semantic supersession responsibility split",
    )


def is_curriculum_grounded(envelope: dict) -> bool:
    return envelope["workflow_type"] in CURRICULUM_GROUNDED_WORKFLOWS


def validate_parity_bootstrap_semantics(envelope: dict, fixture_name: str) -> None:
    bootstrap = envelope["parity_bootstrap"]
    assert_true(
        bootstrap["selected_workflow"] == envelope["workflow_type"],
        f"{fixture_name}: parity bootstrap must stay attached to workflow_type",
    )

    if envelope["entry_mode"] in {"direct-skill", "resume"}:
        assert_true(bootstrap["required"], f"{fixture_name}: {envelope['entry_mode']} must require parity bootstrap")
        assert_true(bootstrap["completed"], f"{fixture_name}: {envelope['entry_mode']} must complete parity bootstrap")

    if envelope["entry_mode"] != "direct-skill":
        return

    expected_gate = DIRECT_ENTRY_GATE_PARITY.get(envelope["workflow_type"])
    if expected_gate is None:
        return

    gate = envelope["gate_v2"]
    for key, value in expected_gate.items():
        assert_true(gate[key] == value, f"{fixture_name}: direct entry must reconstruct router-equivalent gate_v2.{key}")


def validate_curriculum_grounded_fail_closed(envelope: dict, fixture_name: str) -> None:
    if not is_curriculum_grounded(envelope):
        return

    state = envelope["approval_state"]
    curriculum = envelope["curriculum_context"]
    if state["handoff_mode"] == "downstream-ready" or state["can_author_ir"] or state["can_render"]:
        assert_true(curriculum["status"] == "verified", f"{fixture_name}: curriculum-grounded downstream flow requires verified curriculum_context")
        assert_true(bool(curriculum["records"]), f"{fixture_name}: curriculum-grounded downstream flow requires curriculum provider records")

def validate_with_jsonschema(schema: dict, envelope: dict, fixture_name: str) -> None:
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(envelope), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "<root>"
        raise AssertionError(f"{fixture_name}: schema validation failed at {path}: {first.message}")


def expect_schema_rejection(schema: dict, envelope: dict, case_name: str) -> None:
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(envelope), key=lambda error: list(error.path))
    assert_true(bool(errors), f"{case_name}: expected schema rejection")

def parse_iso8601(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise AssertionError(f"invalid iso8601 timestamp: {value}") from error


def recompute_latest_valid_approval(rows: list, fixture_name: str, boundary_id: str) -> dict:
    ordered = sorted(rows, key=lambda approval: parse_iso8601(approval["decided_at"]))
    latest_at = parse_iso8601(ordered[-1]["decided_at"])
    tied = [
        approval for approval in ordered
        if parse_iso8601(approval["decided_at"]) == latest_at
    ]
    assert_true(
        len(tied) == 1,
        f"{fixture_name}: boundary {boundary_id} has {len(tied)} approvals sharing the latest "
        f"decided_at {ordered[-1]['decided_at']}; equal-timestamp supersession is ambiguous and fails closed",
    )
    return ordered[-1]


def validate_boundary_approval_supersession(envelope: dict, fixture_name: str) -> None:
    approvals_by_boundary: dict[str, list] = {}
    for approval in envelope["approvals"]:
        approvals_by_boundary.setdefault(approval["boundary_id"], []).append(approval)

    winners = {
        boundary_id: recompute_latest_valid_approval(rows, fixture_name, boundary_id)
        for boundary_id, rows in approvals_by_boundary.items()
    }

    for boundary in envelope["teacher_judgment_boundaries"]:
        resolution = boundary["resolution"]
        teacher_confirmation = resolution["teacher_confirmation"]
        if not teacher_confirmation["confirmed"]:
            continue
        approval_record = resolution.get("approval_record")
        if approval_record is None:
            continue
        boundary_id = boundary["boundary_id"]
        winner = winners.get(boundary_id)
        assert_true(
            winner is not None,
            f"{fixture_name}: confirmed boundary {boundary_id} has no in-envelope approval history",
        )
        assert_true(
            approval_record["approval_id"] == winner["approval_id"],
            f"{fixture_name}: boundary {boundary_id} resolution references superseded approval "
            f"{approval_record['approval_id']}; the latest '{winner['decision']}' approval "
            f"{winner['approval_id']} at {winner['decided_at']} wins",
        )
        assert_true(
            winner["decision"] == "approved",
            f"{fixture_name}: boundary {boundary_id} latest approval decision '{winner['decision']}' "
            f"cannot keep a confirmed clearance (fail-closed temporal supersession)",
        )


def validate_same_envelope_semantics(envelope: dict, fixture_name: str) -> None:
    assert_true("approval_artifacts" not in envelope, f"{fixture_name}: separate approval artifact namespace is forbidden")

    boundaries = envelope["teacher_judgment_boundaries"]
    approvals = envelope["approvals"]
    boundary_ids = [boundary["boundary_id"] for boundary in boundaries]
    approval_ids = [approval["approval_id"] for approval in approvals]
    assert_true(len(boundary_ids) == len(set(boundary_ids)), f"{fixture_name}: duplicate boundary_id")
    assert_true(len(approval_ids) == len(set(approval_ids)), f"{fixture_name}: duplicate approval_id")

    boundary_by_id = {boundary["boundary_id"]: boundary for boundary in boundaries}

    for approval in approvals:
        assert_true(approval["boundary_id"] in boundary_by_id, f"{fixture_name}: approval references unknown boundary")
        assert_true(approval["decided_by"]["actor_type"] == "teacher", f"{fixture_name}: approvals must be decided by teacher")
        parse_iso8601(approval["decided_at"])
        assert_true(approval["confirmation_anchor"]["carrier"] != "approval-record", f"{fixture_name}: approval confirmation anchors may not recurse through approval-record")

    for boundary in boundaries:
        resolution = boundary["resolution"]
        teacher_confirmation = resolution["teacher_confirmation"]
        anchor = teacher_confirmation["confirmation_anchor"]
        assert_true("supporting_evidence" in resolution, f"{fixture_name}: boundaries must carry supporting_evidence field")

        if teacher_confirmation["confirmed"]:
            assert_true(anchor["carrier"] != "null", f"{fixture_name}: confirmed boundary is missing confirmation anchor")
            assert_true("approval_record" in resolution, f"{fixture_name}: resolved boundary must carry approval_record summary")
            assert_true(resolution["approval_record"]["boundary_id"] == boundary["boundary_id"], f"{fixture_name}: resolution approval_record must stay on the same boundary")
            match = [approval for approval in approvals if approval["approval_id"] == resolution["approval_record"]["approval_id"]]
            assert_true(len(match) == 1, f"{fixture_name}: resolved boundary approval summary must match exactly one approval row")
            approval = match[0]
            assert_true(approval["boundary_id"] == resolution["approval_record"]["boundary_id"], f"{fixture_name}: approval summary boundary_id drift")
            assert_true(approval["decision"] == resolution["approval_record"]["decision"], f"{fixture_name}: approval summary decision drift")
            assert_true(approval["confirmation_anchor"] == teacher_confirmation["confirmation_anchor"], f"{fixture_name}: approval summary confirmation anchor drift")
            assert_true(approval["supporting_evidence"] == resolution["supporting_evidence"], f"{fixture_name}: approval summary supporting_evidence drift")
        else:
            assert_true(anchor["carrier"] == "null", f"{fixture_name}: unconfirmed boundary must stay null-anchored")

    validate_boundary_approval_supersession(envelope, fixture_name)

def expect_semantic_rejection(envelope: dict, case_name: str) -> None:
    try:
        validate_same_envelope_semantics(envelope, case_name)
        validate_parity_bootstrap_semantics(envelope, case_name)
        validate_declared_output_fail_closed(envelope, case_name)
        validate_curriculum_grounded_fail_closed(envelope, case_name)
    except AssertionError:
        return
    raise AssertionError(f"{case_name}: expected semantic validation to reject payload")


def collect_open_hard_affected_outputs(envelope: dict) -> set[str]:
    return {
        output_class
        for boundary in envelope["teacher_judgment_boundaries"]
        if boundary["blocking_severity"] == "hard"
        and boundary["resolution"]["status"] == "open"
        for output_class in boundary["affected_output_classes"]
    }


def validate_declared_output_fail_closed(envelope: dict, fixture_name: str) -> None:
    state = envelope["approval_state"]
    affected_outputs = collect_open_hard_affected_outputs(envelope)

    if "handoff" in affected_outputs:
        assert_true(state["handoff_mode"] != "downstream-ready", f"{fixture_name}: downstream-ready must fail closed on open hard handoff boundaries")
        assert_true(not state["can_handoff"], f"{fixture_name}: can_handoff must fail closed on open hard handoff boundaries")

    if "author-ir" in affected_outputs:
        assert_true(not state["can_author_ir"], f"{fixture_name}: can_author_ir must fail closed on open hard author-ir boundaries")

    if "render" in affected_outputs:
        assert_true(not state["can_render"], f"{fixture_name}: can_render must fail closed on open hard render boundaries")


def expect_fail_closed_regression(schema: dict, envelope: dict, case_name: str) -> None:
    validate_same_envelope_semantics(envelope, case_name)
    expect_schema_rejection(schema, envelope, case_name)


def validate_fixture_expectations(envelope: dict, fixture_name: str) -> None:
    expected = EXPECTED_FIXTURE_BASELINES.get(fixture_name)
    state = envelope["approval_state"]
    if expected is not None:
        for key, value in expected.items():
            assert_true(state[key] == value, f"{fixture_name}: approval_state.{key} mismatch")

    handoff_mode = state["handoff_mode"]
    if handoff_mode == "context-only":
        assert_true(state["can_continue_judgment_only"], f"{fixture_name}: context-only must stay judgment-only")
        assert_true(not state["can_author_ir"] and not state["can_render"], f"{fixture_name}: context-only may not unlock author-ir/render")
        if fixture_name == "context_only.json":
            assert_true(not envelope["teacher_judgment_boundaries"], f"{fixture_name}: context-only fixture should exercise global-only blocking")
    elif handoff_mode == "blocked":
        affected_outputs = collect_open_hard_affected_outputs(envelope)
        if affected_outputs:
            assert_true("handoff" in affected_outputs, f"{fixture_name}: blocked handoff fixture needs a handoff-affecting boundary")
            assert_true(state["can_author_ir"] == ("author-ir" not in affected_outputs), f"{fixture_name}: blocked handoff must respect declared author-ir blocking")
            expected_render = state["can_author_ir"] and ("render" not in affected_outputs)
            assert_true(state["can_render"] == expected_render, f"{fixture_name}: blocked handoff must respect canonical-source render gating")
        else:
            assert_true(not state["can_author_ir"] and not state["can_render"], f"{fixture_name}: global blocked handoff may not unlock downstream outputs")
    elif handoff_mode == "downstream-ready":
        assert_true(bool(envelope["approvals"]), f"{fixture_name}: downstream-ready fixture should exercise same-envelope approvals")
        assert_true(state["can_author_ir"] and state["can_render"], f"{fixture_name}: downstream-ready should unlock downstream outputs")

    validate_parity_bootstrap_semantics(envelope, fixture_name)
    validate_declared_output_fail_closed(envelope, fixture_name)
    validate_curriculum_grounded_fail_closed(envelope, fixture_name)
    if envelope["curriculum_context"]["status"] == "verified":
        assert_true(bool(envelope["curriculum_context"]["records"]), f"{fixture_name}: verified curriculum_context must publish canonical provider records")


def main() -> None:
    schema = load_json(SCHEMA_PATH)
    require_schema_contract(schema)

    fixture_paths = sorted(FIXTURE_DIR.glob("*.json"))
    fixture_names = [path.name for path in fixture_paths]
    missing_baselines = sorted(set(EXPECTED_FIXTURE_BASELINES) - set(fixture_names))
    assert_true(not missing_baselines, f"missing baseline fixtures: {missing_baselines}")

    fixtures = {}
    for path in fixture_paths:
        envelope = load_json(path)
        fixtures[path.name] = envelope
        validate_with_jsonschema(schema, envelope, path.name)
        validate_same_envelope_semantics(envelope, path.name)
        validate_fixture_expectations(envelope, path.name)

    downstream_ready_fixture = fixtures["downstream_ready.json"]
    blocked_handoff_fixture = fixtures["blocked_handoff.json"]
    context_only_fixture = fixtures["context_only.json"]
    blocked_boundary = copy.deepcopy(blocked_handoff_fixture["teacher_judgment_boundaries"][0])

    copied_open_handoff_boundary_fails = copy.deepcopy(downstream_ready_fixture)
    copied_open_handoff_boundary_fails["teacher_judgment_boundaries"].append(copy.deepcopy(blocked_boundary))

    copied_open_author_ir_boundary_fails = copy.deepcopy(downstream_ready_fixture)
    copied_open_author_ir_boundary_fails["teacher_judgment_boundaries"].append(
        {
            **copy.deepcopy(blocked_boundary),
            "affected_output_classes": ["author-ir"],
        }
    )

    copied_open_render_boundary_fails = copy.deepcopy(downstream_ready_fixture)
    copied_open_render_boundary_fails["teacher_judgment_boundaries"].append(
        {
            **copy.deepcopy(blocked_boundary),
            "boundary_id": "tj-render-regression",
            "affected_output_classes": ["render"],
        }
    )

    expect_fail_closed_regression(schema, copied_open_handoff_boundary_fails, "copied_open_handoff_boundary_fails")
    expect_fail_closed_regression(schema, copied_open_author_ir_boundary_fails, "copied_open_author_ir_boundary_fails")
    expect_fail_closed_regression(schema, copied_open_render_boundary_fails, "copied_open_render_boundary_fails")

    direct_entry_incomplete_bootstrap_fails = copy.deepcopy(context_only_fixture)
    direct_entry_incomplete_bootstrap_fails["parity_bootstrap"]["completed"] = False
    expect_schema_rejection(schema, direct_entry_incomplete_bootstrap_fails, "direct_entry_incomplete_bootstrap_fails")

    direct_entry_not_required_bootstrap_fails = copy.deepcopy(context_only_fixture)
    direct_entry_not_required_bootstrap_fails["parity_bootstrap"]["required"] = False
    expect_schema_rejection(schema, direct_entry_not_required_bootstrap_fails, "direct_entry_not_required_bootstrap_fails")

    direct_entry_workflow_drift_fails = copy.deepcopy(context_only_fixture)
    direct_entry_workflow_drift_fails["parity_bootstrap"]["selected_workflow"] = "verified-curriculum-redesign"
    expect_semantic_rejection(direct_entry_workflow_drift_fails, "direct_entry_workflow_drift_fails")

    curriculum_grounded_gate_drift_fails = copy.deepcopy(blocked_handoff_fixture)
    curriculum_grounded_gate_drift_fails["entry_mode"] = "direct-skill"
    curriculum_grounded_gate_drift_fails["parity_bootstrap"]["reason"] = "direct entry mapped to workflow"
    curriculum_grounded_gate_drift_fails["gate_v2"]["threshold_source"] = "explicit"
    expect_semantic_rejection(curriculum_grounded_gate_drift_fails, "curriculum_grounded_gate_drift_fails")

    curriculum_grounded_context_only_handoff_fails = copy.deepcopy(downstream_ready_fixture)
    curriculum_grounded_context_only_handoff_fails["approval_state"]["handoff_mode"] = "downstream-ready"
    curriculum_grounded_context_only_handoff_fails["approval_state"]["can_handoff"] = True
    curriculum_grounded_context_only_handoff_fails["approval_state"]["can_author_ir"] = False
    curriculum_grounded_context_only_handoff_fails["approval_state"]["can_render"] = False
    curriculum_grounded_context_only_handoff_fails["approval_state"]["envelope_authority"]["downstream_operations_cleared"] = {
        "handoff": True,
        "author_ir": False,
        "render": False,
    }
    curriculum_grounded_context_only_handoff_fails["next_authorized_operation"] = "handoff"
    curriculum_grounded_context_only_handoff_fails["curriculum_context"]["status"] = "unverified"
    curriculum_grounded_context_only_handoff_fails["curriculum_context"]["records"] = []
    expect_schema_rejection(schema, curriculum_grounded_context_only_handoff_fails, "curriculum_grounded_context_only_handoff_fails")

    quarantined_provider_fails = copy.deepcopy(downstream_ready_fixture)
    quarantined_provider_fails["capability_record"]["provider_contract"]["provider_status"] = "quarantined"
    quarantined_provider_fails["capability_record"]["provider_contract"]["verification_status"] = "quarantined"
    quarantined_provider_fails["approval_state"]["envelope_authority"]["provider_contract_state"] = "quarantined"

    inferred_unblock_source_fails = copy.deepcopy(downstream_ready_fixture)
    inferred_unblock_source_fails["curriculum_context"]["unblock_sources_allowed"] = [":provided", ":web", ":inferred"]

    expect_schema_rejection(schema, inferred_unblock_source_fails, "inferred_unblock_source_fails")
    expect_schema_rejection(schema, quarantined_provider_fails, "quarantined_provider_fails")

    rejected_handoff_boundary_fails = copy.deepcopy(downstream_ready_fixture)
    rejected_handoff_boundary_fails["teacher_judgment_boundaries"].append(
        {
            **copy.deepcopy(blocked_boundary),
            "resolution": {
                "status": "resolved",
                "teacher_confirmation": {
                    "required": True,
                    "confirmed": True,
                    "confirmation_source": "teacher-approved-edit",
                    "confirmation_anchor": {
                        "carrier": "transcript",
                        "locator_type": "transcript-line-range",
                        "locator_value": "L200-L205",
                    },
                },
                "supporting_evidence": [],
                "approval_record": {
                    "approval_id": "apr-rejected-handoff",
                    "boundary_id": "tj-handoff-scope",
                    "decision": "rejected",
                },
            },
        }
    )

    rejected_render_boundary_fails = copy.deepcopy(downstream_ready_fixture)
    rejected_render_boundary_fails["teacher_judgment_boundaries"].append(
        {
            **copy.deepcopy(blocked_boundary),
            "boundary_id": "tj-render-rejected",
            "affected_output_classes": ["render"],
            "resolution": {
                "status": "resolved",
                "teacher_confirmation": {
                    "required": True,
                    "confirmed": True,
                    "confirmation_source": "teacher-approved-edit",
                    "confirmation_anchor": {
                        "carrier": "transcript",
                        "locator_type": "transcript-line-range",
                        "locator_value": "L210-L214",
                    },
                },
                "supporting_evidence": [],
                "approval_record": {
                    "approval_id": "apr-rejected-render",
                    "boundary_id": "tj-render-rejected",
                    "decision": "rejected",
                },
            },
        }
    )

    expect_schema_rejection(schema, rejected_handoff_boundary_fails, "rejected_handoff_boundary_fails")
    expect_schema_rejection(schema, rejected_render_boundary_fails, "rejected_render_boundary_fails")

    revoked_author_ir_boundary_fails = copy.deepcopy(downstream_ready_fixture)
    revoked_author_ir_boundary_fails["teacher_judgment_boundaries"].append(
        {
            **copy.deepcopy(blocked_boundary),
            "boundary_id": "tj-author-ir-revoked",
            "affected_output_classes": ["author-ir"],
            "resolution": {
                "status": "resolved",
                "teacher_confirmation": {
                    "required": True,
                    "confirmed": True,
                    "confirmation_source": "teacher-approved-edit",
                    "confirmation_anchor": {
                        "carrier": "transcript",
                        "locator_type": "transcript-line-range",
                        "locator_value": "L220-L224",
                    },
                },
                "supporting_evidence": [],
                "approval_record": {
                    "approval_id": "apr-revoked-author-ir",
                    "boundary_id": "tj-author-ir-revoked",
                    "decision": "revoked",
                },
            },
        }
    )

    revoked_handoff_boundary_fails = copy.deepcopy(downstream_ready_fixture)
    revoked_handoff_boundary_fails["teacher_judgment_boundaries"].append(
        {
            **copy.deepcopy(blocked_boundary),
            "boundary_id": "tj-handoff-revoked",
            "resolution": {
                "status": "resolved",
                "teacher_confirmation": {
                    "required": True,
                    "confirmed": True,
                    "confirmation_source": "teacher-approved-edit",
                    "confirmation_anchor": {
                        "carrier": "transcript",
                        "locator_type": "transcript-line-range",
                        "locator_value": "L225-L229",
                    },
                },
                "supporting_evidence": [],
                "approval_record": {
                    "approval_id": "apr-revoked-handoff",
                    "boundary_id": "tj-handoff-revoked",
                    "decision": "revoked",
                },
            },
        }
    )

    revoked_render_boundary_fails = copy.deepcopy(downstream_ready_fixture)
    revoked_render_boundary_fails["teacher_judgment_boundaries"].append(
        {
            **copy.deepcopy(blocked_boundary),
            "boundary_id": "tj-render-revoked",
            "affected_output_classes": ["render"],
            "resolution": {
                "status": "resolved",
                "teacher_confirmation": {
                    "required": True,
                    "confirmed": True,
                    "confirmation_source": "teacher-approved-edit",
                    "confirmation_anchor": {
                        "carrier": "transcript",
                        "locator_type": "transcript-line-range",
                        "locator_value": "L230-L234",
                    },
                },
                "supporting_evidence": [],
                "approval_record": {
                    "approval_id": "apr-revoked-render",
                    "boundary_id": "tj-render-revoked",
                    "decision": "revoked",
                },
            },
        }
    )

    expect_schema_rejection(schema, revoked_author_ir_boundary_fails, "revoked_author_ir_boundary_fails")
    expect_schema_rejection(schema, revoked_handoff_boundary_fails, "revoked_handoff_boundary_fails")
    expect_schema_rejection(schema, revoked_render_boundary_fails, "revoked_render_boundary_fails")

    bad_approval_timestamp_fails = copy.deepcopy(downstream_ready_fixture)
    bad_approval_timestamp_fails["approvals"][0]["decided_at"] = "not-a-date-time"

    bad_provider_url_fails = copy.deepcopy(blocked_handoff_fixture)
    bad_provider_url_fails["curriculum_context"]["records"][0]["verification_anchor"]["locator_value"] = "not-a-url"
    bad_provider_url_fails["provenance_ledger"][0]["verification_anchor"]["locator_value"] = "not-a-url"

    expect_schema_rejection(schema, bad_approval_timestamp_fails, "bad_approval_timestamp_fails")
    expect_schema_rejection(schema, bad_provider_url_fails, "bad_provider_url_fails")

    mismatched_approval_summary_fails = copy.deepcopy(downstream_ready_fixture)
    mismatched_approval_summary_fails["approvals"][0]["decision"] = "revoked"

    expect_semantic_rejection(mismatched_approval_summary_fails, "mismatched_approval_summary_fails")

    malformed_provider_record_fails = copy.deepcopy(downstream_ready_fixture)
    malformed_provider_record_fails["curriculum_context"]["records"] = [
        {
            "record_id": "prov-bad",
            "record_scope": "curriculum-context",
            "provider": {
                "provider_id": "curriculum-2022-social",
                "provider_kind": "curriculum-provider",
                "release_id": "curriculum-2022-social@2026-07-15",
                "release_version": "2026.07.15",
            },
            "provenance_grade": ":provided",
            "verification_status": "complete",
            "source_reference": "curriculum.pdf#p1",
            "verification_evidence_type": "provided-document",
            "verification_anchor": {
                "carrier": "provider-record",
                "locator_type": "provider-record-id",
                "locator_value": "provider-record::curriculum-2022-social::p1",
            },
            "source_license": {
                "status": "verified-compatible",
                "license_id": "CC-BY-4.0",
                "evidence_anchor": {
                    "carrier": "provider-release-manifest",
                    "locator_type": "release-id",
                    "locator_value": "curriculum-2022-social@2026-07-15",
                },
            }
        }
    ]

    expect_schema_rejection(schema, malformed_provider_record_fails, "malformed_provider_record_fails")

    def _superseding_approval(approval_id: str, decision: str, decided_at: str) -> dict:
        return {
            "approval_id": approval_id,
            "boundary_id": "tj-assessment-weight",
            "decision": decision,
            "decided_by": {"actor_type": "teacher", "actor_ref": "teacher:kim"},
            "decided_at": decided_at,
            "confirmation_anchor": {
                "carrier": "transcript",
                "locator_type": "transcript-line-range",
                "locator_value": "L150-L156",
            },
            "supporting_evidence": [
                {
                    "type": "web-verification",
                    "anchor": {
                        "carrier": "url",
                        "locator_type": "absolute-url",
                        "locator_value": "https://example.com/curriculum/assessment-weighting-revised",
                    },
                    "sha256": None,
                    "detail": "이후 결정 기록",
                }
            ],
        }

    stale_approved_superseded_by_revoked_fails = copy.deepcopy(downstream_ready_fixture)
    stale_approved_superseded_by_revoked_fails["approvals"].append(
        _superseding_approval("apr-assessment-weight-revoked", "revoked", "2026-07-15T10:00:00Z")
    )
    expect_semantic_rejection(stale_approved_superseded_by_revoked_fails, "stale_approved_superseded_by_revoked_fails")

    stale_approved_superseded_by_rejected_fails = copy.deepcopy(downstream_ready_fixture)
    stale_approved_superseded_by_rejected_fails["approvals"].append(
        _superseding_approval("apr-assessment-weight-rejected-late", "rejected", "2026-07-15T10:05:00Z")
    )
    expect_semantic_rejection(stale_approved_superseded_by_rejected_fails, "stale_approved_superseded_by_rejected_fails")

    equal_timestamp_conflict_fails = copy.deepcopy(downstream_ready_fixture)
    equal_timestamp_conflict_fails["approvals"].append(
        _superseding_approval("apr-assessment-weight-conflict", "revoked", "2026-07-15T09:30:00Z")
    )
    expect_semantic_rejection(equal_timestamp_conflict_fails, "equal_timestamp_conflict_fails")

    json_mode = "--json" in sys.argv[1:]
    regression_case_count = 22
    if json_mode:
        print(json.dumps({
            "status": "VALIDATION_OK",
            "fixture_count": len(fixture_paths),
            "regression_case_count": regression_case_count,
        }, ensure_ascii=False))
    else:
        print(f"validated {len(fixture_paths)} workflow-envelope fixtures and {regression_case_count} semantic/schema regression cases")
        print("- direct_entry_incomplete_bootstrap_fails: direct-skill entry cannot skip parity_bootstrap completion before handoff")
        print("- direct_entry_not_required_bootstrap_fails: direct-skill entry cannot clear handoff with parity_bootstrap.required=false")
        print("- direct_entry_workflow_drift_fails: direct-skill selected_workflow must stay attached to workflow_type")
        print("- curriculum_grounded_gate_drift_fails: curriculum-grounded direct entry must reconstruct router-equivalent Deep gate defaults")
        print("- curriculum_grounded_context_only_handoff_fails: curriculum-grounded downstream-ready handoff fails closed without verified curriculum records")
        print("- copied_open_handoff_boundary_fails: downstream-ready/can_handoff reject a copied open hard handoff+author-ir boundary")
        print("- copied_open_author_ir_boundary_fails: can_author_ir rejects a copied open hard author-ir boundary even when the rest of the payload stays downstream-ready")
        print("- copied_open_render_boundary_fails: can_render rejects a copied open hard render boundary even when the rest of the payload stays downstream-ready")
        print("- quarantined_provider_fails: provider cleanup/quarantine state cannot pass as downstream-ready")
        print("- inferred_unblock_source_fails: curriculum_context cannot advertise :inferred as an allowed unblock source")
        print("- malformed_provider_record_fails: curriculum_context provider records must publish the canonical provider/provenance/license/read-only fields")
        print("- rejected_handoff_boundary_fails: resolved rejected hard handoff boundary cannot keep downstream-ready clearance")
        print("- rejected_render_boundary_fails: resolved rejected hard render boundary cannot keep render clearance")
        print("- mismatched_approval_summary_fails: approval summaries must stay synchronized with in-envelope approval rows")
        print("- revoked_author_ir_boundary_fails: resolved revoked hard author-ir boundary cannot keep author-ir clearance")
        print("- revoked_handoff_boundary_fails: resolved revoked hard handoff boundary cannot keep downstream-ready clearance")
        print("- revoked_render_boundary_fails: resolved revoked hard render boundary cannot keep render clearance")
        print("- bad_approval_timestamp_fails: malformed approval decided_at timestamps are rejected by the schema contract")
        print("- bad_provider_url_fails: malformed provider URL anchors are rejected by the canonical provider-record schema")
        print("- stale_approved_superseded_by_revoked_fails: a newer revoked decision blocks a stale approved boundary clearance (temporal supersession)")
        print("- stale_approved_superseded_by_rejected_fails: a newer rejected decision blocks a stale approved boundary clearance (temporal supersession)")
        print("- equal_timestamp_conflict_fails: two same-boundary approvals sharing the latest decided_at fail closed as ambiguous")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
