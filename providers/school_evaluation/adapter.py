"""School evaluation-plan adapter (Tier 1 — school operational disclosure).

Mirrors the /tmp/schoolinfo-mcp@d7c78a3 (MIT) contract without vendoring its code:
find_school / get_evaluation_plan / local parse_evaluation_file. Every returned
plan is PII masked-or-blocked, pinned by school·year·grade·subject, and carries a
source anchor (URL·filename·hash·retrieved_at·section/page/table). This provider
NEVER emits national achievement standards as authoritative text — those come from
the curriculum provider (Tier 0) and are aligned separately (VS3).
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from typing import Callable, Optional

from . import pii
from .mcp_client import SchoolMcpClient

# Limits ported from schoolinfo evaluation.ts (values, not code).
MAX_ALL_DOCS = 20
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
MIN_USEFUL_MD = 200          # below this -> image PDF etc.; needs OCR/manual fallback
FETCH_TIMEOUT = 20


@dataclass
class SchoolPlanResult:
    status: str                     # "ok" | "needs_ocr_or_manual" | "blocked_pii" | "not_found" | "error"
    school_pin: dict | None = None
    year: int | None = None
    structured: list | None = None  # rows pinned to the requested subject/grade
    anchor: dict | None = None
    pii_findings: list | None = None
    fallback_used: bool = False
    warning: str | None = None
    provider_kind: str = "school-evaluation-plan-provider"


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def build_anchor(*, url: str | None, filename: str | None, content: str, section: str | None = None, page: str | None = None, table: str | None = None) -> dict:
    return {
        "carrier": "provider-record",
        "locator_type": "provider-record-id",
        "url": url,
        "filename": filename,
        "content_sha256": _content_hash(content),
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "section": section,
        "page": page,
        "table": table,
    }


_SUBJECTS = sorted(
    ["국어", "수학", "영어", "과학", "사회", "역사", "도덕", "기술ㆍ가정", "기술", "가정", "음악", "미술", "체육", "정보", "한문", "제2외국어"],
    key=len, reverse=True,
)


def structure_plan(markdown: str, *, subject: str | None = None) -> list:
    """Extract evaluation rows from a GFM/markdown table plan, pinned to subject when given.

    Deliberately simple + deterministic: each table row with a subject cell becomes a
    structured record. Real schoolinfo hwpx nuances (rowspan/EUC-KR/GFM) are handled by
    the upstream MCP parse; here we structure the already-markdown output.
    """
    rows: list = []
    for line in markdown.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or set("".join(cells)) <= set("-: "):
            continue  # header separator
        subj_cell = next((c for c in cells for s in _SUBJECTS if c == s or c.startswith(s)), None)
        if subj_cell is None:
            continue
        matched = next((s for s in _SUBJECTS if subj_cell == s or subj_cell.startswith(s)), subj_cell)
        if subject and matched != subject:
            continue
        rows.append({"subject": matched, "cells": cells})
    return rows


class SchoolEvaluationAdapter:
    def __init__(self, *, remote: bool = True, client: SchoolMcpClient | None = None):
        # remote=True (hosted MCP): local file tool is NOT exposed (security parity with
        # schoolinfo localFiles=false). remote=False: local parse enabled.
        self.remote = remote
        self.client = client or SchoolMcpClient(timeout=90)

    # --- schoolinfo contract mirror -------------------------------------------

    def find_school(self, name: str) -> dict:
        res = self.client.call_tool("find_school", {"name": name})
        return {"ok": res["ok"], "text": res.get("text", ""), "error": res.get("error")}

    def get_evaluation_plan(
        self,
        *,
        sido: str,
        sgg: str,
        kind: str,
        name: str,
        year: int,
        subject: str,
        approve_previous: Optional[Callable[[int, int], bool]] = None,
    ) -> SchoolPlanResult:
        """Pinned by school (sido/sgg/kind/name) + year + subject.

        current->previous fallback requires explicit approval: approve_previous(current, prev)
        must return True. Never auto-falls-back.
        """
        pin = {"sido": sido, "sgg": sgg, "kind": kind, "name": name, "subject": subject, "grade_pin": subject}
        res = self.client.call_tool(
            "get_evaluation_plan",
            {"sido": sido, "sgg": sgg, "kind": kind, "name": name, "year": year, "subject": subject},
        )
        if not res["ok"] or not res.get("text") or len(res["text"]) < 3:
            # try approved previous year only
            if approve_previous and approve_previous(year, year - 1):
                prev = self.get_evaluation_plan(
                    sido=sido, sgg=sgg, kind=kind, name=name, year=year - 1, subject=subject, approve_previous=None
                )
                if prev.status == "ok":
                    prev.fallback_used = True
                    prev.warning = f"current({year}) unavailable; using approved previous year {year-1}"
                    return prev
            return SchoolPlanResult(status="error", school_pin=pin, year=year, warning=res.get("error") or "no plan text")
        return self._finish(res["text"], pin, year, subject, url=None, filename=None)

    def parse_evaluation_file(self, local_path: str, *, subject: str | None = None) -> SchoolPlanResult:
        """LOCAL-ONLY: parse a teacher-downloaded plan file. Disabled in remote mode."""
        if self.remote:
            return SchoolPlanResult(status="error", warning="parse_evaluation_file is disabled in remote mode (security parity)")
        from pathlib import Path

        data = Path(local_path).read_bytes()
        if len(data) > MAX_DOWNLOAD_BYTES:
            return SchoolPlanResult(status="error", warning=f"file exceeds {MAX_DOWNLOAD_BYTES} bytes")
        text = data.decode("utf-8", "replace")
        return self._finish(text, {"file": Path(local_path).name}, None, subject, url=None, filename=Path(local_path).name)

    # --- internal --------------------------------------------------------------

    def _finish(self, text: str, pin: dict, year: int | None, subject: str | None, *, url, filename) -> SchoolPlanResult:
        if len(text) < MIN_USEFUL_MD:
            return SchoolPlanResult(
                status="needs_ocr_or_manual",
                school_pin=pin,
                year=year,
                warning=f"extracted text < {MIN_USEFUL_MD} chars (likely image PDF); OCR/manual fallback required",
                anchor=build_anchor(url=url, filename=filename, content=text),
            )
        # Mask-or-block on the raw plan text first (table-aware), then structure the
        # masked text so no PII reaches the structured/rendered output.
        mres = pii.mask_or_block_plan(text)
        anchor = build_anchor(url=url, filename=filename, content=text, table=subject)
        if mres.blocked:
            return SchoolPlanResult(
                status="blocked_pii",
                school_pin=pin,
                year=year,
                anchor=anchor,
                pii_findings=mres.findings,
                warning="unmaskable PII residual -> render blocked; teacher review required: " + "; ".join(mres.block_reasons),
            )
        structured = structure_plan(mres.masked_text, subject=subject)
        return SchoolPlanResult(
            status="ok",
            school_pin=pin,
            year=year,
            structured=structured,
            anchor=anchor,
            pii_findings=mres.findings,
        )
