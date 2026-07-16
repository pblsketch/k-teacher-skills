from __future__ import annotations

import contextlib
import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_skill_pack  # noqa: E402

PLUGIN_PATH = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_PATH = ROOT / ".claude-plugin" / "marketplace.json"
REGISTRY_PATH = ROOT / "registry" / "routing-gate-registry.json"


class MutationGuard:
    """Temporarily rewrite a file and guarantee exact byte restoration.

    The original bytes are captured on enter and rewritten verbatim on exit,
    even when the body raises. No git operation (restore/reset/stash/checkout)
    is ever used; restoration is a plain byte write-back.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.original = b""

    def __enter__(self) -> "MutationGuard":
        self.original = self.path.read_bytes()
        return self

    def data(self) -> dict:
        return json.loads(self.original.decode("utf-8"))

    def write_json(self, payload: object) -> None:
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def __exit__(self, *exc: object) -> bool:
        self.path.write_bytes(self.original)
        return False


@contextlib.contextmanager
def _suppress_stdout():
    with open(os.devnull, "w", encoding="utf-8") as devnull, contextlib.redirect_stdout(devnull):
        yield


def expect_validation_failure(case_name: str) -> None:
    """Run validate_skill_pack.main() and require a fail-closed AssertionError."""
    try:
        with _suppress_stdout():
            validate_skill_pack.main()
    except AssertionError:
        return
    except Exception as error:  # noqa: BLE001 - surface unexpected error types
        raise AssertionError(
            f"{case_name}: expected fail-closed AssertionError, "
            f"got {type(error).__name__}: {error}"
        )
    raise AssertionError(
        f"{case_name}: validate_skill_pack accepted a mutated public surface "
        f"that should have failed closed"
    )


def run_h1_plugin_path_drift() -> None:
    with MutationGuard(PLUGIN_PATH) as guard:
        data = guard.data()
        data["skills"][3] = "./skills/lesson-design/does-not-exist/"
        guard.write_json(data)
        expect_validation_failure("plugin_17_skill_path_drift")


def run_h1_plugin_scalar_drift() -> None:
    with MutationGuard(PLUGIN_PATH) as guard:
        data = guard.data()
        data["description"] = "drifted plugin description not owned by the registry"
        guard.write_json(data)
        expect_validation_failure("plugin_description_drift")


def run_h1_marketplace_cardinality_drift() -> None:
    with MutationGuard(MARKETPLACE_PATH) as guard:
        data = guard.data()
        data["plugins"].append(copy.deepcopy(data["plugins"][0]))
        guard.write_json(data)
        expect_validation_failure("marketplace_single_plugin_cardinality")


def run_h1_marketplace_tags_order_drift() -> None:
    with MutationGuard(MARKETPLACE_PATH) as guard:
        data = guard.data()
        data["plugins"][0]["tags"] = list(reversed(data["plugins"][0]["tags"]))
        guard.write_json(data)
        expect_validation_failure("marketplace_tags_order_drift")


def run_h1_marketplace_source_drift() -> None:
    with MutationGuard(MARKETPLACE_PATH) as guard:
        data = guard.data()
        data["plugins"][0]["source"] = "../elsewhere/"
        guard.write_json(data)
        expect_validation_failure("marketplace_source_drift")


def run_m1_registry_gate_drift() -> None:
    with MutationGuard(REGISTRY_PATH) as guard:
        data = guard.data()
        data["skills"]["grill-me-for-k-teacher"]["gate"]["tier3_mode"] = "disabled"
        guard.write_json(data)
        expect_validation_failure("registry_gate_projection_drift")


CASES = [
    run_h1_plugin_path_drift,
    run_h1_plugin_scalar_drift,
    run_h1_marketplace_cardinality_drift,
    run_h1_marketplace_tags_order_drift,
    run_h1_marketplace_source_drift,
    run_m1_registry_gate_drift,
]


def main() -> None:
    # Baseline: the untouched public surfaces must pass before any mutation.
    with _suppress_stdout():
        validate_skill_pack.main()

    plugin_before = PLUGIN_PATH.read_bytes()
    marketplace_before = MARKETPLACE_PATH.read_bytes()
    registry_before = REGISTRY_PATH.read_bytes()

    for case in CASES:
        case()

    # Exact restoration proof: every mutated file is byte-identical afterward.
    assert PLUGIN_PATH.read_bytes() == plugin_before, "plugin.json not restored exactly"
    assert MARKETPLACE_PATH.read_bytes() == marketplace_before, (
        "marketplace.json not restored exactly"
    )
    assert REGISTRY_PATH.read_bytes() == registry_before, (
        "routing-gate-registry.json not restored exactly"
    )

    # Post-restoration: the public surfaces must pass again.
    with _suppress_stdout():
        validate_skill_pack.main()

    json_mode = "--json" in sys.argv[1:]
    if json_mode:
        print(json.dumps({
            "status": "VALIDATION_OK",
            "mutation_case_count": len(CASES),
            "restored_exactly": True,
        }, ensure_ascii=False))
    else:
        print(
            f"validated {len(CASES)} public-surface mutation regressions "
            f"(H1 plugin/marketplace drift + M1 registry gate drift); "
            f"all originals restored byte-exactly"
        )
        print("- plugin_17_skill_path_drift: drifted plugin skill path fails closed against registry.plugin_projection")
        print("- plugin_description_drift: drifted plugin scalar value fails closed against registry.plugin_projection")
        print("- marketplace_single_plugin_cardinality: a second marketplace plugin entry fails closed")
        print("- marketplace_tags_order_drift: reordered marketplace tags fail closed against registry order")
        print("- marketplace_source_drift: drifted marketplace source fails closed against registry.plugin_projection")
        print("- registry_gate_projection_drift: a registry gate change without mapping/SKILL.md update fails closed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
