"""Experimental HWPX backend via the MCP ``create_document_from_plan`` codepath.

EXPERIMENTAL, OPTIONAL, FAIL-CLOSED. Requires the pinned optional deps
(``requirements-render-experimental.txt``: hwpx-mcp-server==4.0.0, python-hwpx==3.1.0).

Flow: canonical -> deterministic document_plan (adapter) -> server plan validation ->
MCP create_document_from_plan -> MANDATORY physical capability probe. If the SAVED
package does not materialize the requested page breaks, raise ``HwpxBackendNotCapable``,
write NO delivered artifact, and NEVER fall back to the builder or patch raw XML.
"""
from __future__ import annotations

import json
import tempfile
import zipfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from .base import BackendReceipt, CapabilityReport, HwpxBackend, HwpxBackendNotCapable
from .capability_probe import probe_file
from .document_plan_adapter import canonical_to_document_plan
from .receipt import build_backend_receipt

_INSTALL_LINE = "pip install -r requirements-render-experimental.txt"
_REQUIRED_DISTRIBUTIONS = {
    "hwpx-mcp-server": "4.0.0",
    "python-hwpx": "3.1.0",
}


def _expected_breaks(canonical: dict) -> int:
    return sum(1 for b in canonical.get("blocks", []) if b.get("block_type") == "page_break")


def _structured_preview(result: Any) -> dict | None:
    """Normalize FastMCP CallToolResult/dict preview responses for the probe."""
    if isinstance(result, dict):
        return result
    structured = getattr(result, "structuredContent", None)
    return structured if isinstance(structured, dict) else None


def _workspace_staging_root() -> Path:
    """Use the pinned server's environment parser as the single root authority."""
    from hwpx_mcp_server.workspace import WorkspaceResolver

    return WorkspaceResolver.from_environment().primary_root


class DocumentPlanBackend(HwpxBackend):
    name = "document_plan"

    def available(self) -> tuple[bool, str]:
        missing: list[str] = []
        try:
            import hwpx  # noqa: F401
        except ImportError:
            missing.append("python-hwpx==3.1.0")
        try:
            import hwpx_mcp_server.server  # noqa: F401
        except ImportError:
            missing.append("hwpx-mcp-server==4.0.0")
        mismatched: list[str] = []
        for distribution, required in _REQUIRED_DISTRIBUTIONS.items():
            try:
                actual = version(distribution)
            except PackageNotFoundError:
                continue
            if actual != required:
                mismatched.append(f"{distribution}=={actual} (requires =={required})")
        if missing:
            return (
                False,
                f"experimental document_plan backend requires {', '.join(missing)}; "
                f"install pinned optional deps: {_INSTALL_LINE}",
            )
        if mismatched:
            return (
                False,
                "experimental document_plan backend version mismatch: "
                f"{', '.join(mismatched)}; install exact pins: {_INSTALL_LINE}",
            )
        return (
            True,
            "exact experimental HWPX deps available: "
            "hwpx-mcp-server==4.0.0, python-hwpx==3.1.0",
        )

    def probe_capabilities(
        self, path: str | Path, expected_breaks: int, **kwargs: Any
    ) -> CapabilityReport:
        return probe_file(path, expected_breaks, **kwargs)

    def render(self, canonical: dict, marker: dict, path: str | Path) -> BackendReceipt:
        path = Path(path)
        ok, reason = self.available()
        if not ok:
            raise HwpxBackendNotCapable(
                reason,
                report=CapabilityReport(
                    capable=False, physical_page_break_count=0, reasons=[reason]
                ),
            )

        plan = canonical_to_document_plan(canonical)
        expected = _expected_breaks(canonical)

        from hwpx.authoring import validate_document_plan  # authoritative validation

        validation = validate_document_plan(plan)
        if not validation.ok:
            raise HwpxBackendNotCapable(
                f"document_plan failed server validation: {validation.to_dict().get('errors')}",
                report=CapabilityReport(
                    capable=False,
                    physical_page_break_count=0,
                    reasons=["plan_validation.ok is false"],
                    evidence={"plan_validation": validation.to_dict()},
                ),
            )

        from hwpx_mcp_server import server as mcp_server

        with tempfile.TemporaryDirectory(
            prefix=".hwpx-mcp-", dir=str(_workspace_staging_root())
        ) as workdir:
            staged = Path(workdir) / "document-plan.hwpx"
            receipt = mcp_server.create_document_from_plan(
                str(staged), plan, verbosity="full"
            )

            if not receipt.get("created") or not staged.exists():
                report = CapabilityReport(
                    capable=False,
                    physical_page_break_count=0,
                    reasons=[f"MCP did not create a package: {receipt.get('error')}"],
                    evidence={"receipt": receipt},
                )
                raise HwpxBackendNotCapable("MCP create_document_from_plan did not produce a package", report=report)

            # Add the same marker/content members that will be delivered before
            # previewing or probing. The governing capability report must describe
            # the exact candidate bytes, not the pre-injection MCP package.
            from ..render import _HWPX_CONTENT, _HWPX_MARKER, _content_sidecar_xml

            with zipfile.ZipFile(staged, "a", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(_HWPX_MARKER, json.dumps(marker, ensure_ascii=False))
                archive.writestr(_HWPX_CONTENT, _content_sidecar_xml(canonical))

            preview: dict | None = None
            try:
                preview_result = mcp_server.render_preview(
                    str(staged),
                    output_dir=str(Path(workdir) / "preview"),
                    max_pages=max(expected + 1, 1),
                    embed_images=False,
                )
                preview = _structured_preview(preview_result)
            except (ImportError, OSError, RuntimeError, ValueError):
                # Physical saved-package evidence remains the governing gate.
                # Preview corroborates when available but screenshot/browser
                # configuration must not decide package open-safety.
                preview = None

            report = self.probe_capabilities(
                staged,
                expected_breaks=expected,
                receipt=receipt,
                preview=preview,
                expected_pages=expected + 1,
            )

            if not report.capable:
                # Fail closed: NO delivered artifact at `path`, NO builder fallback,
                # NO raw-XML patch. The staged temp package is discarded with workdir.
                raise HwpxBackendNotCapable(
                    "document_plan backend cannot physically materialize page breaks "
                    f"(expected {expected}); refusing to deliver. Reasons: {report.reasons}. "
                    "Use the default 'builder' backend for classroom output.",
                    report=report,
                )

            # Capable: copy the already-injected, already-probed candidate bytes.
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(staged.read_bytes())

        manifest = build_backend_receipt(
            backend=self.name,
            delivered_path=str(path),
            capability=report,
            source_fingerprint=str(marker.get("content_fingerprint")),
        )
        self._write_provenance(path, manifest)
        return BackendReceipt(
            backend=self.name, delivered_path=str(path), capability=report, manifest=manifest
        )

    @staticmethod
    def _write_provenance(path: Path, manifest: dict) -> None:
        try:
            artifacts = Path("artifacts") / "hwpx-backend"
            artifacts.mkdir(parents=True, exist_ok=True)
            (artifacts / f"{path.stem}.receipt.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
            )
        except OSError:
            return  # provenance is best-effort; never blocks a capable delivery


__all__ = ["DocumentPlanBackend"]
