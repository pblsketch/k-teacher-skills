from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "lesson-package-ir.schema.json"
BACKPORT_MARKER_FIXTURE_PATH = ROOT / "tests" / "golden" / "backport-marker" / "valid.json"
RENDERER_PARITY_FIXTURE_PATH = ROOT / "tests" / "golden" / "renderer-parity" / "valid.json"
VALID_IR_FIXTURE_PATH = ROOT / "tests" / "golden" / "lesson-package-ir" / "downstream-ready.json"



def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_schema_contract(schema: dict) -> None:
    defs = schema.get("$defs", {})
    required = set(schema.get("required", []))
    assert_true(
        "provider_contract" in required,
        "canonical IR must require provider_contract to preserve provider cleanup/quarantine state",
    )

    provider_contract = defs.get("providerContractSnapshot", {})
    provider_contract_required = set(provider_contract.get("required", []))
    assert_true(
        {
            "access_mode",
            "provider_status",
            "provenance_status",
            "verification_status",
            "source_license_status",
        }.issubset(provider_contract_required),
        "providerContractSnapshot must require the provider cleanup/quarantine fields",
    )
    assert_true(
        provider_contract.get("properties", {}).get("provider_status", {}).get("const") == "available",
        "providerContractSnapshot.provider_status must prove quarantine is cleared",
    )
    assert_true(
        provider_contract.get("properties", {}).get("verification_status", {}).get("const") == "complete",
        "providerContractSnapshot.verification_status must prove quarantine is cleared",
    )

    provenance_record = defs.get("provenanceRecord", {})
    provenance_required = set(provenance_record.get("required", []))
    assert_true(
        {
            "record_id",
            "record_scope",
            "provider",
            "provenance_grade",
            "verification_evidence_type",
            "verification_anchor",
            "source_license",
            "read_only_input",
        }.issubset(provenance_required),
        "provenanceRecord must require the workflow-envelope ledger fields",
    )

    workflow_revision = schema.get("properties", {}).get("workflow_envelope_revision_id", {})
    assert_true(
        workflow_revision.get("$ref") == "#/$defs/envelopeRevisionId",
        "workflow_envelope_revision_id must reuse the envelope revision contract",
    )

    provider_identity = defs.get("providerIdentity", {})
    assert_true(
        provider_identity.get("properties", {}).get("provider_kind", {}).get("enum") == ["curriculum-provider", "textbook-provider", "web-source", "school-evaluation-plan-provider"],
        "providerIdentity.provider_kind enum mismatch",
    )

    source_license = defs.get("sourceLicenseState", {})
    assert_true(
        "license_id" in source_license.get("required", []),
        "sourceLicenseState must require license_id",
    )
    assert_true(
        source_license.get("properties", {}).get("status", {}).get("enum") == ["verified-compatible", "verified-restricted", "prohibited", "unknown"],
        "sourceLicenseState.status enum mismatch",
    )

    assert_true(
        source_license.get("properties", {}).get("license_authority", {}).get("enum") == ["public-license", "teacher-authorized-public-disclosure"],
        "sourceLicenseState.license_authority (AR-1) must be an optional public-license vs teacher-authorized-public-disclosure enum",
    )
    assert_true(
        "license_authority" not in source_license.get("required", []),
        "sourceLicenseState.license_authority must stay optional (non-breaking)",
    )

    verification_anchor = provenance_record.get("properties", {}).get("verification_anchor", {})
    assert_true(
        verification_anchor.get("$ref") == "#/$defs/providerVerificationAnchor",
        "provenanceRecord.verification_anchor must use providerVerificationAnchor",
    )

    render_targets = defs.get("document", {}).get("properties", {}).get("render_targets", {}).get("const")
    assert_true(render_targets == ["hwpx", "docx", "html"], "document.render_targets must publish the stage-1 renderer set")



def make_boundary(boundary_id: str, affected_output_classes: list[str]) -> dict:
    return {
        "boundary_id": f"tj-{boundary_id}",
        "category": "artifact-scope",
        "description": f"Boundary for {boundary_id}",
        "affected_output_classes": affected_output_classes,
        "blocking_severity": "hard",
        "resolution": {
            "status": "open",
            "teacher_confirmation": {
                "required": True,
                "confirmed": False,
                "confirmation_source": None,
                "confirmation_anchor": {
                    "carrier": "null",
                    "locator_type": "null",
                    "locator_value": None,
                },
            },
            "supporting_evidence": [],
        },
        "allowed_next_ops_while_open": [
            "ask-question",
            "summarize",
            "judgment-only",
        ],
        "created_by": "workflow",
        "last_updated_round": 1,
    }


def resolve_boundary(boundary: dict, decision: str, *, status: str = "resolved") -> dict:
    boundary["resolution"] = {
        "status": status,
        "teacher_confirmation": {
            "required": True,
            "confirmed": True,
            "confirmation_source": "teacher-approved-edit",
            "confirmation_anchor": {
                "carrier": "handoff-artifact",
                "locator_type": "handoff-heading",
                "locator_value": f"evidence::{boundary['boundary_id']}",
            },
        },
        "supporting_evidence": [
            {
                "type": "provided-document",
                "anchor": {
                    "carrier": "handoff-artifact",
                    "locator_type": "handoff-heading",
                    "locator_value": f"evidence::{boundary['boundary_id']}",
                },
                "sha256": None,
                "detail": f"Evidence for {boundary['boundary_id']}",
            }
        ],
        "approval_record": {
            "approval_id": f"apr-{boundary['boundary_id'][3:]}",
            "decision": decision,
        },
    }
    return boundary



def make_valid_ir() -> dict:
    return load_json(VALID_IR_FIXTURE_PATH)



def first_error(validator: jsonschema.Draft202012Validator, payload: dict) -> jsonschema.ValidationError | None:
    errors = sorted(validator.iter_errors(payload), key=lambda error: (list(error.path), error.message))
    return errors[0] if errors else None



def expect_valid(validator: jsonschema.Draft202012Validator, payload: dict, case_name: str) -> None:
    error = first_error(validator, payload)
    if error is not None:
        path = ".".join(str(part) for part in error.path) or "<root>"
        raise AssertionError(f"{case_name}: expected valid but failed at {path}: {error.message}")


def expect_invalid(validator: jsonschema.Draft202012Validator, payload: dict, case_name: str) -> None:
    error = first_error(validator, payload)
    assert_true(error is not None, f"{case_name}: expected invalid but schema accepted payload")
def validate_first_vertical_slice(ir_payload: dict, marker_payload: dict, case_name: str) -> None:
    assert_true(ir_payload["ir_id"] == marker_payload["ir_id"], f"{case_name}: IR id must match the canonical backport marker")
    assert_true(
        marker_payload["manual_edit_status"] == "backported",
        f"{case_name}: first vertical slice requires a backported marker, not a drifted render",
    )
    expected_ir_revision = marker_payload.get("backported_to_ir_revision_id") or marker_payload["ir_revision_id"]
    assert_true(
        ir_payload["ir_revision_id"] == expected_ir_revision,
        f"{case_name}: IR revision identity must match the canonical backport marker lifecycle",
    )
    assert_true(
        ir_payload["workflow_id"] == marker_payload["workflow_id"],
        f"{case_name}: workflow_id must match the canonical backport marker lifecycle",
    )

    documents = ir_payload["lesson_package"]["documents"]
    assert_true(bool(documents), f"{case_name}: lesson_package must include at least one document")
    expected_render_targets = ["hwpx", "docx", "html"]
    for document in documents:
        assert_true(
            document["render_targets"] == expected_render_targets,
            f"{case_name}: first vertical slice must expose hwpx/docx/html render targets in canonical order",
        )


def validate_renderer_parity_handoff(ir_payload: dict, parity_payload: dict, case_name: str) -> None:
    assert_true(ir_payload["ir_id"] == parity_payload["ir_id"], f"{case_name}: IR id must match renderer parity proof")
    assert_true(
        ir_payload["ir_revision_id"] == parity_payload["backported_to_ir_revision_id"],
        f"{case_name}: IR revision must match the renderer parity backport target",
    )
    assert_true(ir_payload["approval_state"] == "approved", f"{case_name}: positive parity handoff requires approved IR state")
    assert_true(ir_payload["handoff_mode"] == "downstream-ready", f"{case_name}: positive parity handoff requires downstream-ready mode")
    documents = ir_payload["lesson_package"]["documents"]
    assert_true(len(documents) == 1, f"{case_name}: renderer parity proof fixture expects one canonical document")
    document = documents[0]
    assert_true(document["document_id"] == parity_payload["document"]["document_id"], f"{case_name}: document_id drifted from parity fixture")
    assert_true(document["document_class"] == parity_payload["document"]["document_class"], f"{case_name}: document_class drifted from parity fixture")
    assert_true(ir_payload["workflow_id"] == parity_payload["workflow_id"], f"{case_name}: workflow_id drifted from parity fixture")
    assert_true(document["title"] == parity_payload["document"]["title"], f"{case_name}: document title drifted from parity fixture")
    assert_true(document["render_targets"] == parity_payload["expected_render_targets"], f"{case_name}: render_targets drifted from parity fixture")
    assert_true(document["content"]["sections"] == parity_payload["required_content"], f"{case_name}: IR sections drifted from parity fixture")
    assert_true(document["content"]["provenance_markers"] == parity_payload["provenance_markers"], f"{case_name}: IR provenance markers drifted from parity fixture")
    assert_true(
        document["content"]["unresolved_boundary_markers"] == parity_payload["unresolved_boundary_markers"],
        f"{case_name}: IR unresolved boundary markers drifted from parity fixture",
    )
    assert_true(document["content"]["unresolved_boundary_markers"] == [], f"{case_name}: downstream-ready IR may not carry unresolved boundary markers")
    assert_true(parity_payload["unresolved_boundary_markers"] == [], f"{case_name}: downstream-ready parity proof may not carry unresolved boundary markers")
    ledger_record_ids = {record["record_id"] for record in ir_payload["provenance_ledger"]}
    parity_record_ids = {marker["record_id"] for marker in parity_payload["provenance_markers"]}
    assert_true(parity_record_ids.issubset(ledger_record_ids), f"{case_name}: parity provenance markers must be backed by IR provenance_ledger records")
    for render in parity_payload["renders"]:
        artifact = load_json(ROOT / render["artifact_path"])
        assert_true(artifact["document_id"] == document["document_id"], f"{case_name}: {render['renderer_format']} artifact document_id drifted from IR")
        assert_true(artifact["document_class"] == document["document_class"], f"{case_name}: {render['renderer_format']} artifact document_class drifted from IR")
        assert_true(artifact["title"] == document["title"], f"{case_name}: {render['renderer_format']} artifact title drifted from IR")
        assert_true(artifact["required_content"] == document["content"]["sections"], f"{case_name}: {render['renderer_format']} artifact required content drifted from IR")
        assert_true(artifact["provenance_markers"] == document["content"]["provenance_markers"], f"{case_name}: {render['renderer_format']} artifact provenance markers drifted from IR")
        assert_true(
            artifact["unresolved_boundary_markers"] == document["content"]["unresolved_boundary_markers"],
            f"{case_name}: {render['renderer_format']} artifact unresolved boundary markers drifted from IR",
        )
        artifact_marker = artifact["embedded_backport_marker"]
        assert_true(artifact_marker["ir_id"] == ir_payload["ir_id"], f"{case_name}: {render['renderer_format']} embedded marker ir_id drifted from IR")
        assert_true(artifact_marker["ir_revision_id"] == parity_payload["rendered_from_ir_revision_id"], f"{case_name}: {render['renderer_format']} embedded marker rendered revision drifted")
        assert_true(artifact_marker["backported_to_ir_revision_id"] == ir_payload["ir_revision_id"], f"{case_name}: {render['renderer_format']} embedded marker backport target drifted from IR")
        assert_true(artifact_marker["workflow_id"] == ir_payload["workflow_id"], f"{case_name}: {render['renderer_format']} embedded marker workflow_id drifted from IR")

def validate_witness_chain(marker_payload: dict, parity_payload: dict, case_name: str) -> None:
    assert_true(marker_payload["workflow_id"] == parity_payload["workflow_id"], f"{case_name}: workflow_id drifted between canonical marker and parity proof")
    assert_true(marker_payload["ir_id"] == parity_payload["ir_id"], f"{case_name}: ir_id drifted between canonical marker and parity proof")
    assert_true(marker_payload["ir_revision_id"] == parity_payload["rendered_from_ir_revision_id"], f"{case_name}: rendered IR revision drifted between canonical marker and parity proof")
    assert_true(marker_payload["backported_to_ir_revision_id"] == parity_payload["backported_to_ir_revision_id"], f"{case_name}: backport target drifted between canonical marker and parity proof")

def expect_semantic_rejection(check, payload: dict, reference: dict, case_name: str) -> None:
    try:
        check(payload, reference, case_name)
    except AssertionError:
        return
    raise AssertionError(f"{case_name}: expected semantic rejection")





def main() -> None:
    schema = load_json(SCHEMA_PATH)
    require_schema_contract(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)
    backport_marker = load_json(BACKPORT_MARKER_FIXTURE_PATH)
    renderer_parity_fixture = load_json(RENDERER_PARITY_FIXTURE_PATH)

    blocked_handoff_author_ir_ok = make_valid_ir()
    blocked_handoff_author_ir_ok["handoff_mode"] = "blocked"
    blocked_handoff_author_ir_ok["teacher_judgment_boundaries"] = [
        make_boundary("boundary-handoff", ["handoff"])
    ]

    downstream_ready_ok = make_valid_ir()


    open_author_ir_boundary_fails = copy.deepcopy(blocked_handoff_author_ir_ok)
    open_author_ir_boundary_fails["teacher_judgment_boundaries"] = [
        make_boundary("boundary-author-ir", ["author-ir"])
    ]

    rejected_author_ir_resolution_fails = make_valid_ir()
    rejected_author_ir_resolution_fails["teacher_judgment_boundaries"] = [
        resolve_boundary(make_boundary("boundary-author-ir-resolution", ["author-ir"]), "rejected")
    ]

    revoked_author_ir_resolution_fails = make_valid_ir()
    revoked_author_ir_resolution_fails["teacher_judgment_boundaries"] = [
        resolve_boundary(make_boundary("boundary-author-ir-revoked", ["author-ir"]), "revoked")
    ]

    open_downstream_boundary_fails = make_valid_ir()
    open_downstream_boundary_fails["teacher_judgment_boundaries"] = [
        make_boundary("boundary-downstream", ["handoff"])
    ]

    rejected_downstream_resolution_fails = make_valid_ir()
    rejected_downstream_resolution_fails["teacher_judgment_boundaries"] = [
        resolve_boundary(
            make_boundary("boundary-downstream-rejected", ["handoff"]),
            "rejected",
        )
    ]

    revoked_downstream_resolution_fails = make_valid_ir()
    revoked_downstream_resolution_fails["teacher_judgment_boundaries"] = [
        resolve_boundary(
            make_boundary("boundary-downstream-revoked", ["handoff"]),
            "revoked",
        )
    ]

    open_render_boundary_fails = make_valid_ir()
    open_render_boundary_fails["teacher_judgment_boundaries"] = [
        make_boundary("boundary-render", ["render"])
    ]

    rejected_render_resolution_fails = make_valid_ir()
    rejected_render_resolution_fails["teacher_judgment_boundaries"] = [
        resolve_boundary(make_boundary("boundary-render-rejected", ["render"]), "rejected")
    ]

    revoked_render_resolution_fails = make_valid_ir()
    revoked_render_resolution_fails["teacher_judgment_boundaries"] = [
        resolve_boundary(make_boundary("boundary-render-revoked", ["render"]), "revoked")
    ]

    inferred_provenance_fails = make_valid_ir()
    inferred_provenance_fails["provenance_ledger"][0]["provenance_grade"] = ":inferred"

    missing_verification_anchor_fails = make_valid_ir()
    missing_verification_anchor_fails["provenance_ledger"][0]["verification_anchor"] = None

    unresolved_license_fails = make_valid_ir()
    unresolved_license_fails["provenance_ledger"][0]["source_license"] = {
        "status": "unknown",
        "license_id": None,
        "evidence_anchor": None,
    }

    provider_not_read_only_fails = make_valid_ir()
    provider_not_read_only_fails["provenance_ledger"][0]["read_only_input"] = False

    quarantined_provider_contract_fails = make_valid_ir()
    quarantined_provider_contract_fails["provider_contract"]["verification_status"] = "quarantined"

    blocked_without_handoff_boundary_fails = make_valid_ir()
    blocked_without_handoff_boundary_fails["handoff_mode"] = "blocked"
    blocked_without_handoff_boundary_fails["teacher_judgment_boundaries"] = []

    mismatched_approval_anchor_fails = make_valid_ir()
    mismatched_approval_anchor_fails["teacher_judgment_boundaries"] = [
        resolve_boundary(make_boundary("boundary-author-ir-mismatch", ["author-ir"]), "approved")
    ]
    mismatched_approval_anchor_fails["teacher_judgment_boundaries"][0]["resolution"]["teacher_confirmation"]["confirmation_anchor"] = {
        "carrier": "approval-record",
        "locator_type": "approval-id",
        "locator_value": "apr-different",
    }

    malformed_web_url_fails = make_valid_ir()
    malformed_web_url_fails["provenance_ledger"][0]["provider"]["provider_kind"] = "web-source"
    malformed_web_url_fails["provenance_ledger"][0]["provenance_grade"] = ":web"
    malformed_web_url_fails["provenance_ledger"][0]["verification_evidence_type"] = "web-verification"
    malformed_web_url_fails["provenance_ledger"][0]["verification_anchor"] = {
        "carrier": "url",
        "locator_type": "absolute-url",
        "locator_value": "not-a-url",
    }
    malformed_web_url_fails["provenance_ledger"][0]["source_reference"] = "https://example.com/curriculum/web-copy"

    missing_html_render_target_fails = make_valid_ir()
    missing_html_render_target_fails["lesson_package"]["documents"][0]["render_targets"] = ["hwpx", "docx"]

    backport_marker_revision_drift_fails = make_valid_ir()
    backport_marker_revision_drift_fails["ir_revision_id"] = "rev-1002"

    drifted_backport_marker_fails = make_valid_ir()

    expect_valid(validator, blocked_handoff_author_ir_ok, "blocked_handoff_author_ir_ok")
    expect_valid(validator, downstream_ready_ok, "downstream_ready_ok")
    validate_first_vertical_slice(downstream_ready_ok, backport_marker, "downstream_ready_ok")
    validate_renderer_parity_handoff(downstream_ready_ok, renderer_parity_fixture, "downstream_ready_ok")
    validate_witness_chain(backport_marker, renderer_parity_fixture, "downstream_ready_ok")

    expect_invalid(validator, open_author_ir_boundary_fails, "open_author_ir_boundary_fails")
    expect_invalid(validator, rejected_author_ir_resolution_fails, "rejected_author_ir_resolution_fails")
    expect_invalid(validator, revoked_author_ir_resolution_fails, "revoked_author_ir_resolution_fails")
    expect_invalid(validator, open_downstream_boundary_fails, "open_downstream_boundary_fails")
    expect_invalid(validator, rejected_downstream_resolution_fails, "rejected_downstream_resolution_fails")
    expect_invalid(validator, revoked_downstream_resolution_fails, "revoked_downstream_resolution_fails")
    expect_invalid(validator, inferred_provenance_fails, "inferred_provenance_fails")
    expect_invalid(validator, missing_verification_anchor_fails, "missing_verification_anchor_fails")
    expect_invalid(validator, unresolved_license_fails, "unresolved_license_fails")
    expect_invalid(validator, provider_not_read_only_fails, "provider_not_read_only_fails")
    expect_invalid(validator, quarantined_provider_contract_fails, "quarantined_provider_contract_fails")
    expect_invalid(validator, open_render_boundary_fails, "open_render_boundary_fails")
    expect_invalid(validator, rejected_render_resolution_fails, "rejected_render_resolution_fails")
    expect_invalid(validator, revoked_render_resolution_fails, "revoked_render_resolution_fails")
    expect_invalid(validator, blocked_without_handoff_boundary_fails, "blocked_without_handoff_boundary_fails")
    expect_invalid(validator, mismatched_approval_anchor_fails, "mismatched_approval_anchor_fails")
    expect_invalid(validator, malformed_web_url_fails, "malformed_web_url_fails")
    expect_invalid(validator, missing_html_render_target_fails, "missing_html_render_target_fails")
    expect_valid(validator, backport_marker_revision_drift_fails, "backport_marker_revision_drift_fails_schema")
    expect_semantic_rejection(validate_first_vertical_slice, backport_marker_revision_drift_fails, backport_marker, "backport_marker_revision_drift_fails")
    expect_semantic_rejection(validate_first_vertical_slice, drifted_backport_marker_fails, load_json(ROOT / "tests" / "golden" / "backport-marker" / "drifted.json"), "drifted_backport_marker_fails")

    backport_marker_workflow_drift_fails = copy.deepcopy(backport_marker)
    backport_marker_workflow_drift_fails["workflow_id"] = "workflow-drifted"
    expect_semantic_rejection(validate_first_vertical_slice, downstream_ready_ok, backport_marker_workflow_drift_fails, "backport_marker_workflow_drift_fails")

    parity_workflow_drift_fails = copy.deepcopy(renderer_parity_fixture)
    parity_workflow_drift_fails["workflow_id"] = "workflow-drifted"
    expect_semantic_rejection(validate_renderer_parity_handoff, downstream_ready_ok, parity_workflow_drift_fails, "parity_workflow_drift_fails")

    unresolved_boundary_markers_fails = make_valid_ir()
    unresolved_boundary_markers_fails["lesson_package"]["documents"][0]["content"]["unresolved_boundary_markers"] = [
        {"boundary_id": "tj-local-example", "indicator_text": "교사 확인 필요", "detail_text": "지역 사례와 학교별 현장 맥락은 교사가 최종 확정해야 함"}
    ]
    expect_semantic_rejection(validate_renderer_parity_handoff, unresolved_boundary_markers_fails, renderer_parity_fixture, "unresolved_boundary_markers_fails")

    parity_source_revision_drift_fails = copy.deepcopy(renderer_parity_fixture)
    parity_source_revision_drift_fails["rendered_from_ir_revision_id"] = "rev-9999"
    expect_semantic_rejection(validate_witness_chain, backport_marker, parity_source_revision_drift_fails, "parity_source_revision_drift_fails")

    parity_workflow_witness_drift_fails = copy.deepcopy(renderer_parity_fixture)
    parity_workflow_witness_drift_fails["workflow_id"] = "workflow-drifted"
    expect_semantic_rejection(validate_witness_chain, backport_marker, parity_workflow_witness_drift_fails, "parity_workflow_witness_drift_fails")

    parity_ir_id_witness_drift_fails = copy.deepcopy(renderer_parity_fixture)
    parity_ir_id_witness_drift_fails["ir_id"] = "lesson-ir-drifted"
    expect_semantic_rejection(validate_witness_chain, backport_marker, parity_ir_id_witness_drift_fails, "parity_ir_id_witness_drift_fails")

    parity_backport_target_witness_drift_fails = copy.deepcopy(renderer_parity_fixture)
    parity_backport_target_witness_drift_fails["backported_to_ir_revision_id"] = "rev-1999"
    expect_semantic_rejection(validate_witness_chain, backport_marker, parity_backport_target_witness_drift_fails, "parity_backport_target_witness_drift_fails")

    json_mode = "--json" in sys.argv[1:]
    if json_mode:
        print(json.dumps({
            "status": "VALIDATION_OK",
            "case_count": 22,
        }, ensure_ascii=False))
    else:
        print("validated 22 lesson-package-ir cases")
        print("- blocked_handoff_author_ir_ok: blocked handoff remains valid when no open hard boundary blocks author-ir")
        print("- downstream_ready_ok: downstream-ready remains valid with envelope-aligned provider, verification anchor, compatible license evidence, cleared provider contract, and backport-marker-aligned revision identity")
        print("- downstream_ready_ok also matches the renderer-parity proof fixture for canonical document identity and render-target order")
        print("- open_author_ir_boundary_fails: open hard author-ir boundary prevents canonical IR validation")
        print("- rejected_author_ir_resolution_fails: resolved hard author-ir boundary with rejected approval trace cannot clear canonical IR approval")
        print("- revoked_author_ir_resolution_fails: resolved hard author-ir boundary with revoked approval trace cannot clear canonical IR approval")
        print("- open_downstream_boundary_fails: open hard downstream handoff boundary prevents handoff_mode=downstream-ready")
        print("- rejected_downstream_resolution_fails: resolved hard downstream handoff boundary with rejected approval trace cannot clear downstream-ready handoff")
        print("- revoked_downstream_resolution_fails: resolved hard downstream handoff boundary with revoked approval trace cannot clear downstream-ready handoff")
        print("- open_render_boundary_fails: open hard render boundary prevents canonical IR validation")
        print("- rejected_render_resolution_fails: resolved hard render boundary with rejected approval trace cannot clear canonical IR validation")
        print("- revoked_render_resolution_fails: resolved hard render boundary with revoked approval trace cannot clear canonical IR validation")
        print("- blocked_without_handoff_boundary_fails: blocked handoff requires a concrete unresolved or non-approved hard handoff boundary")
        print("- mismatched_approval_anchor_fails: approval-record confirmation anchors are rejected from canonical IR confirmation evidence")
        print("- malformed_web_url_fails: malformed URL-based provider verification anchors are rejected by canonical IR")
        print("- inferred_provenance_fails: :inferred provenance cannot survive to canonical IR or render outputs")
        print("- missing_verification_anchor_fails: downstream-ready provenance must keep a non-null verification anchor")
        print("- unresolved_license_fails: unknown source license state cannot survive to canonical IR or render outputs")
        print("- provider_not_read_only_fails: provider outputs remain read-only inputs via record-level const read_only_input=true")
        print("- quarantined_provider_contract_fails: canonical IR cannot validate while the upstream provider cleanup/quarantine gate remains uncleared")
        print("- missing_html_render_target_fails: first vertical slice rejects partial renderer target publication at schema level")
        print("- backport_marker_revision_drift_fails: IR revision drift from the canonical backport marker lifecycle is rejected before render/backport handoff")
        print("- drifted_backport_marker_fails: drifted markers remain blocked at the IR/backport handoff until a backport is complete")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
