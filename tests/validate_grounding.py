#!/usr/bin/env python3
"""Cross-domain grounding gate (RED-first).

The individualized package is a science lesson on `[9과17-01]` (대기권/온실효과).
A release-blocking bug crossed subject boundaries: the reused base fixture injected
2022 개정 *사회과* provenance and regional (지역 사례) textbook examples into a science
package. This gate proves, deterministically:

  1. no rendered teacher/student file may carry another subject's provenance
     (사회과 / 지역 사례 / social provider ids) — RED against acfc166;
  2. the shared standard code, the lesson subject, and every provenance marker /
     provider must all agree on one subject;
  3. `check_cross_domain_grounding` flags a science package that carries social
     provenance and passes the clean, fixed package.

Independent implementation (no vendored third-party code).
"""
from __future__ import annotations

import sys
import zipfile
import copy
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from renderers import render_package  # noqa: E402
from validate_individualized_materials import build_sample_ir, TEACHER_DOC, GROUP_DOCS  # noqa: E402

# Tokens that belong to a *different* subject than science `[9과17-01]`.
# None of them may appear in a rendered science package.
FOREIGN_SUBJECT_TOKENS = [
    "사회과",
    "사회 교과",
    "지역 사례",
    "지역 문제 해결 토론",
    "2022 개정 사회",
    "curriculum-2022-social",
    "textbook-social",
]


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _all_text(paths: dict) -> str:
    """Every human-visible + embedded string recoverable from a rendered doc."""
    chunks = [Path(paths["html"]).read_text(encoding="utf-8")]
    for fmt, members in (
        ("docx", ("word/document.xml", "customXml/kteacher-content.xml", "customXml/kteacher-backport-marker.json")),
        ("hwpx", ("Contents/section0.xml", "Contents/kteacher-content.xml", "META-INF/kteacher-backport-marker.json")),
    ):
        with zipfile.ZipFile(paths[fmt]) as z:
            names = set(z.namelist())
            for m in members:
                if m in names:
                    chunks.append(z.read(m).decode("utf-8", "replace"))
    return "\n".join(chunks)


def main() -> None:
    ir = build_sample_ir()

    # (1) rendered artifacts must be free of any foreign-subject provenance.
    with tempfile.TemporaryDirectory() as td:
        rendered = render_package(ir, td)
        for did in (TEACHER_DOC, *GROUP_DOCS.values()):
            text = _all_text(rendered[did])
            for token in FOREIGN_SUBJECT_TOKENS:
                assert_true(token not in text,
                            f"{did}: rendered science package leaks foreign-subject provenance {token!r}")

    # (2)+(3) the deterministic grounding gate itself.
    from providers.materials.individualized import check_cross_domain_grounding  # noqa: E402

    clean = check_cross_domain_grounding(ir)
    assert_true(clean == [], f"clean science package must pass the grounding gate: {clean}")

    # negative: inject a social provenance marker into the science package.
    social = copy.deepcopy(ir)
    tdoc = next(d for d in social["lesson_package"]["documents"] if d["document_id"] == TEACHER_DOC)
    tdoc["content"].setdefault("provenance_markers", []).append({
        "record_id": "prov-textbook-social-unit2-1",
        "label": "[from-textbook:provided]",
        "evidence_text": "2022 개정 사회과 교과서 42~43쪽 지역 사례 읽기",
    })
    assert_true(check_cross_domain_grounding(social) != [],
                "a science package carrying 사회과 provenance must be flagged by the grounding gate")

    # negative: subject declared on the lesson context disagreeing with the standard code.
    mismatch = copy.deepcopy(ir)
    for d in mismatch["lesson_package"]["documents"]:
        if "lesson_context" in d["content"]:
            d["content"]["lesson_context"]["subject"] = "사회"
    assert_true(check_cross_domain_grounding(mismatch) != [],
                "declared subject disagreeing with the standard code must be flagged")

    print("PASS validate_grounding")
    print("- rendered teacher + all student files carry no foreign-subject provenance")
    print("- clean [9과17-01] science package passes the cross-domain grounding gate")
    print("- planted 사회과 provenance and subject/standard disagreement are both flagged")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL validate_grounding: {error}")
        raise SystemExit(1) from error
