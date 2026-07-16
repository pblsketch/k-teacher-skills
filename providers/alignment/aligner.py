"""Alignment / promotion / quarantine between school plans (Tier 1) and the
national curriculum provider (Tier 0).

Invariants enforced here (data-model level):
- INV-1: a school record is NEVER promoted to curriculum-record. Alignment emits a
  SEPARATE national curriculum-record; the school record stays curriculum-context.
- INV-2: fail-closed — a matched code is not downstream-ready unless the national
  record itself verifies AND the teacher has approved.
- INV-3: mismatch / not_found / ambiguity / missing revision -> quarantined + teacher-confirm.
- INV-4: teacher approval is required before any aligned record is downstream-ready.
- INV-5: these are envelope-stage provenance records (they appear in the workflow
  envelope before any lesson-package IR).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# National achievement-standard code shape (parenthetical/Roman variants included).
_CODE_IN_TEXT = re.compile(r"\[?\d{1,2}[가-힣][가-힣A-Za-zⅠⅡⅢ()]*-?[0-9A-Za-z\-]*\d\]?")
_CODE_STRICT = re.compile(r"^\[\d{1,2}[가-힣][^\]]*-[^\]]*\]$")


@dataclass
class AlignedPair:
    code: str
    school_context: dict          # curriculum-context (Tier 1)
    national_record: dict         # curriculum-record (Tier 0), additive
    downstream_ready: bool
    note: str = ""


@dataclass
class QuarantineEntry:
    code: str
    reason: str
    teacher_confirm: bool = True


@dataclass
class AlignmentResult:
    aligned: list = field(default_factory=list)
    quarantined: list = field(default_factory=list)

    def coexisting_records(self) -> list:
        """Envelope-stage provenance records: both tiers coexist per aligned pair."""
        out = []
        for pair in self.aligned:
            out.append(pair.school_context)
            out.append(pair.national_record)
        return out


def extract_codes(source) -> list[str]:
    """Pull candidate achievement-standard codes from structured rows or raw text."""
    if isinstance(source, list):
        text = " ".join(
            " ".join(str(c) for c in (row.get("cells") or []) if c) if isinstance(row, dict) else str(row)
            for row in source
        )
    else:
        text = str(source)
    seen: list[str] = []
    for m in _CODE_IN_TEXT.finditer(text):
        code = m.group(0)
        if not code.startswith("["):
            code = "[" + code.strip("[]") + "]"
        if _CODE_STRICT.match(code) and code not in seen:
            seen.append(code)
    return seen


def _school_context_record(code: str, school_provider_id: str, subject: str) -> dict:
    return {
        "record_scope": "curriculum-context",
        "provider": {"provider_id": school_provider_id, "provider_kind": "school-evaluation-plan-provider"},
        "referenced_code": code,
        "subject": subject,
        "authority": "school-operational-fact",
    }


def _national_curriculum_record(record: dict, verify: dict) -> dict:
    rec = {
        "record_scope": "curriculum-record",
        "provider": {"provider_id": "gepai-curriculum-2022-local", "provider_kind": "curriculum-provider"},
        "canonical_code": record["canonical_code"],
        "curriculum_revision": record["curriculum_revision"],
        "school_level": record["school_level"],
        "subject": record["subject"],
        "content": record["content"],
        "provenance_grade": verify.get("provenance_grade", ":inferred"),
        "source_license_status": record.get("source", {}).get("license_status", "unverified"),
        "authority": "national-achievement-standard",
    }
    # INV-1 guard: a curriculum-record MUST come from a curriculum-provider.
    assert rec["provider"]["provider_kind"] == "curriculum-provider", "INV-1: curriculum-record must be national"
    return rec


def align_plan_codes_to_national(
    codes: list[str],
    national,
    *,
    school_level: str,
    subject: str,
    revision: str = "2022",
    teacher_approved: bool = False,
    school_provider_id: str = "schoolinfo-plan",
) -> AlignmentResult:
    result = AlignmentResult()
    for code in codes:
        res = national.lookup_standard_by_code(code, revision=revision, school_level=school_level, subject=subject)
        if res.status == "ok" and res.record is not None:
            verify = national.verify_standard(code, revision=revision, school_level=school_level, subject=subject)
            downstream = bool(verify.get("downstream_ready") and teacher_approved)  # INV-2, INV-4
            result.aligned.append(
                AlignedPair(
                    code=code,
                    school_context=_school_context_record(code, school_provider_id, subject),  # INV-1: stays context
                    national_record=_national_curriculum_record(res.record, verify),
                    downstream_ready=downstream,
                    note="matched; " + ("downstream-ready" if downstream else "fail-closed until national verified + teacher-approved"),
                )
            )
        else:
            reason = {
                "not_found": "no national match for natural key",
                "quarantined": "national record quarantined (e.g. mixed-revision)",
            }.get(res.status, "ambiguous or unresolved")
            if res.disambiguation:
                reason = "ambiguous: multiple national candidates"
            result.quarantined.append(QuarantineEntry(code=code, reason=reason, teacher_confirm=True))  # INV-3
    return result
