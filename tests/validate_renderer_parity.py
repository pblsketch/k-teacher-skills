from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
BACKPORT_SCHEMA_PATH = ROOT / "schemas" / "kteacher-backport-marker.schema.json"
FIXTURE_PATH = ROOT / "tests" / "golden" / "renderer-parity" / "valid.json"
EXPECTED_RENDER_ORDER = ["hwpx", "docx", "html"]
EXPECTED_CANONICAL_LOCATIONS = {
    "hwpx": {
        "locator_kind": "package-member",
        "locator_value": "META-INF/kteacher-backport-marker.json",
        "validator_extraction_method": "read package member META-INF/kteacher-backport-marker.json and parse JSON",
    },
    "docx": {
        "locator_kind": "opc-part",
        "locator_value": "/customXml/kteacher-backport-marker.json",
        "validator_extraction_method": "read OPC custom XML part /customXml/kteacher-backport-marker.json and parse JSON",
    },
    "html": {
        "locator_kind": "dom-node",
        "locator_value": "script#kteacher-backport-marker",
        "validator_extraction_method": "read <script id=kteacher-backport-marker type=application/json> from document head and parse text as JSON",
    },
}
FORMAT_DRIFT_CASES_BY_FORMAT = {
    "hwpx": ["canonical_hwpx_marker_location_drift_fails", "embedded_marker_payload_drift_hwpx_fails", "embedded_marker_workflow_drift_hwpx_fails"],
    "docx": ["canonical_docx_marker_location_drift_fails", "embedded_marker_payload_drift_docx_fails", "embedded_marker_workflow_drift_docx_fails"],
    "html": ["canonical_html_marker_location_drift_fails", "embedded_marker_payload_drift_html_fails", "embedded_marker_workflow_drift_html_fails"],
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def first_error(validator: jsonschema.Draft202012Validator, payload: dict) -> jsonschema.ValidationError | None:
    errors = sorted(validator.iter_errors(payload), key=lambda error: (list(error.path), error.message))
    return errors[0] if errors else None


def expect_valid(validator: jsonschema.Draft202012Validator, payload: dict, case_name: str) -> None:
    error = first_error(validator, payload)
    if error is not None:
        path = ".".join(str(part) for part in error.path) or "<root>"
        raise AssertionError(f"{case_name}: expected valid but failed at {path}: {error.message}")


def expect_semantic_rejection(validator: jsonschema.Draft202012Validator, payload: dict, case_name: str) -> None:
    try:
        validate_renderer_parity(validator, payload, case_name)
    except AssertionError:
        return
    raise AssertionError(f"{case_name}: expected semantic rejection")


def load_artifact(render: dict) -> dict:
    artifact_override = render.get("artifact_override")
    if artifact_override is not None:
        return artifact_override
    return load_json(ROOT / render["artifact_path"])


def validate_renderer_parity(validator: jsonschema.Draft202012Validator, payload: dict, case_name: str) -> None:
    assert_true(payload["expected_render_targets"] == EXPECTED_RENDER_ORDER, f"{case_name}: expected_render_targets drifted")
    renders = payload["renders"]
    assert_true(len(renders) == len(EXPECTED_RENDER_ORDER), f"{case_name}: renders must cover hwpx/docx/html exactly once")

    observed_order = [render["renderer_format"] for render in renders]
    assert_true(observed_order == EXPECTED_RENDER_ORDER, f"{case_name}: renderer order drifted")

    document = payload["document"]
    expected_required_content = payload["required_content"]
    expected_provenance_markers = payload["provenance_markers"]
    expected_unresolved_boundaries = payload["unresolved_boundary_markers"]
    assert_true(expected_unresolved_boundaries == [], f"{case_name}: downstream-ready parity proof may not carry unresolved boundary markers")

    for render in renders:
        renderer_format = render["renderer_format"]
        artifact = load_artifact(render)
        assert_true(artifact["renderer_format"] == renderer_format, f"{case_name}: {renderer_format} artifact format drifted")
        assert_true(artifact["document_id"] == document["document_id"], f"{case_name}: {renderer_format} document_id drifted")
        assert_true(artifact["document_class"] == document["document_class"], f"{case_name}: {renderer_format} document_class drifted")
        assert_true(artifact["title"] == document["title"], f"{case_name}: {renderer_format} title drifted")
        assert_true(artifact["required_content"] == expected_required_content, f"{case_name}: {renderer_format} required content drifted")
        assert_true(artifact["provenance_markers"] == expected_provenance_markers, f"{case_name}: {renderer_format} provenance markers drifted")
        assert_true(
            artifact["unresolved_boundary_markers"] == expected_unresolved_boundaries,
            f"{case_name}: {renderer_format} unresolved boundary markers drifted",
        )
        assert_true(
            artifact["embedded_backport_marker_locator"] == EXPECTED_CANONICAL_LOCATIONS[renderer_format]["locator_value"],
            f"{case_name}: {renderer_format} embedded backport marker locator drifted",
        )

        artifact_marker = artifact["embedded_backport_marker"]
        expect_valid(validator, artifact_marker, f"{case_name}:{renderer_format}:artifact_backport_marker")
        assert_true(artifact_marker == render["backport_marker"], f"{case_name}: {renderer_format} extracted marker payload drifted from parity fixture")
        assert_true(artifact_marker["workflow_id"] == payload["workflow_id"], f"{case_name}: {renderer_format} workflow_id drifted")
        assert_true(artifact_marker["ir_id"] == payload["ir_id"], f"{case_name}: {renderer_format} ir_id drifted")
        assert_true(
            artifact_marker["ir_revision_id"] == payload["rendered_from_ir_revision_id"],
            f"{case_name}: {renderer_format} rendered IR revision drifted",
        )
        assert_true(
            artifact_marker["backported_to_ir_revision_id"] == payload["backported_to_ir_revision_id"],
            f"{case_name}: {renderer_format} backport target revision drifted",
        )
        assert_true(artifact_marker["renderer_format"] == renderer_format, f"{case_name}: {renderer_format} marker format mismatch")
        assert_true(artifact_marker["manual_edit_status"] == "backported", f"{case_name}: {renderer_format} marker must stay backported")
        assert_true(
            artifact_marker["canonical_locations"] == EXPECTED_CANONICAL_LOCATIONS,
            f"{case_name}: {renderer_format} canonical marker locations drifted",
        )


def main() -> None:
    schema = load_json(BACKPORT_SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)
    valid_fixture = load_json(FIXTURE_PATH)

    validate_renderer_parity(validator, valid_fixture, "valid_fixture")

    content_mismatch_fails = copy.deepcopy(valid_fixture)
    content_mismatch_fails["required_content"][1]["text"] = "학습 목표: 지역 문제를 한 문장으로만 말한다."

    provenance_marker_mismatch_fails = copy.deepcopy(valid_fixture)
    provenance_marker_mismatch_fails["provenance_markers"][0]["label"] = "[from-curriculum:web]"

    unresolved_boundary_marker_mismatch_fails = copy.deepcopy(valid_fixture)
    unresolved_boundary_marker_mismatch_fails["unresolved_boundary_markers"] = [
        {"boundary_id": "tj-local-example", "indicator_text": "교사 확인 필요", "detail_text": "지역 사례와 학교별 현장 맥락은 교사가 최종 확정해야 함"}
    ]
    unresolved_boundary_marker_mismatch_fails["renders"][0]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][0]["artifact_path"]))
    unresolved_boundary_marker_mismatch_fails["renders"][0]["artifact_override"]["unresolved_boundary_markers"] = copy.deepcopy(unresolved_boundary_marker_mismatch_fails["unresolved_boundary_markers"])

    format_order_drift_fails = copy.deepcopy(valid_fixture)
    format_order_drift_fails["renders"][0], format_order_drift_fails["renders"][1] = (
        format_order_drift_fails["renders"][1],
        format_order_drift_fails["renders"][0],
    )

    canonical_hwpx_marker_location_drift_fails = copy.deepcopy(valid_fixture)
    canonical_hwpx_marker_location_drift_fails["renders"][0]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][0]["artifact_path"]))
    canonical_hwpx_marker_location_drift_fails["renders"][0]["artifact_override"]["embedded_backport_marker_locator"] = "markers/kteacher-backport-marker.json"

    canonical_docx_marker_location_drift_fails = copy.deepcopy(valid_fixture)
    canonical_docx_marker_location_drift_fails["renders"][1]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][1]["artifact_path"]))
    canonical_docx_marker_location_drift_fails["renders"][1]["artifact_override"]["embedded_backport_marker_locator"] = "/customXml/alternate-marker.json"

    canonical_html_marker_location_drift_fails = copy.deepcopy(valid_fixture)
    canonical_html_marker_location_drift_fails["renders"][2]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][2]["artifact_path"]))
    canonical_html_marker_location_drift_fails["renders"][2]["artifact_override"]["embedded_backport_marker_locator"] = "script#alternate-marker"

    embedded_marker_payload_drift_hwpx_fails = copy.deepcopy(valid_fixture)
    embedded_marker_payload_drift_hwpx_fails["renders"][0]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][0]["artifact_path"]))
    embedded_marker_payload_drift_hwpx_fails["renders"][0]["artifact_override"]["embedded_backport_marker"]["backported_to_ir_revision_id"] = "rev-1999"

    embedded_marker_payload_drift_docx_fails = copy.deepcopy(valid_fixture)
    embedded_marker_payload_drift_docx_fails["renders"][1]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][1]["artifact_path"]))
    embedded_marker_payload_drift_docx_fails["renders"][1]["artifact_override"]["embedded_backport_marker"]["backported_to_ir_revision_id"] = "rev-1999"

    embedded_marker_payload_drift_html_fails = copy.deepcopy(valid_fixture)
    embedded_marker_payload_drift_html_fails["renders"][2]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][2]["artifact_path"]))
    embedded_marker_payload_drift_html_fails["renders"][2]["artifact_override"]["embedded_backport_marker"]["backported_to_ir_revision_id"] = "rev-1999"

    expect_semantic_rejection(validator, content_mismatch_fails, "content_mismatch_fails")
    expect_semantic_rejection(validator, provenance_marker_mismatch_fails, "provenance_marker_mismatch_fails")
    expect_semantic_rejection(validator, unresolved_boundary_marker_mismatch_fails, "unresolved_boundary_marker_mismatch_fails")
    expect_semantic_rejection(validator, format_order_drift_fails, "format_order_drift_fails")
    expect_semantic_rejection(validator, canonical_hwpx_marker_location_drift_fails, "canonical_hwpx_marker_location_drift_fails")
    expect_semantic_rejection(validator, canonical_docx_marker_location_drift_fails, "canonical_docx_marker_location_drift_fails")
    expect_semantic_rejection(validator, canonical_html_marker_location_drift_fails, "canonical_html_marker_location_drift_fails")
    expect_semantic_rejection(validator, embedded_marker_payload_drift_hwpx_fails, "embedded_marker_payload_drift_hwpx_fails")
    expect_semantic_rejection(validator, embedded_marker_payload_drift_docx_fails, "embedded_marker_payload_drift_docx_fails")
    expect_semantic_rejection(validator, embedded_marker_payload_drift_html_fails, "embedded_marker_payload_drift_html_fails")

    workflow_id_drift_fails = copy.deepcopy(valid_fixture)
    workflow_id_drift_fails["workflow_id"] = "workflow-drifted"

    embedded_marker_workflow_drift_hwpx_fails = copy.deepcopy(valid_fixture)
    embedded_marker_workflow_drift_hwpx_fails["renders"][0]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][0]["artifact_path"]))
    embedded_marker_workflow_drift_hwpx_fails["renders"][0]["artifact_override"]["embedded_backport_marker"]["workflow_id"] = "workflow-drifted"

    embedded_marker_workflow_drift_docx_fails = copy.deepcopy(valid_fixture)
    embedded_marker_workflow_drift_docx_fails["renders"][1]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][1]["artifact_path"]))
    embedded_marker_workflow_drift_docx_fails["renders"][1]["artifact_override"]["embedded_backport_marker"]["workflow_id"] = "workflow-drifted"

    embedded_marker_workflow_drift_html_fails = copy.deepcopy(valid_fixture)
    embedded_marker_workflow_drift_html_fails["renders"][2]["artifact_override"] = copy.deepcopy(load_json(ROOT / valid_fixture["renders"][2]["artifact_path"]))
    embedded_marker_workflow_drift_html_fails["renders"][2]["artifact_override"]["embedded_backport_marker"]["workflow_id"] = "workflow-drifted"

    expect_semantic_rejection(validator, workflow_id_drift_fails, "workflow_id_drift_fails")
    expect_semantic_rejection(validator, embedded_marker_workflow_drift_hwpx_fails, "embedded_marker_workflow_drift_hwpx_fails")
    expect_semantic_rejection(validator, embedded_marker_workflow_drift_docx_fails, "embedded_marker_workflow_drift_docx_fails")
    expect_semantic_rejection(validator, embedded_marker_workflow_drift_html_fails, "embedded_marker_workflow_drift_html_fails")

    json_mode = "--json" in sys.argv[1:]
    if json_mode:
        print(json.dumps({
            "status": "VALIDATION_OK",
            "format_drift_cases_by_format": FORMAT_DRIFT_CASES_BY_FORMAT,
        }, ensure_ascii=False))
    else:
        print("validated 15 renderer-parity cases")
        print("- valid_fixture: extracted Korean HWPX/DOCX/HTML artifacts keep required content, provenance, unresolved-boundary markers, embedded marker payloads, and backport references aligned")
        print("- content_mismatch_fails: per-format content drift is rejected fail-closed")
        print("- provenance_marker_mismatch_fails: per-format provenance label drift is rejected fail-closed")
        print("- unresolved_boundary_marker_mismatch_fails: per-format unresolved-boundary indicator drift is rejected fail-closed")
        print("- format_order_drift_fails: renderer publication order drift is rejected fail-closed")
        print("- canonical_hwpx_marker_location_drift_fails: alternate HWPX embedded backport-marker locations are rejected fail-closed")
        print("- canonical_docx_marker_location_drift_fails: alternate DOCX embedded backport-marker locations are rejected fail-closed")
        print("- canonical_html_marker_location_drift_fails: alternate HTML embedded backport-marker locations are rejected fail-closed")
        print("- embedded_marker_payload_drift_hwpx_fails: extracted HWPX marker payload drift is rejected fail-closed")
        print("- embedded_marker_payload_drift_docx_fails: extracted DOCX marker payload drift is rejected fail-closed")
        print("- embedded_marker_payload_drift_html_fails: extracted HTML marker payload drift is rejected fail-closed")
        print("- workflow_id_drift_fails: top-level parity workflow drift is rejected fail-closed")
        print("- embedded_marker_workflow_drift_hwpx_fails: embedded HWPX marker workflow drift is rejected fail-closed")
        print("- embedded_marker_workflow_drift_docx_fails: embedded DOCX marker workflow drift is rejected fail-closed")
        print("- embedded_marker_workflow_drift_html_fails: embedded HTML marker workflow drift is rejected fail-closed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
