#!/usr/bin/env python3
"""Teacher/student field-readiness gate (RED-first).

Proves the individualized package is a real, printable classroom operating plan and
student worksheet — not one A4 page of repeated heading+paragraph prose. Every check
is derived from the committed IR and the three rendered production files, and every
check is designed to FAIL against commit acfc166 (minimal renderer output).

Physical page contract:
  - teacher plan: HTML 3 `<section class="page">`, DOCX 2 page breaks, HWPX 2 page breaks;
  - each student worksheet: HTML 2 `<section class="page">`, DOCX 1 page break, HWPX 1.

Structural content contract: required table captions, flow minutes summing to 45,
Group A/B/C deployment matrix, regroup rules, blank observation grid, interpretation
table, real atmosphere-layer source data + greenhouse card, header field blanks,
success/self-check checklists, submission instruction — and NO generic placeholders.

Independent implementation (no vendored third-party code).
"""
from __future__ import annotations

import re
import html as html_lib
import sys
import zipfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from renderers import render_package  # noqa: E402
from validate_individualized_materials import build_sample_ir, TEACHER_DOC, GROUP_DOCS  # noqa: E402

# --- shared structural vocabulary (must match the provider composition) -------- #
CAP_OVERVIEW = "수업 개요"
CAP_FLOW = "45분 수업 흐름"
CAP_MATRIX = "모둠별 배치 비교"
CAP_REGROUP = "유연한 재편성 규칙"
CAP_OBSERVE = "관찰·피드백 기록표"
CAP_INTERPRET = "출구표 해석과 다음 단계"

CAP_HEADER = "학습자 정보"
CAP_SUCCESS = "성공 기준 자기 점검"
CAP_SOURCE = "대기권 층상 구조 자료"
CAP_SELFCHECK = "스스로 점검"

# Generic placeholders that a field-ready student worksheet must never render.
STUDENT_PLACEHOLDERS = [
    "학급 제공 자료",
    "그림과 표로 정보를 함께 제시한다",
    "제공된 자료를 사용합니다",
]


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _blocks(doc: dict) -> list:
    return doc["content"].get("blocks", [])


def _captions(blocks: list) -> set:
    return {b.get("caption") for b in blocks if b.get("caption")}


def _tables(blocks: list) -> list:
    return [b for b in blocks if b["block_type"] in ("data_table", "fill_table")]


def html_pages(path: str) -> int:
    return len(re.findall(r'<section class="page"', Path(path).read_text(encoding="utf-8")))


def visible_html_text(path: str) -> str:
    """Extract user-visible text only; marker/style/data attributes are not surface copy."""
    text = Path(path).read_text(encoding="utf-8")
    text = re.sub(r"<script\b[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<style\b[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


def docx_pagebreaks(path: str) -> int:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    return len(re.findall(r'<w:br\b[^>]*w:type="page"', xml))


def hwpx_pagebreaks(path: str) -> int:
    with zipfile.ZipFile(path) as z:
        xml = z.read("Contents/section0.xml").decode("utf-8")
    return xml.count('pageBreak="1"')


def _row_widths_ok(blocks: list) -> list:
    bad = []
    for b in blocks:
        if b["block_type"] == "data_table":
            w = len(b["headers"])
            for i, r in enumerate(b["cells"]):
                if len(r) != w:
                    bad.append(f"{b['block_id']} data_table row {i} width {len(r)} != {w}")
        elif b["block_type"] == "fill_table":
            w = len(b["headers"])
            for i, r in enumerate(b["rows"]):
                if len(r) != w:
                    bad.append(f"{b['block_id']} fill_table row {i} width {len(r)} != {w}")
    return bad


# --------------------------------------------------------------------------- #
# Teacher operating plan
# --------------------------------------------------------------------------- #

def check_teacher(doc: dict, paths: dict) -> None:
    blocks = _blocks(doc)
    caps = _captions(blocks)

    # lesson context grounded on science [9과17-01].
    ctx = doc["content"].get("lesson_context")
    assert_true(isinstance(ctx, dict), "teacher plan: missing structured lesson_context")
    assert_true(ctx.get("subject") == "과학", f"teacher lesson_context.subject must be 과학: {ctx.get('subject')}")
    assert_true(ctx.get("standard_code") == "[9과17-01]", "teacher lesson_context.standard_code must be [9과17-01]")
    assert_true(int(ctx.get("lesson_minutes", 0)) == 45, "teacher lesson_minutes must be 45")

    for cap in (CAP_OVERVIEW, CAP_FLOW, CAP_MATRIX, CAP_REGROUP, CAP_OBSERVE, CAP_INTERPRET):
        assert_true(any(cap in c for c in caps), f"teacher plan missing required table: {cap!r} (have {sorted(caps)})")

    # 45-minute flow table: phase/minutes/teacher move/student action/formative evidence; minutes sum to 45.
    flow = next(b for b in blocks if b["block_type"] == "data_table" and CAP_FLOW in b["caption"])
    assert_true(len(flow["headers"]) == 5, f"flow table must have 5 columns, got {flow['headers']}")
    minutes = []
    for r in flow["cells"]:
        m = re.search(r"\d+", r[1])
        assert_true(m is not None, f"flow row has no minutes: {r}")
        minutes.append(int(m.group()))
    assert_true(sum(minutes) == 45, f"lesson-flow minutes must sum to 45, got {minutes} = {sum(minutes)}")

    # Group A/B/C deployment matrix with access/representation/response/rigor rows.
    matrix = next(b for b in blocks if b["block_type"] == "data_table" and CAP_MATRIX in b["caption"])
    assert_true([h for h in matrix["headers"] if "Group A" in h] and
                any("Group B" in h for h in matrix["headers"]) and
                any("Group C" in h for h in matrix["headers"]),
                f"matrix must compare Group A/B/C in columns: {matrix['headers']}")
    row_labels = " ".join(r[0] for r in matrix["cells"])
    for need in ("접근", "표상", "반응", "엄격"):
        assert_true(need in row_labels, f"matrix must carry a {need} row: {row_labels}")

    # observation grid: blank student rows + observable criteria columns.
    obs = next(b for b in blocks if b["block_type"] == "fill_table" and CAP_OBSERVE in (b.get("caption") or ""))
    assert_true(len(obs["headers"]) >= 3, "observation grid needs student + >=2 observable-criteria columns")
    blank_rows = [r for r in obs["rows"] if all(not str(c).strip() for c in r)]
    assert_true(len(blank_rows) >= 5, f"observation grid needs >=5 blank student rows, got {len(blank_rows)}")

    # post-lesson notes area.
    assert_true(any(b["block_type"] == "answer_box" for b in blocks), "teacher plan missing post-lesson notes area")

    # no malformed row widths.
    bad = _row_widths_ok(blocks)
    assert_true(not bad, f"teacher plan has malformed table rows: {bad}")

    # no heading/text label duplication or internal implementation metadata on user surfaces.
    html = Path(paths["html"]).read_text(encoding="utf-8")
    visible = visible_html_text(paths["html"])
    assert_true("공통 목표:" not in html, "teacher HTML duplicates the '공통 목표' label in heading and text")
    assert_true(doc["document_id"] not in visible, "teacher HTML exposes an internal document id")
    assert_true("[from-" not in visible, "teacher HTML exposes a machine provenance token")
    assert_true('<div class="subtitle">개별화 수업 운영안</div>' not in html,
                "teacher HTML repeats the title as its subtitle")
    assert_true("create" not in visible.casefold(), "teacher HTML exposes an internal cognitive enum")
    assert_true(not re.search(r'(?m)^tr\[data-row-height-mm\] td\{border:none', html),
                "generic fill-table CSS strips observation/checklist column borders")
    assert_true('table[data-block-type="answer_box"] tr[data-row-height-mm] td' in html,
                "ruled-line CSS must be scoped to answer boxes only")

    # physical pages.
    assert_true(html_pages(paths["html"]) == 3, f"teacher HTML must have 3 A4 pages, got {html_pages(paths['html'])}")
    assert_true(docx_pagebreaks(paths["docx"]) == 2, f"teacher DOCX must have 2 page breaks, got {docx_pagebreaks(paths['docx'])}")
    assert_true(hwpx_pagebreaks(paths["hwpx"]) == 2, f"teacher HWPX must have 2 page breaks, got {hwpx_pagebreaks(paths['hwpx'])}")

    # captions actually reach the rendered HTML (not DOM tokens only, but real visible captions).
    for cap in (CAP_FLOW, CAP_MATRIX, CAP_OBSERVE):
        assert_true(cap in html, f"teacher HTML missing visible caption {cap!r}")


# --------------------------------------------------------------------------- #
# Student worksheet
# --------------------------------------------------------------------------- #

def check_student(gid: str, doc: dict, paths: dict) -> None:
    blocks = _blocks(doc)
    caps = _captions(blocks)

    for cap in (CAP_HEADER, CAP_SUCCESS, CAP_SOURCE, CAP_SELFCHECK):
        assert_true(any(cap in c for c in caps), f"{gid} worksheet missing required table: {cap!r} (have {sorted(caps)})")

    # header fields: blank 학년/반/번호/이름/날짜.
    header = next(b for b in blocks if b.get("caption") and CAP_HEADER in b["caption"])
    header_text = " ".join(header["headers"])
    for field in ("학년", "반", "번호", "이름", "날짜"):
        assert_true(field in header_text, f"{gid} header missing blank field {field!r}: {header['headers']}")

    # real source: atmosphere data table (>=4 layer rows) + greenhouse/radiation card.
    source = next(b for b in blocks if b["block_type"] == "data_table" and CAP_SOURCE in b["caption"])
    assert_true(len(source["cells"]) >= 4, f"{gid} atmosphere source must list >=4 layers, got {len(source['cells'])}")
    source_join = " ".join(source["headers"]) + " " + " ".join(c for r in source["cells"] for c in r)
    for term in ("대류권", "성층권", "고도", "기온"):
        assert_true(term in source_join, f"{gid} atmosphere source missing real content {term!r}")
    assert_true(any(b["block_type"] == "source_card" and ("복사" in b["body"] or "온실" in b["body"]) for b in blocks),
                f"{gid} worksheet missing greenhouse/radiation evidence card")

    # 3-step overview + submission instruction.
    notes = " ".join(b["text"] for b in blocks if b["block_type"] == "student_note")
    assert_true("순서" in notes or re.search(r"1\..*2\..*3\.", notes, re.DOTALL), f"{gid} missing 3-step overview")
    assert_true("제출" in notes, f"{gid} worksheet missing a submission instruction")

    # real writing space + tasks + exactly one exit ticket.
    assert_true(sum(1 for b in blocks if b["block_type"] == "student_task") >= 2, f"{gid} needs >=2 core tasks")
    assert_true(sum(1 for b in blocks if b["block_type"] == "answer_box") >= 2, f"{gid} needs >=2 answer spaces")
    assert_true(sum(1 for b in blocks if b["block_type"] == "exit_ticket") == 1, f"{gid} needs exactly one exit ticket")

    # NO generic placeholders.
    all_text = _student_all_text(blocks)
    for ph in STUDENT_PLACEHOLDERS:
        assert_true(ph not in all_text, f"{gid} worksheet contains generic placeholder {ph!r}")

    # no malformed row widths.
    bad = _row_widths_ok(blocks)
    assert_true(not bad, f"{gid} worksheet has malformed table rows: {bad}")

    # physical pages.
    assert_true(html_pages(paths["html"]) == 2, f"{gid} HTML must have 2 A4 pages, got {html_pages(paths['html'])}")
    assert_true(docx_pagebreaks(paths["docx"]) == 1, f"{gid} DOCX must have 1 page break, got {docx_pagebreaks(paths['docx'])}")
    assert_true(hwpx_pagebreaks(paths["hwpx"]) == 1, f"{gid} HWPX must have 1 page break, got {hwpx_pagebreaks(paths['hwpx'])}")

    # final user surface: no internal ids and no duplicated target copy.
    visible = visible_html_text(paths["html"])
    assert_true(doc["document_id"] not in visible, f"{gid} HTML exposes an internal document id")
    target = doc["content"]["individualization_contract"]["target_text"]
    assert_true(visible.count(target) == 1,
                f"{gid} target must appear exactly once on the visible worksheet, got {visible.count(target)}")


def _student_all_text(blocks: list) -> str:
    out = []
    for b in blocks:
        for k in ("text", "body", "prompt", "caption", "source", "title"):
            v = b.get(k)
            if isinstance(v, str):
                out.append(v)
        for k in ("headers", "stems"):
            for v in b.get(k, []) or []:
                out.append(str(v))
        for r in b.get("rows", []) or []:
            out.extend(str(c) for c in r)
        for r in b.get("cells", []) or []:
            out.extend(str(c) for c in r)
    return "\n".join(out)


def main() -> None:
    ir = build_sample_ir()
    docs = {d["document_id"]: d for d in ir["lesson_package"]["documents"]}
    with tempfile.TemporaryDirectory() as td:
        rendered = render_package(ir, td)
        check_teacher(docs[TEACHER_DOC], rendered[TEACHER_DOC])
        for gid in GROUP_DOCS.values():
            check_student(gid, docs[gid], rendered[gid])

    print("PASS validate_field_readiness")
    print("- teacher plan: 3 A4 pages; overview/45-min flow(=45)/A-B-C matrix/regroup/observation/interpretation tables")
    print("- teacher observation grid carries blank student rows; no label duplication; no malformed rows")
    print("- each student worksheet: 2 A4 pages; header blanks, real atmosphere source + greenhouse card")
    print("- student success + self-check checklists, 3-step overview, submission instruction; no placeholders")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL validate_field_readiness: {error}")
        raise SystemExit(1) from error
