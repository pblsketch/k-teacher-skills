"""`:web` provenance overlay for national achievement standards.

M2 rigor:
- CONTENT verification requires a substantive normalized content-token match strictly
  above an explicit threshold AND official-source anchoring. A bare code-string hit
  only corroborates; it can NEVER substitute for a content match.
- LICENSE confirmation is SEPARATE from content verification. A successful fetch never
  infers a redistribution-compatible license. `apply_web_overlay` only sets a
  verified-compatible license when independently-supplied license evidence is provided;
  otherwise the record is content-verified but stays fail-closed on license.
- Never fabricates: unreachable / non-official / weak-match sources stay fail-closed.

The fetch function is injectable so tests run offline.
"""
from __future__ import annotations

import hashlib
import re
import time
import urllib.parse
import urllib.request
from typing import Callable

# Official public curriculum sources (2022 revision). NCIC is the national authority.
OFFICIAL_SOURCES = {
    "ncic": "https://ncic.re.kr",
    "moe": "https://www.moe.go.kr",
    "law": "https://www.law.go.kr",
}
# Host suffixes that count as official curriculum sources for :web anchoring.
OFFICIAL_HOST_SUFFIXES = ("ncic.re.kr", "moe.go.kr", "law.go.kr")
DEFAULT_MIN_TOKEN_RATIO = 0.6


def _default_fetch(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "kteacher-curriculum-verify/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https scheme)
        raw = resp.read()
    for enc in ("utf-8", "euc-kr", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _significant_tokens(content: str) -> list[str]:
    toks = re.split(r"[\s,.·、，。：;()（）\[\]]+", content)
    return [t for t in toks if len(t) >= 3][:12]


def is_official_source(url: str) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return any(host == suf or host.endswith("." + suf) for suf in OFFICIAL_HOST_SUFFIXES)


def verify_via_web(
    code: str,
    content: str,
    source_url: str,
    *,
    fetch: Callable[[str], str] = _default_fetch,
    min_token_ratio: float = DEFAULT_MIN_TOKEN_RATIO,
) -> dict:
    """Attempt CONTENT verification only. Returns an overlay dict; content_verified may be False.

    content_verified requires: official source AND content-token ratio strictly above
    min_token_ratio. code_hit is recorded for audit but never promotes on its own.
    License is NOT decided here.
    """
    retrieved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    official = is_official_source(source_url)
    try:
        body = fetch(source_url)
    except Exception as exc:  # noqa: BLE001 - honest failure, never fabricate
        return {
            "content_verified": False,
            "provenance_grade": ":inferred",
            "verification_evidence_type": None,
            "code_hit": False,
            "is_official_source": official,
            "match_ratio": 0.0,
            "threshold": min_token_ratio,
            "reason": f"source unreachable: {type(exc).__name__}",
            "source_url": source_url,
            "retrieved_at": retrieved_at,
        }
    tokens = _significant_tokens(content)
    hit = sum(1 for t in tokens if t in body)
    ratio = (hit / len(tokens)) if tokens else 0.0
    code_hit = code.strip("[]") in body
    body_hash = hashlib.sha256(body.encode("utf-8", "replace")).hexdigest()

    # code_hit only corroborates; strict threshold; official anchoring required.
    content_match = ratio > min_token_ratio
    content_verified = bool(content_match and official)

    if not official:
        reason = "source is not an official curriculum source; :web requires official anchoring"
    elif not content_match:
        reason = (
            f"content-token match {round(ratio, 3)} not strictly above threshold {min_token_ratio}"
            + (" (code-string hit alone cannot promote)" if code_hit else "")
        )
    else:
        reason = None

    return {
        "content_verified": content_verified,
        "provenance_grade": ":web" if content_verified else ":inferred",
        "verification_evidence_type": "web-verification" if content_verified else None,
        "match_ratio": round(ratio, 3),
        "threshold": min_token_ratio,
        "code_hit": code_hit,
        "is_official_source": official,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "content_sha256_of_source": body_hash,
        "source_anchor": {
            "carrier": "url",
            "locator_type": "official-source-url",
            "locator_value": f"{source_url}#retrieved={retrieved_at}#src_sha256={body_hash[:16]}",
        },
        "reason": reason,
    }


def _valid_license_evidence(evidence: dict | None) -> bool:
    """License evidence must be independently supplied and verified-compatible."""
    return bool(
        evidence
        and evidence.get("status") == "verified-compatible"
        and evidence.get("license_id")
        and evidence.get("license_authority")
    )


def apply_web_overlay(record: dict, overlay: dict, license_evidence: dict | None = None) -> dict:
    """Apply a `:web` overlay. CONTENT verification and LICENSE confirmation are separate.

    - overlay.content_verified False -> no change (fail-closed).
    - content verified, no valid license evidence -> record content provenance
      (verified=True, url, web-verification, source anchor) but license_status stays
      unverified, so verify_standard remains fail-closed (not downstream-ready).
    - content verified AND independently-supplied verified-compatible license evidence
      -> also set license_status/license_id/license_authority (downstream-ready eligible).
    """
    rec = dict(record)
    src = dict(rec.get("source", {}))
    if not overlay.get("content_verified"):
        return rec  # fail-closed: a fetch that did not verify content changes nothing

    src.update(
        {
            "url": overlay["source_url"],
            "verified": True,
            "provenance_grade": ":web",
            "verification_evidence_type": "web-verification",
            "source_anchor": overlay["source_anchor"],
            "content_verified": True,
        }
    )
    flags = rec.setdefault("quality_flags", [])
    if "web_content_verified" not in flags:
        flags.append("web_content_verified")

    if _valid_license_evidence(license_evidence):
        src["license_status"] = "verified-compatible"
        src["license_id"] = license_evidence["license_id"]
        src["license_authority"] = license_evidence["license_authority"]
        if "web_license_confirmed" not in flags:
            flags.append("web_license_confirmed")
    else:
        # License NOT inferred from the fetch; stays fail-closed until independently confirmed.
        src["license_status"] = src.get("license_status", "unverified")
        src.setdefault("license_id", None)

    rec["source"] = src
    return rec
