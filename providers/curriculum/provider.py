"""Read-only national curriculum provider over a normalized (non-distributed) index.

Fail-closed contract:
- quarantined records are never returned as downstream-ready; they surface only as
  status='quarantined' with a warning so a teacher can confirm, never as authoritative text.
- verify_standard() requires per-record provenance + verified-compatible license before it
  reports downstream_ready=True. Absent that, it stays fail-closed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .importer import canonical_code, strip_brackets


@dataclass
class LookupResult:
    status: str                      # "ok" | "quarantined" | "not_found"
    record: Optional[dict] = None
    disambiguation: Optional[list] = None
    warning: Optional[str] = None

    @property
    def is_resolved(self) -> bool:
        """Whether the lookup resolved to a single structurally-ok record.

        This is a RESOLUTION signal only — it is NOT a downstream-readiness gate.
        The sole authority on downstream-readiness is verify_standard() (provenance +
        verified-compatible license). A resolved record can still be fail-closed.
        """
        return self.status == "ok" and bool(self.record) and self.record.get("status") == "ok"


class CurriculumProvider:
    """Load a normalized index and answer read-only lookups.

    access_mode is always read-only; provider never mutates the index.
    """

    access_mode = "read-only"

    def __init__(self, index_path: str | Path, manifest_path: str | Path | None = None):
        self.index_path = Path(index_path)
        self._records: list[dict] = []
        with self.index_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    self._records.append(json.loads(line))
        self.manifest = None
        mp = Path(manifest_path) if manifest_path else self.index_path.parent / "manifest.json"
        if mp.exists():
            self.manifest = json.loads(mp.read_text(encoding="utf-8"))

    # --- read-only tool surface -------------------------------------------------

    def lookup_standard_by_code(
        self,
        code: str,
        *,
        revision: str | None = None,
        school_level: str | None = None,
        subject: str | None = None,
        grade_band: str | None = None,
    ) -> LookupResult:
        canon = canonical_code(code)
        matches = [r for r in self._records if r["canonical_code"] == canon]
        # Natural-key narrowing.
        for field_name, val in (
            ("curriculum_revision", revision),
            ("school_level", school_level),
            ("subject", subject),
            ("grade_band", grade_band),
        ):
            if val is not None:
                matches = [r for r in matches if r.get(field_name) == val]
        if not matches:
            return LookupResult(status="not_found", warning=f"{canon}: no record for the given natural key")
        if len(matches) > 1:
            return LookupResult(
                status="ok" if any(m["status"] == "ok" for m in matches) else "quarantined",
                disambiguation=[self._summary(m) for m in matches],
                warning=f"{canon}: {len(matches)} candidates; teacher must disambiguate",
            )
        rec = matches[0]
        if rec["status"] != "ok":
            return LookupResult(
                status="quarantined",
                record=rec,
                warning=f"{canon}: quarantined ({rec.get('quarantine_reason')}); not downstream-ready",
            )
        return LookupResult(status="ok", record=rec)

    def search_standards(
        self,
        *,
        school_level: str | None = None,
        subject: str | None = None,
        grade_band: str | None = None,
        keyword: str | None = None,
        limit: int = 5,
    ) -> dict:
        pool = self._filter(school_level, subject, grade_band)
        if keyword:
            k = keyword.strip()
            # keywords[] is empty in source (audit 5.5); search code+content substrings.
            pool = [r for r in pool if k in r.get("content", "") or k in r.get("canonical_code", "")]
        ok = [r for r in pool if r["status"] == "ok"]
        candidates = [self._summary(r) for r in ok[:limit]]
        return {"candidates": candidates, "truncated": len(ok) > limit, "total_ok": len(ok)}

    def list_standards(
        self,
        *,
        school_level: str | None = None,
        subject: str | None = None,
        grade_band: str | None = None,
        page: int = 0,
        page_size: int = 50,
    ) -> dict:
        pool = [r for r in self._filter(school_level, subject, grade_band) if r["status"] == "ok"]
        start = page * page_size
        return {
            "records": [self._summary(r) for r in pool[start : start + page_size]],
            "page": page,
            "total_ok": len(pool),
        }

    def verify_standard(self, code: str, **narrow) -> dict:
        """Fail-closed verification report for a single record."""
        res = self.lookup_standard_by_code(code, **narrow)
        if res.status != "ok" or not res.record:
            return {
                "downstream_ready": False,
                "status": res.status,
                "reason": res.warning or "no verified record",
            }
        rec = res.record
        src = rec.get("source", {})
        license_ok = src.get("license_status") == "verified-compatible" and bool(src.get("license_id"))
        provenance_ok = bool(src.get("verified")) and src.get("url")
        recorded_grade = src.get("provenance_grade")
        grade = recorded_grade if recorded_grade in (":provided", ":web") else (":provided" if provenance_ok else ":inferred")
        downstream_ready = bool(license_ok and provenance_ok and rec["status"] == "ok")
        return {
            "downstream_ready": downstream_ready,
            "status": rec["status"],
            "provenance_grade": grade if downstream_ready else ":inferred",
            "curriculum_revision": rec["curriculum_revision"],
            "source": src,
            "quality_flags": rec.get("quality_flags", []),
            "reason": None if downstream_ready else "provenance/license unverified -> fail-closed",
        }

    # --- helpers ---------------------------------------------------------------

    def _filter(self, school_level, subject, grade_band) -> list[dict]:
        pool = self._records
        if school_level is not None:
            pool = [r for r in pool if r.get("school_level") == school_level]
        if subject is not None:
            pool = [r for r in pool if r.get("subject") == subject]
        if grade_band is not None:
            pool = [r for r in pool if r.get("grade_band") == grade_band]
        return pool

    @staticmethod
    def _summary(rec: dict) -> dict:
        return {
            "canonical_code": rec["canonical_code"],
            "curriculum_revision": rec["curriculum_revision"],
            "school_level": rec["school_level"],
            "grade_band": rec["grade_band"],
            "subject": rec["subject"],
            "content": rec["content"],
            "source_status": rec.get("source", {}).get("license_status", "unverified"),
            "status": rec["status"],
            "quality_flags": rec.get("quality_flags", []),
        }
