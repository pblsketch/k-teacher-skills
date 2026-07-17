"""Minimal own HWPX/DOCX/HTML renderer derived from a single canonical IR."""
from .render import (
    render_all,
    render_package,
    extract_all,
    extract_hwpx,
    extract_docx,
    extract_html,
    verify_parity,
    canonical_content,
    content_fingerprint,
    build_marker,
    CANONICAL_LOCATIONS,
)
from .backends import (
    select_hwpx_backend,
    HwpxBackendNotCapable,
    CapabilityReport,
    DEFAULT_BACKEND,
)

__all__ = [
    "render_all",
    "render_package",
    "extract_all",
    "extract_hwpx",
    "extract_docx",
    "extract_html",
    "verify_parity",
    "canonical_content",
    "content_fingerprint",
    "build_marker",
    "CANONICAL_LOCATIONS",
    "select_hwpx_backend",
    "HwpxBackendNotCapable",
    "CapabilityReport",
    "DEFAULT_BACKEND",
]
