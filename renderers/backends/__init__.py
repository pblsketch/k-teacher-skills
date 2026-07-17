"""Pluggable HWPX authoring backends (additive; default-preserving).

`builder` is the DEFAULT and unchanged. `document_plan` is EXPERIMENTAL, OPTIONAL,
and fail-closed behind a physical capability probe. Selection never imports heavy
optional deps for the default path.
"""
from __future__ import annotations

from .base import (
    BackendReceipt,
    CapabilityReport,
    HwpxBackend,
    HwpxBackendNotCapable,
)

DEFAULT_BACKEND = "builder"
_REGISTRY = {"builder", "document_plan"}


def select_hwpx_backend(name: str | None = None) -> HwpxBackend:
    """Return the backend for ``name`` (``None`` -> the default ``builder``).

    Unknown names raise ``ValueError`` listing the valid registry names. Backend
    modules are imported lazily so the default path never triggers optional deps.
    """
    resolved = DEFAULT_BACKEND if name is None else name
    if resolved not in _REGISTRY:
        valid = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"unknown hwpx backend {name!r}; valid backends: {valid}")
    if resolved == "builder":
        from .builder_backend import BuilderBackend

        return BuilderBackend()
    from .document_plan_backend import DocumentPlanBackend

    return DocumentPlanBackend()


__all__ = [
    "DEFAULT_BACKEND",
    "select_hwpx_backend",
    "HwpxBackend",
    "HwpxBackendNotCapable",
    "CapabilityReport",
    "BackendReceipt",
]
