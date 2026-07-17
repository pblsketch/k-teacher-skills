"""Backend contracts for pluggable HWPX authoring.

Physical-truth-only capability model. A backend is only "capable" when the SAVED
package materializes the requested page breaks (``pageBreak="1"`` on ``<hp:p>`` in
``Contents/section0.xml``), never on a server self-report. Fail-closed by design.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CapabilityReport:
    """Result of a PHYSICAL capability probe against a produced HWPX package."""

    capable: bool
    physical_page_break_count: int
    page_count: int | None = None
    open_safety_ok: bool | None = None
    quality_page_break_count: int | None = None
    reasons: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "capable": self.capable,
            "physical_page_break_count": self.physical_page_break_count,
            "page_count": self.page_count,
            "open_safety_ok": self.open_safety_ok,
            "quality_page_break_count": self.quality_page_break_count,
            "reasons": list(self.reasons),
            "evidence": dict(self.evidence),
        }


@dataclass
class BackendReceipt:
    """What a backend actually delivered (or refused to deliver)."""

    backend: str
    delivered_path: str | None
    capability: CapabilityReport
    manifest: dict[str, Any] = field(default_factory=dict)


class HwpxBackendNotCapable(RuntimeError):
    """Raised when an experimental backend cannot PHYSICALLY materialize output.

    Carries the failing :class:`CapabilityReport` so callers can log the exact
    physical/self-report contradiction. The default builder backend is NEVER
    invoked as a fallback — the caller decides explicitly.
    """

    def __init__(self, message: str, *, report: CapabilityReport | None = None) -> None:
        super().__init__(message)
        self.report = report


class HwpxBackend(abc.ABC):
    """Abstract HWPX authoring backend."""

    name: str = "hwpx-backend"

    @abc.abstractmethod
    def available(self) -> tuple[bool, str]:
        """Return ``(is_available, reason)``. Reason carries a remediation line
        (exact install command) when unavailable."""

    @abc.abstractmethod
    def render(self, canonical: dict, marker: dict, path: str | Path) -> BackendReceipt:
        """Author a real HWPX package at ``path`` or fail closed. Never returns a
        partial/placeholder artifact; never silently falls back to another backend."""

    @abc.abstractmethod
    def probe_capabilities(
        self, path: str | Path, expected_breaks: int, **kwargs: Any
    ) -> CapabilityReport:
        """Physically probe a produced package/section for page-break materialization."""


__all__ = [
    "CapabilityReport",
    "BackendReceipt",
    "HwpxBackend",
    "HwpxBackendNotCapable",
]
