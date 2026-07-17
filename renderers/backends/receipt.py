"""Provenance receipt for a backend render decision (written under artifacts/, ignored)."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any

from .base import CapabilityReport

PINNED_HWPX_MCP_SERVER = "4.0.0"
PINNED_PYTHON_HWPX = "3.1.0"


def _dist_version(dist_name: str) -> str | None:
    try:
        return version(dist_name)
    except PackageNotFoundError:
        return None


def build_backend_receipt(
    *,
    backend: str,
    delivered_path: str | None,
    capability: CapabilityReport,
    source_fingerprint: str | None = None,
) -> dict[str, Any]:
    mcp_version = _dist_version("hwpx-mcp-server")
    hwpx_version = _dist_version("python-hwpx")
    pinned = mcp_version == PINNED_HWPX_MCP_SERVER and hwpx_version == PINNED_PYTHON_HWPX
    return {
        "receipt_version": "kteacher.hwpx-backend-receipt.v1",
        "backend": backend,
        "delivered_path": delivered_path,
        "hwpx_mcp_server_version": mcp_version,
        "python_hwpx_version": hwpx_version,
        "pinned": pinned,
        "no_silent_fallback": True,
        "source_fingerprint": source_fingerprint,
        "capability": capability.as_dict(),
    }


__all__ = ["build_backend_receipt", "PINNED_HWPX_MCP_SERVER", "PINNED_PYTHON_HWPX"]
