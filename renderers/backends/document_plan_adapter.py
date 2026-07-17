"""Deterministic ``canonical -> hwpx.document_plan.v1`` adapter.

Pure function of the canonical K-Teacher content model (the single source of truth).
Reuses the existing backend-neutral layout ops (``renderers.render._flow``) so the
document_plan projection stays consistent with the DEFAULT builder/DOCX/HTML output.
Deterministic: no time, no uuid; ``json.dumps(sort_keys=True, ensure_ascii=False)``
is byte-identical across runs.
"""
from __future__ import annotations

from typing import Any, TypedDict

from ..render import _flow

DOCUMENT_PLAN_SCHEMA_VERSION = "hwpx.document_plan.v1"
# Fixed ruled-answer line used to expand answer-space into writable paragraphs.
ANSWER_LINE = "_" * 60
# MCP table composition does not paint borders for rows whose cells are all
# empty/whitespace.  A short writing rule keeps observation/input rows visibly
# writable in print without changing the canonical IR or semantic sidecar.
BLANK_CELL = "────────"


class DocumentPlan(TypedDict):
    """JSON-compatible boundary shape accepted by hwpx authoring validation."""

    schemaVersion: str
    title: str
    metadata: dict[str, str]
    blocks: list[dict[str, Any]]


def _columns(labels: list[str]) -> list[dict[str, str]]:
    # col1..colN keys mirror the server's own markdown->plan bridge convention.
    return [{"key": f"col{i + 1}", "label": str(label)} for i, label in enumerate(labels)]


def _rows(labels: list[str], rows: list[list[Any]]) -> list[dict[str, str]]:
    keys = [f"col{i + 1}" for i in range(len(labels))]
    out: list[dict[str, str]] = []
    for row in rows:
        values = [("" if v is None else str(v)) for v in row[: len(keys)]]
        if values and all(not value.strip() for value in values):
            values = [BLANK_CELL for _ in values]
        out.append({keys[i]: value for i, value in enumerate(values)})
    return out


def _table_block(labels: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {"type": "table", "columns": _columns(labels), "rows": _rows(labels, rows)}


def _string_metadata(metadata: Any) -> dict[str, str]:
    if not isinstance(metadata, dict):
        return {}
    return {
        str(k): str(v)
        for k, v in metadata.items()
        if v is not None and str(v).strip()
    }


def canonical_to_document_plan(canonical: dict) -> DocumentPlan:
    """Project the canonical content model into a ``hwpx.document_plan.v1`` mapping."""
    # The MCP authoring pipeline renders plan.title itself.  Repeating it as a
    # level-1 heading creates a visible duplicate in the delivered HWPX.
    blocks: list[dict[str, Any]] = []

    for op in _flow(canonical):
        kind = op[0]
        if kind in ("title", "meta"):
            continue
        if kind == "heading":
            blocks.append({"type": "heading", "level": 2, "text": str(op[1])})
        elif kind == "para":
            blocks.append({"type": "paragraph", "text": str(op[1])})
        elif kind == "evidence":
            rows = [[label, text] for label, text in op[1]]
            blocks.append(_table_block(["구분", "근거"], rows))
        elif kind == "task":
            demand = f"[{op[1]}] " if op[1] else ""
            blocks.append({"type": "paragraph", "text": f"과제 {demand}{op[2]}"})
        elif kind == "answer":
            for _ in range(int(op[1])):
                blocks.append({"type": "paragraph", "text": ANSWER_LINE})
        elif kind == "card":
            title, body, source, citation = op[1], op[2], op[3], op[4]
            src = f"출처: {source}" + (f" ({citation})" if citation else "")
            blocks.append(_table_block([str(title)], [[str(body)], [src]]))
        elif kind == "stems":
            blocks.append({"type": "paragraph", "text": "문장 도우미: " + " / ".join(op[1])})
        elif kind == "note":
            blocks.append({"type": "paragraph", "text": str(op[1])})
        elif kind == "callout":
            blocks.append({"type": "heading", "level": 2, "text": str(op[1])})
            blocks.append({"type": "paragraph", "text": str(op[2])})
        elif kind == "table":
            caption, headers, rows, _rh = op[1], op[2], op[3], op[4]
            if caption:
                blocks.append({"type": "heading", "level": 2, "text": str(caption)})
            blocks.append(_table_block([str(h) for h in headers], rows))
        elif kind == "pagebreak":
            blocks.append({"type": "page_break"})

    return {
        "schemaVersion": DOCUMENT_PLAN_SCHEMA_VERSION,
        "title": str(canonical["title"]),
        "metadata": _string_metadata(canonical.get("metadata")),
        "blocks": blocks,
    }


__all__ = [
    "canonical_to_document_plan",
    "ANSWER_LINE",
    "BLANK_CELL",
    "DocumentPlan",
    "DOCUMENT_PLAN_SCHEMA_VERSION",
]
