from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "kteacher-backport-marker.schema.json"
FIXTURE_DIR = ROOT / "tests" / "golden" / "backport-marker"
VALID_FIXTURE_PATH = FIXTURE_DIR / "valid.json"
DRIFTED_FIXTURE_PATH = FIXTURE_DIR / "drifted.json"
RENDERER_PARITY_FIXTURE_PATH = ROOT / "tests" / "golden" / "renderer-parity" / "valid.json"

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
    "hwpx": ["invalid_hwpx_location_fails"],
    "docx": ["invalid_docx_location_fails"],
    "html": ["invalid_html_location_fails"],
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


def expect_invalid(validator: jsonschema.Draft202012Validator, payload: dict, case_name: str) -> None:
    error = first_error(validator, payload)
    assert_true(error is not None, f"{case_name}: expected invalid but schema accepted payload")


def require_schema_contract(schema: dict) -> None:
    required = set(schema.get("required", []))
    assert_true(
        {
            "ir_revision_id",
            "render_revision_id",
            "renderer_format",
            "manual_edit_status",
            "backported_to_ir_revision_id",
            "canonical_locations",
        }.issubset(required),
        "schema must require revision linkage, lifecycle state, and canonical locations",
    )
    assert_true(schema.get("properties", {}).get("authoritative_source", {}).get("const") == "json-ir", "authoritative_source must stay json-ir")
    assert_true(
        schema.get("properties", {}).get("renderer_format", {}).get("enum") == ["hwpx", "docx", "html"],
        "renderer_format enum mismatch",
    )
    assert_true(
        schema.get("properties", {}).get("manual_edit_status", {}).get("enum") == ["unmodified", "modified-after-render", "backported"],
        "manual_edit_status enum mismatch",
    )
    comment = schema.get("$comment", "")
    assert_true("No alternate locations are valid" in comment, "schema must freeze canonical extraction points")

    lifecycle_rules = schema.get("allOf", [])
    assert_true(len(lifecycle_rules) == 2, "schema must publish fail-closed lifecycle rules")
    backported_rule = lifecycle_rules[0]
    assert_true(
        backported_rule.get("if", {}).get("properties", {}).get("manual_edit_status", {}).get("const") == "backported",
        "backported lifecycle rule missing",
    )
    assert_true(
        backported_rule.get("then", {}).get("properties", {}).get("backported_to_ir_revision_id", {}).get("$ref") == "#/$defs/irRevisionId",
        "backported lifecycle must require an IR revision id",
    )
    drift_rule = lifecycle_rules[1]
    assert_true(
        drift_rule.get("if", {}).get("properties", {}).get("manual_edit_status", {}).get("enum") == ["unmodified", "modified-after-render"],
        "drift lifecycle rule mismatch",
    )
    assert_true(
        drift_rule.get("then", {}).get("properties", {}).get("backported_to_ir_revision_id", {}).get("type") == "null",
        "drift lifecycle must stay null until backported",
    )


def validate_marker_semantics(marker: dict, case_name: str) -> None:
    assert_true(marker["canonical_locations"] == EXPECTED_CANONICAL_LOCATIONS, f"{case_name}: canonical_locations drifted")
    assert_true(
        marker["renderer_format"] in marker["canonical_locations"],
        f"{case_name}: renderer_format must map to a canonical validator location",
    )
    assert_true(
        marker["ir_revision_id"] != marker["render_revision_id"],
        f"{case_name}: render_revision_id must remain distinct from ir_revision_id",
    )
    if marker["manual_edit_status"] == "backported":
        target_revision = marker["backported_to_ir_revision_id"]
        assert_true(target_revision is not None, f"{case_name}: backported marker must record the receiving IR revision")
        assert_true(
            revision_number(target_revision) > revision_number(marker["ir_revision_id"]),
            f"{case_name}: backport target must advance beyond the rendered IR revision",
        )
    else:
        assert_true(marker["backported_to_ir_revision_id"] is None, f"{case_name}: non-backported marker must keep backported_to_ir_revision_id null")


def revision_number(revision_id: str) -> int:
    return int(revision_id.split("-", 1)[1])


def validate_drift_blocker(marker: dict, case_name: str) -> None:
    assert_true(marker["manual_edit_status"] == "modified-after-render", f"{case_name}: fixture must exercise manual-edit drift")
    assert_true(marker["backported_to_ir_revision_id"] is None, f"{case_name}: drifted marker must stay unbackported")


def validate_renderer_parity_markers(
    validator: jsonschema.Draft202012Validator,
    parity_fixture: dict,
    case_name: str,
) -> None:
    assert_true(
        parity_fixture["expected_render_targets"] == ["hwpx", "docx", "html"],
        f"{case_name}: expected_render_targets drifted",
    )
    renders = parity_fixture["renders"]
    assert_true(len(renders) == 3, f"{case_name}: renderer parity fixture must cover three stage-1 renderers")
    for render in renders:
        renderer_format = render["renderer_format"]
        marker = render["backport_marker"]
        expect_valid(validator, marker, f"{case_name}:{renderer_format}:schema")
        validate_marker_semantics(marker, f"{case_name}:{renderer_format}")
        assert_true(marker["renderer_format"] == renderer_format, f"{case_name}: {renderer_format} marker format drifted")
        assert_true(marker["workflow_id"] == parity_fixture["workflow_id"], f"{case_name}: {renderer_format} workflow_id drifted")
        assert_true(marker["ir_id"] == parity_fixture["ir_id"], f"{case_name}: {renderer_format} ir_id drifted")
        assert_true(
            marker["ir_revision_id"] == parity_fixture["rendered_from_ir_revision_id"],
            f"{case_name}: {renderer_format} rendered IR revision drifted",
        )
        assert_true(
            marker["backported_to_ir_revision_id"] == parity_fixture["backported_to_ir_revision_id"],
            f"{case_name}: {renderer_format} backport target revision drifted",
        )


def expect_semantic_rejection(marker: dict, case_name: str) -> None:
    try:
        validate_marker_semantics(marker, case_name)
    except AssertionError:
        return
    raise AssertionError(f"{case_name}: expected semantic rejection")


def main() -> None:
    schema = load_json(SCHEMA_PATH)
    require_schema_contract(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)

    valid_marker = load_json(VALID_FIXTURE_PATH)
    drifted_marker = load_json(DRIFTED_FIXTURE_PATH)
    renderer_parity_fixture = load_json(RENDERER_PARITY_FIXTURE_PATH)

    expect_valid(validator, valid_marker, "valid_fixture")
    validate_marker_semantics(valid_marker, "valid_fixture")

    expect_valid(validator, drifted_marker, "drifted_fixture")
    validate_marker_semantics(drifted_marker, "drifted_fixture")
    validate_drift_blocker(drifted_marker, "drifted_fixture")

    validate_renderer_parity_markers(validator, renderer_parity_fixture, "renderer_parity_fixture")


    invalid_hwpx_location_fails = copy.deepcopy(valid_marker)
    invalid_hwpx_location_fails["canonical_locations"]["hwpx"]["locator_value"] = "markers/kteacher-backport-marker.json"

    invalid_docx_location_fails = copy.deepcopy(valid_marker)
    invalid_docx_location_fails["canonical_locations"]["docx"]["locator_value"] = "/customXml/alternate-marker.json"

    invalid_html_location_fails = copy.deepcopy(valid_marker)
    invalid_html_location_fails["canonical_locations"]["html"]["locator_value"] = "script#alternate-marker"

    unmodified_with_backport_target_fails = copy.deepcopy(valid_marker)
    unmodified_with_backport_target_fails["manual_edit_status"] = "unmodified"

    drifted_with_backport_target_fails = copy.deepcopy(drifted_marker)
    drifted_with_backport_target_fails["backported_to_ir_revision_id"] = "rev-1001"

    backported_without_target_fails = copy.deepcopy(valid_marker)
    backported_without_target_fails["backported_to_ir_revision_id"] = None

    backported_same_revision_fails = copy.deepcopy(valid_marker)
    backported_same_revision_fails["backported_to_ir_revision_id"] = backported_same_revision_fails["ir_revision_id"]

    backported_older_revision_fails = copy.deepcopy(valid_marker)
    backported_older_revision_fails["backported_to_ir_revision_id"] = "rev-0999"

    expect_invalid(validator, invalid_hwpx_location_fails, "invalid_hwpx_location_fails")
    expect_invalid(validator, invalid_docx_location_fails, "invalid_docx_location_fails")
    expect_invalid(validator, invalid_html_location_fails, "invalid_html_location_fails")
    expect_invalid(validator, unmodified_with_backport_target_fails, "unmodified_with_backport_target_fails")
    expect_invalid(validator, drifted_with_backport_target_fails, "drifted_with_backport_target_fails")
    expect_invalid(validator, backported_without_target_fails, "backported_without_target_fails")
    expect_valid(validator, backported_same_revision_fails, "backported_same_revision_fails_schema")
    expect_semantic_rejection(backported_same_revision_fails, "backported_same_revision_fails")
    expect_valid(validator, backported_older_revision_fails, "backported_older_revision_fails_schema")
    expect_semantic_rejection(backported_older_revision_fails, "backported_older_revision_fails")

    json_mode = "--json" in sys.argv[1:]
    if json_mode:
        print(json.dumps({
            "status": "VALIDATION_OK",
            "format_drift_cases_by_format": FORMAT_DRIFT_CASES_BY_FORMAT,
        }, ensure_ascii=False))
    else:
        print("validated 11 backport-marker cases")
        print("- valid_fixture: canonical marker records fixed validator locations and teacher-approved backport linkage")
        print("- drifted_fixture: manual edit drift remains representable but blocked until a newer IR revision absorbs edits")
        print("- renderer_parity_fixture: HWPX/DOCX/HTML parity fixture keeps per-format markers on the canonical revision-linked backport path")
        print("- invalid_hwpx_location_fails: alternate HWPX marker locations are rejected fail-closed")
        print("- invalid_docx_location_fails: alternate DOCX marker locations are rejected fail-closed")
        print("- invalid_html_location_fails: alternate HTML marker locations are rejected fail-closed")
        print("- unmodified_with_backport_target_fails: unmodified markers cannot claim a backport target")
        print("- drifted_with_backport_target_fails: modified-after-render markers cannot skip directly to a backport target")
        print("- backported_without_target_fails: backported markers must point at the receiving IR revision")
        print("- backported_same_revision_fails: semantic validation rejects same-revision backport drift masquerading as a real backport")
        print("- backported_older_revision_fails: semantic validation rejects older receiving revisions that do not advance the IR")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
