"""Physical capability probe (governing gate) for HWPX page-break materialization.

Reuses the repo's proven extractor logic
(``tests/validate_field_readiness.py::hwpx_pagebreaks`` =
``zipfile -> Contents/section0.xml -> xml.count('pageBreak="1"')``) — matching ONLY
``pageBreak="1"`` on ``<hp:p>`` (never ``"0"`` / ``"CELL"`` / ``columnBreak``).

Decision order:
  1. (always, governing) physical = section0 count('pageBreak="1"');
     capable requires physical >= expected_breaks.
  2. (conditional) python-hwpx present AND path is a real package -> assert
     physical == document.page_break_count (independent corroboration).
  3. (conditional, receipt-backed) REJECT the exact contradiction
     block_counts.page_break > 0 AND document.page_break_count == 0; require
     openSafety.ok (manifest version-part WARNING tolerated; ERRORS fail).
  4. (conditional, receipt/preview-backed) require pageCount >= expected_pages.
  5. NEVER read formatted / semanticDiff.changed / breakBefore.after /
     <hh:breakSetting> as capability evidence.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

from .base import CapabilityReport

_SECTION_MEMBER = "Contents/section0.xml"


def _read_section_xml(path: Path) -> str:
    """Return section0.xml text whether ``path`` is a HWPX package or a raw XML file."""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            return z.read(_SECTION_MEMBER).decode("utf-8")
    return path.read_text(encoding="utf-8")


def _physical_page_breaks(xml: str) -> int:
    # Identical semantics to validate_field_readiness.hwpx_pagebreaks. python-hwpx
    # emits pageBreak="1" ONLY on <hp:p> paragraph breaks; tables carry
    # pageBreak="CELL"/"0" and column breaks use a different attribute, so this
    # substring count matches paragraph page breaks and nothing else on real output.
    return xml.count('pageBreak="1"')


def _hwpx_importable() -> bool:
    try:
        import hwpx.document  # noqa: F401

        return True
    except ImportError:
        return False


def _library_page_break_count(path: Path) -> int | None:
    """Independent python-hwpx count (paragraphs with pageBreak=="1"); None if the
    library is absent OR the path is not a reopenable package OR reopen failed."""
    if not zipfile.is_zipfile(path):
        return None
    try:
        from hwpx.document import HwpxDocument
    except ImportError:
        return None
    try:
        import contextlib
        import io
        from hwpx.opc.package import HwpxPackageError, HwpxStructureError

        with contextlib.redirect_stderr(io.StringIO()):
            doc = HwpxDocument.open(str(path))
        return sum(1 for p in doc.paragraphs if p.element.get("pageBreak") == "1")
    except (HwpxPackageError, HwpxStructureError, OSError, ValueError, KeyError):
        return None


def _dig(mapping: Any, *keys: str) -> Any:
    cur = mapping
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _receipt_block_page_break(receipt: dict) -> int | None:
    val = _dig(receipt, "quality", "block_counts", "page_break")
    if val is None:
        val = _dig(receipt, "block_counts", "page_break")
    return int(val) if isinstance(val, (int, float)) else None


def _receipt_doc_page_break_count(receipt: dict) -> int | None:
    val = _dig(receipt, "quality", "document", "page_break_count")
    if val is None:
        val = _dig(receipt, "document", "page_break_count")
    return int(val) if isinstance(val, (int, float)) else None


def _open_safety(receipt: dict) -> tuple[bool | None, list[str]]:
    """Return (ok, blocking_errors). Version-part manifest warnings are tolerated."""
    os_report = _dig(receipt, "verification", "openSafety")
    if not isinstance(os_report, dict):
        os_report = _dig(receipt, "openSafety")
    if not isinstance(os_report, dict):
        return None, []
    ok = os_report.get("ok")
    errors: list[str] = []
    for section in ("validatePackage", "validateDocument"):
        node = os_report.get(section)
        if isinstance(node, dict):
            for key in ("errors", "validatorErrors"):
                items = node.get(key)
                if isinstance(items, list):
                    errors.extend(str(e) for e in items)
    return (ok if isinstance(ok, bool) else None), errors


def _preview_page_count(preview: dict | None, receipt: dict | None) -> int | None:
    for source in (preview, _dig(receipt or {}, "render_preview"), _dig(receipt or {}, "quality", "render_preview")):
        if isinstance(source, dict) and isinstance(source.get("pageCount"), (int, float)):
            return int(source["pageCount"])
    return None


def probe_file(
    path: str | Path,
    expected_breaks: int,
    *,
    receipt: dict | None = None,
    preview: dict | None = None,
    expected_pages: int | None = None,
) -> CapabilityReport:
    """Physically decide whether a produced HWPX materializes ``expected_breaks``.

    ``path`` may be a full ``.hwpx`` package OR a raw ``section0.xml`` file. The
    file-only mode (no receipt) decides on steps 1-2 alone, so a genuinely-capable
    builder fixture with no receipt is never wrongly rejected.
    """
    path = Path(path)
    xml = _read_section_xml(path)
    physical = _physical_page_breaks(xml)
    reasons: list[str] = []
    evidence: dict[str, Any] = {"physical_page_break_count": physical, "expected_breaks": expected_breaks}

    capable = physical >= expected_breaks
    if not capable:
        reasons.append(
            f"physical page breaks in saved section0.xml ({physical}) < expected ({expected_breaks})"
        )

    # Step 2 — independent python-hwpx corroboration (package + library present).
    lib_count = _library_page_break_count(path)
    if lib_count is not None:
        evidence["document_page_break_count"] = lib_count
        if lib_count != physical:
            capable = False
            reasons.append(
                f"python-hwpx document.page_break_count ({lib_count}) != physical ({physical})"
            )
    elif zipfile.is_zipfile(path) and _hwpx_importable():
        # A real package that python-hwpx is present for but could not reopen to
        # corroborate the physical count is treated as NOT capable (fail-closed):
        # never accept the raw substring count alone when the library is available.
        capable = False
        reasons.append(
            "python-hwpx is installed but could not reopen the saved package to "
            "corroborate the physical page-break count (fail-closed)"
        )

    quality_pbc: int | None = None
    open_safety_ok: bool | None = None

    if receipt is not None:
        block_pb = _receipt_block_page_break(receipt)
        doc_pbc = _receipt_doc_page_break_count(receipt)
        quality_pbc = doc_pbc
        evidence["receipt_block_counts_page_break"] = block_pb
        evidence["receipt_document_page_break_count"] = doc_pbc
        if doc_pbc is None:
            capable = False
            reasons.append(
                "quality.document.page_break_count is required when a receipt is supplied"
            )
        elif doc_pbc != physical:
            capable = False
            reasons.append(
                "quality document page-break count "
                f"({doc_pbc}) != saved physical page-break count ({physical})"
            )
        # Step 3 — reject the exact self-report contradiction.
        if (block_pb or 0) > 0 and doc_pbc == 0:
            capable = False
            reasons.append(
                "self-report contradiction: quality.block_counts.page_break="
                f"{block_pb} but quality.document.page_break_count=0 (saved package materializes none)"
            )
        # openSafety: ok required; version-part warnings tolerated, errors fail.
        open_safety_ok, os_errors = _open_safety(receipt)
        evidence["open_safety_ok"] = open_safety_ok
        if open_safety_ok is not True:
            capable = False
            reasons.append("openSafety.ok must be explicitly true when a receipt is supplied")
        if os_errors:
            capable = False
            reasons.append(f"openSafety reported blocking errors: {os_errors}")

    # Step 4 — preview corroboration when a page-count receipt is supplied.
    page_count = _preview_page_count(preview, receipt)
    if page_count is not None:
        evidence["page_count"] = page_count
        want_pages = expected_pages if expected_pages is not None else (expected_breaks + 1)
        if page_count < want_pages:
            capable = False
            reasons.append(f"render_preview.pageCount ({page_count}) < expected pages ({want_pages})")

    return CapabilityReport(
        capable=capable,
        physical_page_break_count=physical,
        page_count=page_count,
        open_safety_ok=open_safety_ok,
        quality_page_break_count=quality_pbc,
        reasons=reasons,
        evidence=evidence,
    )


__all__ = ["probe_file"]
