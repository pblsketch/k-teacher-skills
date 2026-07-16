#!/usr/bin/env python3
"""VS4a renderer spike (hard gate): single canonical IR -> real HWPX/DOCX/HTML files,
re-extracted, 3-way parity verified for real. No anthropics renderer code.
"""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from renderers import render_all, extract_all, verify_parity  # noqa: E402

IR_PATH = ROOT / "tests" / "golden" / "lesson-package-ir" / "downstream-ready.json"


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> None:
    ir = json.loads(IR_PATH.read_text(encoding="utf-8"))
    document = ir["lesson_package"]["documents"][0]
    expected_content = [{"content_id": s["content_id"], "text": s["text"]} for s in document["content"]["sections"]]

    with tempfile.TemporaryDirectory() as td:
        paths = render_all(ir, td)

        # 1. Real files exist; hwpx/docx are valid zips carrying the marker member.
        for fmt in ("hwpx", "docx", "html"):
            assert_true(Path(paths[fmt]).exists() and Path(paths[fmt]).stat().st_size > 0, f"{fmt} file generated")
        with zipfile.ZipFile(paths["hwpx"]) as z:
            names = z.namelist()
            assert_true(names[0] == "mimetype" and z.read("mimetype") == b"application/hwp+zip", "hwpx OCF mimetype first/stored")
            assert_true("META-INF/kteacher-backport-marker.json" in names, "hwpx marker at canonical member")
            assert_true("Contents/section0.xml" in names, "hwpx has content section")
        with zipfile.ZipFile(paths["docx"]) as z:
            names = z.namelist()
            assert_true("customXml/kteacher-backport-marker.json" in names, "docx marker at canonical OPC part")
            assert_true("word/document.xml" in names and "[Content_Types].xml" in names, "docx OOXML skeleton")
        html_text = Path(paths["html"]).read_text(encoding="utf-8")
        assert_true('<script id="kteacher-backport-marker" type="application/json">' in html_text, "html marker script node")

        # 2. Re-extract each real file.
        extracted = extract_all(paths)

        # 3. Content round-trips from every format and matches the source IR.
        for fmt in ("hwpx", "docx", "html"):
            assert_true(extracted[fmt]["required_content"] == expected_content, f"{fmt} content round-trips from real file")
            assert_true(extracted[fmt]["title"] == document["title"], f"{fmt} title round-trips")
            assert_true(len(extracted[fmt]["provenance_markers"]) == len(document["content"]["provenance_markers"]), f"{fmt} provenance round-trips")

        # 4. 3-way parity: identical content + fingerprint; markers at canonical locations.
        ok, reasons = verify_parity(extracted)
        assert_true(ok, f"3-way parity failed: {reasons}")
        fps = {extracted[f]["embedded_backport_marker"]["content_fingerprint"] for f in ("hwpx", "docx", "html")}
        assert_true(len(fps) == 1, "identical content_fingerprint across formats (same source IR)")

        # 5. Adversarial: tamper HTML content -> parity must fail.
        tampered = Path(paths["html"]).read_text(encoding="utf-8").replace(expected_content[0]["text"], "변조된 내용")
        Path(paths["html"]).write_text(tampered, encoding="utf-8")
        extracted2 = extract_all(paths)
        ok2, reasons2 = verify_parity(extracted2)
        assert_true(not ok2 and any("required_content" in r for r in reasons2), "tampered content breaks parity")

    print("PASS validate_renderer_spike")
    print("- real HWPX(OWPML zip)/DOCX(OOXML zip)/HTML generated from one canonical IR")
    print("- backport marker at each schema canonical location; extractable")
    print("- content round-trips from every real file; 3-way parity green; fingerprint identical")
    print("- adversarial content tamper breaks parity (fail-closed)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
