"""Default HWPX backend: the proven python-hwpx builder path (positive control).

This backend is unchanged behaviour — it delegates to the existing
``renderers.render.render_hwpx`` builder implementation and is the byte/behaviour
baseline for the 12-file classroom bundle.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BackendReceipt, CapabilityReport, HwpxBackend
from .capability_probe import probe_file


class BuilderBackend(HwpxBackend):
    name = "builder"

    def available(self) -> tuple[bool, str]:
        try:
            import hwpx.builder  # noqa: F401

            return True, "python-hwpx builder available"
        except ImportError:
            return (
                False,
                "python-hwpx is required to render production HWPX. "
                "Install render dependencies: pip install -r requirements-render.txt",
            )

    def render(self, canonical: dict, marker: dict, path: str | Path) -> BackendReceipt:
        # Import here to avoid a circular import at module load.
        from ..render import render_hwpx

        path = Path(path)
        render_hwpx(canonical, marker, path)  # DEFAULT path, unchanged
        # expected_breaks=0: the builder receipt's capable flag is nominal — the
        # default classroom path short-circuits inline in render_hwpx and never
        # dispatches through this backend, so this receipt is informational only.
        report = self.probe_capabilities(path, expected_breaks=0)
        return BackendReceipt(backend=self.name, delivered_path=str(path), capability=report)

    def probe_capabilities(
        self, path: str | Path, expected_breaks: int, **kwargs: Any
    ) -> CapabilityReport:
        return probe_file(path, expected_breaks, **kwargs)


__all__ = ["BuilderBackend"]
