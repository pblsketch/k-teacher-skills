"""Mask-or-block PII pipeline for public school-disclosure evaluation plans.

Public disclosure documents may still embed personal data (teacher names/contact,
student identifiers). Policy is fail-closed:
- Confidently-maskable PII (contact info, student numbers, inline-labeled names) is masked.
- A person-name that survives in a person-role TABLE COLUMN cannot be safely auto-masked
  (no inline label to anchor on) -> BLOCK the render for teacher review. Never best-effort
  pass-through.
- Name detection is intentionally role-column/labeled-text scoped. Applying a generic
  2–5 Hangul-token rule to subject/domain cells would misclassify ordinary curriculum
  words (for example 물질/생명). Live documents therefore still require the workflow's
  final teacher PII review before downstream-ready approval.
Masks fields AND free-text table cells.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_PHONE = re.compile(r"\b(?:0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}|01\d[-\s]?\d{3,4}[-\s]?\d{4})\b")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_STUDENT_NO = re.compile(r"(?:학번|학생\s*번호)\s*[:：]?\s*\d{3,6}")
_GRADE_CLASS_NO = re.compile(r"\b\d\s*학년\s*\d{1,2}\s*반\s*\d{1,2}\s*번\b")
# Inline-labeled person name: '담임: 홍길동' -> mask only the name group.
_NAME_LABEL = re.compile(r"(담임|담당\s*교사|담당|지도\s*교사|지도|작성자|교사|선생님|성명|이름)(\s*[:：]\s*)([가-힣]{2,5})(?![가-힣])")
# Table header cells that designate a person column.
_PERSON_HEADER = re.compile(r"^(담당\s*교사|담임(?:\s*교사)?|지도\s*교사|작성자|교사명|담당자|성명|이름)$")
# Masked placeholder token (must NOT be treated as evidence the name itself was handled).
_MASK_TOKEN = re.compile(r"\[MASKED:[a-z_]+\]")
# Whitespace + punctuation stripped when checking a person-column cell for residual identity.
_PERSON_CELL_STRIP = re.compile(r"[\s,./()·ㆍ~\-–—:：;|_]+")


@dataclass
class MaskResult:
    masked_text: str
    blocked: bool = False
    findings: list = field(default_factory=list)
    block_reasons: list = field(default_factory=list)


def _mask_matches(text: str, pattern: re.Pattern, kind: str, findings: list, name_group: int | None = None) -> str:
    def repl(m: re.Match) -> str:
        # Audit the category, never the PII value that was removed. Raw contact/name/
        # student identifiers must not survive in findings or downstream logs.
        findings.append({"type": kind, "text": f"[REDACTED:{kind}]"})
        if name_group is not None:
            return m.group(1) + m.group(2) + f"[MASKED:{kind}]"
        return f"[MASKED:{kind}]"

    return pattern.sub(repl, text)


def mask_text(text: str) -> tuple[str, list]:
    """Inline masking of contact PII, student numbers, and labeled names."""
    findings: list = []
    out = text
    out = _mask_matches(out, _EMAIL, "email", findings)
    out = _mask_matches(out, _PHONE, "phone", findings)
    out = _mask_matches(out, _STUDENT_NO, "student_no", findings)
    out = _mask_matches(out, _GRADE_CLASS_NO, "student_grade_class_no", findings)
    out = _mask_matches(out, _NAME_LABEL, "person_name", findings, name_group=3)
    return out, findings


def _split_table_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and set("".join(cells)) <= set("-: ")


def _person_columns(header_cells: list[str]) -> list[int]:
    return [i for i, c in enumerate(header_cells) if _PERSON_HEADER.match(c)]


def _person_cell_residual(cell: str) -> str | None:
    """Residual identity text in a person-role column cell after masking, or None if clean.

    Fail-closed: a person cell is clean ONLY when nothing but masked placeholders,
    whitespace, or punctuation remains. ANY residual — a bare name, a name+honorific
    (홍길동 선생님), a 5+ char name (압둘라만호), a name beside a masked phone
    (김철수 [MASKED:phone]), or any unrecognized nonempty identity text — blocks. The
    presence of a [MASKED:*] marker is never treated as proof the name was handled.
    """
    without_masks = _MASK_TOKEN.sub(" ", cell)
    residue = _PERSON_CELL_STRIP.sub("", without_masks)
    return cell.strip() if residue else None

def _redact(text: str) -> str:
    """Return a non-reversible audit marker for any blocked person identity.

    Never preserve scripts, initials, length, honorifics, or contact fragments: blocked
    Hangul, Latin, mixed-script, and otherwise unrecognized identities receive the same
    marker so findings and warning text cannot become a secondary PII channel.
    """
    return "[REDACTED:person_identity]"



def mask_or_block_plan(markdown: str) -> MaskResult:
    """Mask inline PII across the whole document, then block if any person-role table
    column still holds a bare person-name (unmaskable without a label)."""
    masked, findings = mask_text(markdown)
    lines = masked.splitlines()
    blocked = False
    reasons: list = []

    # Walk markdown tables: a header line, an optional separator, then data rows.
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|"):
            header = _split_table_row(lines[i])
            person_cols = _person_columns(header)
            j = i + 1
            # skip a separator row
            if j < len(lines) and lines[j].strip().startswith("|") and _is_separator(_split_table_row(lines[j])):
                j += 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = _split_table_row(lines[j])
                for c in person_cols:
                    if c < len(cells):
                        residual = _person_cell_residual(cells[c])
                        if residual is not None:
                            blocked = True
                            reasons.append(f"unmaskable person-name/identity in '{header[c]}' column: {_redact(residual)}")
                            findings.append({"type": "person_name_blocked", "column": header[c], "text": _redact(residual)})
                j += 1
            i = j
        else:
            i += 1

    return MaskResult(masked_text=masked, blocked=blocked, findings=findings, block_reasons=reasons)


def mask_structured(plan: dict) -> tuple[dict, MaskResult]:
    """Mask each string field of an already-structured plan (contact/labeled PII)."""
    findings: list = []

    def walk(node):
        if isinstance(node, str):
            masked, f = mask_text(node)
            findings.extend(f)
            return masked
        if isinstance(node, list):
            return [walk(x) for x in node]
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        return node

    return walk(plan), MaskResult(masked_text="<structured>", blocked=False, findings=findings)
