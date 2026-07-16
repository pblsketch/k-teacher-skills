"""Non-distributed normalization/import pipeline for the GEPAI achievement-standard
backup into a local, license-unverified curriculum search index.

The raw GEPAI dataset is NEVER redistributed: this reads an external source path
(default points outside the repo) and writes a normalized index + release manifest
under providers/_local/ (gitignored). It deterministically repairs the six audited
defects and quarantines anything it cannot verify, so downstream lookups fail closed.

Audit reference: 04-gepai-curriculum-data-audit.md sections 5.1-5.7.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

DEFAULT_GEPAI_SOURCE = "/mnt/e/github/gepai2026/supabase-backup-20260706/achievement_standards.jsonl"
# Original integrated CSV needed to restore the 11 upstream-dropped collision codes
# (audit 5.2). Optional: absent -> collisions recorded as dropped, never fabricated.
DEFAULT_COLLISION_CSV = "/mnt/e/github/gepai2026/gepai2026/data/초중고 성취기준 데이터베이스 - 데이터베이스.csv"

# Elementary grade-typo corrections (audit 5.4): only these three 3~4 science codes.
GRADE_TYPO_FIX = {"3~5": "3~4", "3~6": "3~4", "3~7": "3~4"}

# Middle-school grade band label.
_MIDDLE_BAND = "1~3학년"

# 2022 code shapes include parentheticals ([9사(일사)01-02]) and Roman numerals
# ([12영Ⅰ-01-01], [12미적Ⅱ-02-03]). Validity: '[' + 1-2 grade digits + a Korean
# subject char + a hyphenated domain-sequence tail. subject_code is the leading
# Korean run only. Genuinely malformed codes (no grade digit / no hyphen) quarantine.
_VALID_CODE_RE = re.compile(r"^\[\d{1,2}[가-힣][^\]]*-[^\]]*\]$")
_SUBJ_RE = re.compile(r"^\[\d{1,2}([가-힣]+)")


def strip_brackets(code: str) -> str:
    return code.strip().lstrip("[").rstrip("]").strip()


def canonical_code(code: str) -> str:
    """'[' + normalized inner + ']' (audit 5.3)."""
    return "[" + strip_brackets(code) + "]"


def subject_code_from(code: str) -> str | None:
    m = _SUBJ_RE.match(canonical_code(code))
    return m.group(1) if m else None


def normalize_record(raw: dict, *, mixed_revision_codes: set[str] | None = None) -> dict:
    """Pure normalization of one raw GEPAI row into the internal provider record.

    Fail-closed: provenance/license default to unverified; mixed-revision and
    unparseable rows are quarantined.
    """
    mixed_revision_codes = mixed_revision_codes or set()
    raw_code = str(raw.get("code", "")).strip()
    canon = canonical_code(raw_code)
    school_level = raw.get("school_level")
    subject = raw.get("subject")
    grade_level = str(raw.get("grade_level", "")).strip()
    flags: list[str] = []
    quarantine_reason: str | None = None

    # Defect 5.3: bracket normalization.
    had_brackets = raw_code.startswith("[") and raw_code.endswith("]")
    if not had_brackets:
        flags.append("bracket_normalized")

    # Defect 5.4: elementary grade typo -> 3~4.
    grade_band = grade_level
    if school_level == "초등학교" and grade_level in GRADE_TYPO_FIX:
        grade_band = GRADE_TYPO_FIX[grade_level]
        flags.append("grade_corrected")

    if school_level == "중학교":
        grade_band = grade_band or _MIDDLE_BAND

    # Defect 5.5: keyword/env_topics search-augmentation absent.
    if not raw.get("keywords"):
        flags.append("keywords_absent")

    # Defect 5.1: mixed revision. The elementary 5~6 no-bracket set is a 2015 mapping
    # mislabelled as 2022. Anything in that set (or otherwise unverifiable) is quarantined
    # with revision downgraded to 'unverified' so it never ships as authoritative 2022.
    curriculum_revision = str(raw.get("curriculum", "")).strip() or "unverified"
    stripped = strip_brackets(raw_code)
    is_mixed = stripped in mixed_revision_codes or (
        school_level == "초등학교" and grade_band in ("5~6",) and not had_brackets
    )
    status = "ok"
    if is_mixed:
        status = "quarantined"
        quarantine_reason = "mixed_revision_suspected"
        curriculum_revision = "unverified"
        flags.append("mixed_revision")

    # Defect 5.6/5.7: lost curriculum context + no provenance/license.
    parsed_ok = _VALID_CODE_RE.match(canon) is not None
    if not parsed_ok:
        status = "quarantined"
        quarantine_reason = quarantine_reason or "unparseable_code"
        flags.append("unparseable_code")

    record = {
        "standard_id": f"curriculum:{curriculum_revision}:{school_level}:{subject}:{canon}",
        "curriculum_revision": curriculum_revision,
        "school_level": school_level,
        "grade_band": grade_band,
        "subject": subject,
        "subject_code": subject_code_from(canon),
        "canonical_code": canon,
        "raw_code": raw_code,
        "content": raw.get("content", ""),
        "domain": None,          # reserved for P2 enrichment (audit 5.6)
        "core_ideas": [],        # reserved for P2 enrichment
        "action_verbs": [],      # reserved for P2 enrichment
        "content_elements": [],
        "commentary": None,
        "keywords": list(raw.get("keywords") or []),
        "quality_flags": flags,
        "source": {
            "issuer": "교육부",
            "notice_number": None,
            "document_title": None,
            "page": None,
            "url": None,
            "license_id": None,
            "license_status": "unverified",
            "verified": False,
        },
        "revision_evidence": (
            "curriculum field=2022 and bracketed code retained"
            if status == "ok"
            else f"downgraded: {quarantine_reason}"
        ),
        "status": status,
        "quarantine_reason": quarantine_reason,
    }
    return record


@dataclass
class ImportStats:
    total: int = 0
    ok: int = 0
    quarantined: int = 0
    flags: dict = field(default_factory=dict)
    collision_restored: int = 0
    collision_dropped_upstream: int = 0


def _detect_mixed_revision_set(rows: list[dict]) -> set[str]:
    """The 322 elementary 5~6 no-bracket codes are the 2015 mapping (audit 5.1)."""
    return {
        strip_brackets(str(r.get("code", "")))
        for r in rows
        if r.get("school_level") == "초등학교"
        and str(r.get("grade_level", "")).strip() == "5~6"
        and not str(r.get("code", "")).strip().startswith("[")
    }


def import_dataset(
    source_path: str | Path = DEFAULT_GEPAI_SOURCE,
    out_dir: str | Path | None = None,
    *,
    collision_csv: str | Path | None = DEFAULT_COLLISION_CSV,
) -> dict:
    """Read the external GEPAI JSONL, normalize, and write a local (gitignored)
    normalized index + release manifest. Returns the manifest dict."""
    source_path = Path(source_path)
    out_dir = Path(out_dir) if out_dir else Path(__file__).resolve().parents[1] / "_local" / "curriculum-2022"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    with source_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    mixed = _detect_mixed_revision_set(rows)
    stats = ImportStats(total=len(rows))
    normalized: list[dict] = []
    seen_keys: set[tuple] = set()
    for raw in rows:
        rec = normalize_record(raw, mixed_revision_codes=mixed)
        key = (rec["curriculum_revision"], rec["school_level"], rec["grade_band"], rec["subject"], rec["canonical_code"])
        # Natural key uniqueness (audit 5.2): duplicates would be collisions.
        if key in seen_keys:
            rec["status"] = "quarantined"
            rec["quarantine_reason"] = "natural_key_collision"
            rec["quality_flags"].append("natural_key_collision")
        seen_keys.add(key)
        if rec["status"] == "ok":
            stats.ok += 1
        else:
            stats.quarantined += 1
        for f in rec["quality_flags"]:
            stats.flags[f] = stats.flags.get(f, 0) + 1
        normalized.append(rec)

    # Collision restore (audit 5.2): only possible from the original CSV (3,285 rows).
    collision_note = "not_attempted"
    if collision_csv and Path(collision_csv).exists():
        collision_note = "csv_present_restore_todo"  # restore hook; not fabricated when absent
    else:
        collision_note = "csv_absent_collisions_dropped_upstream_recorded"

    # Write normalized index (non-distributed).
    index_path = out_dir / "normalized.jsonl"
    with index_path.open("w", encoding="utf-8") as fh:
        for rec in normalized:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    content_sha = hashlib.sha256(index_path.read_bytes()).hexdigest()

    manifest = {
        "release_id": f"gepai-curriculum-2022-local@{time.strftime('%Y-%m-%d')}",
        "release_version": time.strftime("%Y.%m.%d"),
        "record_count": stats.total,
        "ok_count": stats.ok,
        "quarantined_count": stats.quarantined,
        "content_sha256": content_sha,
        "natural_key": ["curriculum_revision", "school_level", "grade_band", "subject", "canonical_code"],
        "defects_handled": stats.flags,
        "collision_handling": collision_note,
        "distribution": "non-distributed-local-only",
        "license_status": "unverified",
        "source_note": (
            "Local normalization of the GEPAI supabase backup. NOT redistributed. "
            "License unverified; records ship fail-closed until per-record provenance/"
            "license is verified. Elementary 5~6 no-bracket set quarantined as 2015 mixed."
        ),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
