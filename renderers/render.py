"""Minimal own renderer: single canonical lesson-package IR -> real HWPX/DOCX/HTML.

Each rendered file embeds an extractable backport marker at the schema's canonical
location and encodes content paragraphs with data-content-id / data-provenance-*
attributes so the file can be re-parsed and 3-way parity verified for real. This is
an independent implementation (no anthropics renderer code); it is intentionally
minimal (spike scope), not a full HWP/OOXML layout engine.
"""
from __future__ import annotations

import hashlib
import html as htmllib
import json
import re
import zipfile
from pathlib import Path

CANONICAL_LOCATIONS = {
    "hwpx": {"locator_kind": "package-member", "locator_value": "META-INF/kteacher-backport-marker.json", "validator_extraction_method": "read package member META-INF/kteacher-backport-marker.json and parse JSON"},
    "docx": {"locator_kind": "opc-part", "locator_value": "/customXml/kteacher-backport-marker.json", "validator_extraction_method": "read OPC custom XML part /customXml/kteacher-backport-marker.json and parse JSON"},
    "html": {"locator_kind": "dom-node", "locator_value": "script#kteacher-backport-marker", "validator_extraction_method": "read <script id=kteacher-backport-marker type=application/json> from document head and parse text as JSON"},
}
# ZIP member paths (marker), per format.
_HWPX_MARKER = "META-INF/kteacher-backport-marker.json"
_DOCX_MARKER = "customXml/kteacher-backport-marker.json"

_XML_ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}


def _xesc(s: str) -> str:
    return "".join(_XML_ESC.get(c, c) for c in s)


# --- canonical content + marker ------------------------------------------------

def canonical_content(document: dict) -> dict:
    content = document.get("content", {})
    return {
        "document_id": document["document_id"],
        "document_class": document["document_class"],
        "title": document["title"],
        "required_content": [{"content_id": s["content_id"], "text": s["text"]} for s in content.get("sections", [])],
        "provenance_markers": [
            {"record_id": m["record_id"], "label": m["label"], "evidence_text": m["evidence_text"]}
            for m in content.get("provenance_markers", [])
        ],
        "unresolved_boundary_markers": list(content.get("unresolved_boundary_markers", [])),
        "blocks": list(content.get("blocks", [])),
    }


def content_fingerprint(canonical: dict) -> str:
    payload = json.dumps(
        {k: canonical[k] for k in ("required_content", "provenance_markers", "unresolved_boundary_markers", "blocks")},
        ensure_ascii=False, sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_marker(ir: dict, fmt: str, fingerprint: str, render_revision_id: str, rendered_at: str = "2026-07-16T00:00:00Z") -> dict:
    return {
        "backport_marker_version": "1",
        "workflow_id": ir["workflow_id"],
        "ir_id": ir["ir_id"],
        "ir_revision_id": ir["ir_revision_id"],
        "render_revision_id": render_revision_id,
        "renderer_format": fmt,
        "renderer_version": "kteacher-minimal-renderer@2026.07.16",
        "rendered_at": rendered_at,
        "content_fingerprint": fingerprint,
        "authoritative_source": "json-ir",
        "manual_edit_status": "clean",
        "canonical_locations": CANONICAL_LOCATIONS,
    }


# --- paragraph encoding (round-trippable) --------------------------------------

def _content_paras(canonical: dict, ptag: str, ttag: str | None) -> str:
    out = []
    for item in canonical["required_content"]:
        inner = f"<{ttag}>{_xesc(item['text'])}</{ttag}>" if ttag else _xesc(item["text"])
        out.append(f'<{ptag} data-content-id="{_xesc(item["content_id"])}">{inner}</{ptag}>')
    for m in canonical["provenance_markers"]:
        inner = f"<{ttag}>{_xesc(m['evidence_text'])}</{ttag}>" if ttag else _xesc(m["evidence_text"])
        out.append(
            f'<{ptag} data-provenance-record-id="{_xesc(m["record_id"])}" data-label="{_xesc(m["label"])}">{inner}</{ptag}>'
        )
    return "\n".join(out)

# --- block encoding (real tables + answer-space, round-trippable) --------------

_BLOCK_TAGS = {
    "html": {"para": "p", "table": "table", "row": "tr", "cell": "td"},
    "hwpx": {"para": "hp:p", "table": "hp:tbl", "row": "hp:tr", "cell": "hp:tc"},
    "docx": {"para": "w:p", "table": "w:tbl", "row": "w:tr", "cell": "w:tc"},
}


def _block_attrs(block: dict) -> str:
    payload = json.dumps(block, ensure_ascii=False, sort_keys=True)
    return (
        f'data-block-id="{_xesc(block["block_id"])}" '
        f'data-block-type="{_xesc(block["block_type"])}" '
        f'data-block-json="{_xesc(payload)}"'
    )


def _cell_xml(value, tags: dict, fmt: str) -> str:
    """Emit a table cell with the paragraph/run/text nesting required by the
    target office format. Empty cells still receive a text node container."""
    c = tags["cell"]
    text = _xesc(str(value))
    if fmt == "docx":
        return f'<{c}><w:p><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p></{c}>'
    if fmt == "hwpx":
        return f'<{c}><hp:subList><hp:p><hp:run><hp:t>{text}</hp:t></hp:run></hp:p></hp:subList></{c}>'
    return f"<{c}>{text}</{c}>"


def _row_xml(values: list, tags: dict, fmt: str, row_height_mm: float | None = None) -> str:
    r = tags["row"]
    cells = "".join(_cell_xml(v, tags, fmt) for v in values)
    if row_height_mm is None:
        return f"<{r}>{cells}</{r}>"
    if fmt == "docx":
        twips = max(1, round(row_height_mm * 56.6929))
        return f'<{r}><w:trPr><w:trHeight w:val="{twips}" w:hRule="atLeast"/></w:trPr>{cells}</{r}>'
    if fmt == "hwpx":
        return f'<{r} data-row-height-mm="{row_height_mm:g}">{cells}</{r}>'
    return f'<{r} style="height:{row_height_mm:g}mm" data-row-height-mm="{row_height_mm:g}">{cells}</{r}>'


def _table_block(block: dict, header: list, rows: list, tags: dict, fmt: str,
                 row_height_mm: float | None = None) -> str:
    t = tags["table"]
    parts = [f"<{t} {_block_attrs(block)}>"]
    if header:
        parts.append(_row_xml(header, tags, fmt))
    for row in rows:
        parts.append(_row_xml(row, tags, fmt, row_height_mm))
    parts.append(f"</{t}>")
    return "".join(parts)


def _block_visible_text(block: dict) -> str:
    bt = block["block_type"]
    if bt in ("student_task", "exit_ticket"):
        return block["prompt"]
    if bt == "student_note":
        return block["text"]
    if bt == "source_card":
        citation = f' ({block["citation"]})' if block.get("citation") else ""
        return f'{block["title"]}: {block["body"]} — {block["source"]}{citation}'
    if bt == "sentence_support":
        return " / ".join(block["stems"])
    if bt == "number_line":
        return f'{block.get("label", "수직선")}: {block["min"]}~{block["max"]} (step {block["step"]})'
    if bt == "group_cohesion":
        return f'{block["group_label"]}: ' + ", ".join(block["members"])
    if bt == "page_break":
        return "[page-break]"
    return ""


def _content_blocks(canonical: dict, fmt: str) -> str:
    """Encode content.blocks into real per-format tables + answer-space nodes, each
    carrying data-block-id/data-block-type and a round-trippable data-block-json."""
    tags = _BLOCK_TAGS[fmt]
    para = tags["para"]
    out = []
    for block in canonical.get("blocks", []):
        bt = block["block_type"]
        if bt == "fill_table":
            out.append(_table_block(block, block["headers"], block["rows"], tags, fmt,
                                    row_height_mm=block["row_height_mm"]))
        elif bt == "data_table":
            out.append(_table_block(block, block["headers"], block["cells"], tags, fmt))
        elif bt == "answer_box":
            # Real ruled answer-space: one empty ruled row per required line.
            line_height_mm = block["min_height_mm"] / max(1, block["min_lines"])
            out.append(_table_block(block, [], [[""] for _ in range(block["min_lines"])], tags, fmt,
                                    row_height_mm=line_height_mm))
        else:
            out.append(f'<{para} {_block_attrs(block)}>{_xesc(_block_visible_text(block))}</{para}>')
    return "\n".join(out)


# --- renderers -----------------------------------------------------------------

def render_html(canonical: dict, marker: dict, path: Path) -> None:
    body = _content_paras(canonical, "p", None)
    blocks_body = _content_blocks(canonical, "html")
    if blocks_body:
        body = f"{body}\n{blocks_body}"
    doc = (
        "<!doctype html>\n<html lang=\"ko\"><head><meta charset=\"utf-8\">"
        f"<title>{_xesc(canonical['title'])}</title>"
        f'<script id="kteacher-backport-marker" type="application/json">{json.dumps(marker, ensure_ascii=False)}</script>'
        f"</head><body data-document-id=\"{_xesc(canonical['document_id'])}\" "
        f"data-document-class=\"{_xesc(canonical['document_class'])}\">"
        f"<h1>{_xesc(canonical['title'])}</h1>\n{body}\n</body></html>"
    )
    path.write_text(doc, encoding="utf-8")


def _write_zip(path: Path, members: dict[str, str], mimetype: str | None = None) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        if mimetype is not None:
            # OCF convention: mimetype stored first, uncompressed.
            zi = zipfile.ZipInfo("mimetype")
            zi.compress_type = zipfile.ZIP_STORED
            z.writestr(zi, mimetype)
        for name, data in members.items():
            z.writestr(name, data)


def render_hwpx(canonical: dict, marker: dict, path: Path) -> None:
    body = _content_paras(canonical, "hp:p", "hp:t")
    blocks_body = _content_blocks(canonical, "hwpx")
    if blocks_body:
        body = f"{body}\n{blocks_body}"
    section = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
        'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
        f'data-document-id="{_xesc(canonical["document_id"])}" data-document-class="{_xesc(canonical["document_class"])}" '
        f'data-title="{_xesc(canonical["title"])}">\n{body}\n</hs:sec>'
    )
    members = {
        "version.xml": '<?xml version="1.0" encoding="UTF-8"?><hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" tagetApplication="WORDPROCESSOR"/>',
        "Contents/content.hpf": '<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf"/>',
        "Contents/section0.xml": section,
        "META-INF/container.xml": '<?xml version="1.0" encoding="UTF-8"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="Contents/content.hpf"/></rootfiles></container>',
        _HWPX_MARKER: json.dumps(marker, ensure_ascii=False),
    }
    _write_zip(path, members, mimetype="application/hwp+zip")


def render_docx(canonical: dict, marker: dict, path: Path) -> None:
    body = _content_paras(canonical, "w:p", "w:t")
    blocks_body = _content_blocks(canonical, "docx")
    if blocks_body:
        body = f"{body}\n{blocks_body}"
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        f'data-document-id="{_xesc(canonical["document_id"])}" data-document-class="{_xesc(canonical["document_class"])}" '
        f'data-title="{_xesc(canonical["title"])}"><w:body>\n{body}\n</w:body></w:document>'
    )
    members = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        "word/document.xml": document,
        _DOCX_MARKER: json.dumps(marker, ensure_ascii=False),
    }
    _write_zip(path, members)


def render_all(ir: dict, out_dir: str | Path, *, document_index: int = 0) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    document = ir["lesson_package"]["documents"][document_index]
    canonical = canonical_content(document)
    fp = content_fingerprint(canonical)
    paths = {}
    for i, (fmt, renderer) in enumerate((("hwpx", render_hwpx), ("docx", render_docx), ("html", render_html))):
        marker = build_marker(ir, fmt, fp, render_revision_id=f"render-{2100 + i}")
        p = out_dir / f"{document['document_id']}.{fmt}"
        renderer(canonical, marker, p)
        paths[fmt] = str(p)
    return paths

SUPPORTED_RENDER_TARGETS = ["hwpx", "docx", "html"]


def render_package(ir: dict, out_dir: str | Path) -> dict:
    """Render every document in the package to all three formats.

    Returns `{document_id: {fmt: path}}`. Refuses duplicate document ids and any
    document whose render_targets are not exactly the supported HWPX/DOCX/HTML set.
    Reuses `render_all` per document (the single-document path stays unchanged)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    documents = ir["lesson_package"]["documents"]
    seen: set = set()
    result: dict = {}
    for index, document in enumerate(documents):
        did = document["document_id"]
        if did in seen:
            raise ValueError(f"duplicate document id in package: {did!r}")
        seen.add(did)
        if document.get("render_targets") != SUPPORTED_RENDER_TARGETS:
            raise ValueError(f"unsupported render targets for {did!r}: {document.get('render_targets')!r}")
        result[did] = render_all(ir, out_dir, document_index=index)
    return result

# --- extractors (real round-trip) ----------------------------------------------

_PARA_RE = re.compile(r"<(?:hp:p|w:p|p)\b([^>]*)>(.*?)</(?:hp:p|w:p|p)>", re.DOTALL)
_ATTR_RE = re.compile(r'([\w:-]+)="([^"]*)"')
_TEXT_RE = re.compile(r"<[^>]+>")


def _parse_paras(xml: str) -> tuple[list, list]:
    content, prov = [], []
    for attrs_s, inner in _PARA_RE.findall(xml):
        attrs = dict(_ATTR_RE.findall(attrs_s))
        text = htmllib.unescape(_TEXT_RE.sub("", inner)).strip()
        if "data-content-id" in attrs:
            content.append({"content_id": attrs["data-content-id"], "text": text})
        elif "data-provenance-record-id" in attrs:
            prov.append({"record_id": attrs["data-provenance-record-id"], "label": htmllib.unescape(attrs.get("data-label", "")), "evidence_text": text})
    return content, prov

_BLOCK_RE = re.compile(r'<(table|hp:tbl|w:tbl|p|hp:p|w:p)\b([^>]*\bdata-block-id="[^"]*"[^>]*)>(.*?)</\1>', re.DOTALL)
_ROW_RE = re.compile(r"<(?:tr|hp:tr|w:tr)\b")
_CELL_RE = re.compile(r"<(?:td|hp:tc|w:tc)\b")
_FIRST_ROW_RE = re.compile(r"<(?:tr|hp:tr|w:tr)\b[^>]*>(.*?)</(?:tr|hp:tr|w:tr)>", re.DOTALL)


def _parse_blocks(xml: str) -> list:
    """Round-trip content.blocks from a rendered file: recover exact semantic fields
    from data-block-json and recompute the real rendered table/answer-space shape."""
    blocks = []
    for tag, attrs_s, inner in _BLOCK_RE.findall(xml):
        attrs = dict(_ATTR_RE.findall(attrs_s))
        payload = json.loads(htmllib.unescape(attrs["data-block-json"]))
        shape = None
        if tag in ("table", "hp:tbl", "w:tbl"):
            nrows = len(_ROW_RE.findall(inner))
            first = _FIRST_ROW_RE.search(inner)
            ncols = len(_CELL_RE.findall(first.group(1))) if first else 0
            shape = {"rows": nrows, "cols": ncols}
        blocks.append({
            "block_id": attrs["data-block-id"],
            "block_type": attrs["data-block-type"],
            "block": payload,
            "rendered_shape": shape,
        })
    return blocks


def _extract_zip(path: Path, marker_member: str, content_member: str) -> dict:
    with zipfile.ZipFile(path) as z:
        marker = json.loads(z.read(marker_member).decode("utf-8"))
        xml = z.read(content_member).decode("utf-8")
    content, prov = _parse_paras(xml)
    head = re.search(r'data-document-id="([^"]*)"[^>]*data-document-class="([^"]*)"[^>]*data-title="([^"]*)"', xml)
    return {
        "renderer_format": marker["renderer_format"],
        "document_id": head.group(1) if head else None,
        "document_class": head.group(2) if head else None,
        "title": htmllib.unescape(head.group(3)) if head else None,
        "required_content": content,
        "provenance_markers": prov,
        "unresolved_boundary_markers": [],
        "blocks": _parse_blocks(xml),
        "embedded_backport_marker_locator": marker_member,
        "embedded_backport_marker": marker,
    }


def extract_hwpx(path: str | Path) -> dict:
    return _extract_zip(Path(path), _HWPX_MARKER, "Contents/section0.xml")


def extract_docx(path: str | Path) -> dict:
    return _extract_zip(Path(path), _DOCX_MARKER, "word/document.xml")


def extract_html(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r'<script id="kteacher-backport-marker" type="application/json">(.*?)</script>', text, re.DOTALL)
    marker = json.loads(m.group(1))
    content, prov = _parse_paras(text)
    head = re.search(r'data-document-id="([^"]*)"[^>]*data-document-class="([^"]*)"', text)
    title = re.search(r"<h1>(.*?)</h1>", text, re.DOTALL)
    return {
        "renderer_format": "html",
        "document_id": head.group(1) if head else None,
        "document_class": head.group(2) if head else None,
        "title": htmllib.unescape(title.group(1)) if title else None,
        "required_content": content,
        "provenance_markers": prov,
        "unresolved_boundary_markers": [],
        "blocks": _parse_blocks(text),
        "embedded_backport_marker_locator": "script#kteacher-backport-marker",
        "embedded_backport_marker": marker,
    }


def extract_all(paths: dict) -> dict:
    return {"hwpx": extract_hwpx(paths["hwpx"]), "docx": extract_docx(paths["docx"]), "html": extract_html(paths["html"])}


def verify_parity(extracted: dict) -> tuple[bool, list]:
    """3-way parity: identical content/provenance/title across formats; each marker at
    its canonical location; identical content_fingerprint (same source IR)."""
    reasons = []
    fmts = ["hwpx", "docx", "html"]
    ref = extracted["hwpx"]
    for f in fmts:
        e = extracted[f]
        if e["required_content"] != ref["required_content"]:
            reasons.append(f"{f}: required_content drift")
        if e["provenance_markers"] != ref["provenance_markers"]:
            reasons.append(f"{f}: provenance_markers drift")
        if e["title"] != ref["title"] or e["document_id"] != ref["document_id"]:
            reasons.append(f"{f}: title/document_id drift")
        loc = CANONICAL_LOCATIONS[f]["locator_value"].lstrip("/")
        got = e["embedded_backport_marker_locator"].lstrip("/")
        if f != "html" and got != loc:
            reasons.append(f"{f}: marker not at canonical location ({got})")
        if e["embedded_backport_marker"]["content_fingerprint"] != ref["embedded_backport_marker"]["content_fingerprint"]:
            reasons.append(f"{f}: content_fingerprint drift (content not from same IR)")
        if e["embedded_backport_marker"]["renderer_format"] != f:
            reasons.append(f"{f}: marker renderer_format mismatch")
        if e.get("blocks", []) != ref.get("blocks", []):
            reasons.append(f"{f}: blocks drift")
    return (len(reasons) == 0, reasons)
