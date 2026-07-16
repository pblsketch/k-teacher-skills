"""Minimal own HWPX/DOCX/HTML renderer derived from a single canonical IR."""
from .render import (
    render_all,
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

__all__ = [
    "render_all",
    "extract_all",
    "extract_hwpx",
    "extract_docx",
    "extract_html",
    "verify_parity",
    "canonical_content",
    "content_fingerprint",
    "build_marker",
    "CANONICAL_LOCATIONS",
]
