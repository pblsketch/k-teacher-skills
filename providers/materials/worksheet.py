"""Direct-entry student worksheet semantics: an additive `content.blocks` vocabulary
on the single canonical lesson-package IR, deterministic physical-workload gates, a
facet block-recursion helper set, and a standalone quick-draft (context-only) gate.

Single source of truth: worksheet blocks are additive `content.blocks[]` on the
existing IR (`content` is `additionalProperties:true`). No second IR, no second
renderer. Block shapes are pinned by `schemas/lesson-package-ir.schema.json`
`$defs/worksheetBlock` (referenced only by `tests/validate_worksheet_physical.py`).

Independent implementation (no third-party code).
"""
from __future__ import annotations

import re

# --- block vocabulary constructors ---------------------------------------------
# Each block is an ordered dict `{block_id, block_type, ...fields}`. Keys are emitted
# in a deterministic order so the extracted semantic golden stays byte-stable.

BLOCK_TYPES = (
    "student_task",
    "answer_box",
    "fill_table",
    "data_table",
    "number_line",
    "source_card",
    "group_cohesion",
    "page_break",
    "student_note",
    "sentence_support",
    "exit_ticket",
)

COGNITIVE_DEMANDS = ("recall", "apply", "analyze", "evaluate", "create")
RESPONSE_DEMANDS = ("short", "sentence", "paragraph", "extended")


def student_task(block_id: str, *, task_ref: str, prompt: str, cognitive_demand: str) -> dict:
    return {"block_id": block_id, "block_type": "student_task", "task_ref": task_ref, "prompt": prompt, "cognitive_demand": cognitive_demand}


def answer_box(block_id: str, *, response_demand: str, min_lines: int, min_height_mm: int, label: str | None = None) -> dict:
    block = {"block_id": block_id, "block_type": "answer_box", "response_demand": response_demand, "min_lines": min_lines, "min_height_mm": min_height_mm}
    if label is not None:
        block["label"] = label
    return block


FILL_TABLE_ROW_HEIGHT_MM = 26


def fill_table(block_id: str, *, headers: list, rows: list, caption: str | None = None,
               row_height_mm: int = FILL_TABLE_ROW_HEIGHT_MM) -> dict:
    block = {
        "block_id": block_id,
        "block_type": "fill_table",
        "headers": list(headers),
        "rows": [list(r) for r in rows],
        "row_height_mm": row_height_mm,
    }
    if caption is not None:
        block["caption"] = caption
    return block


def data_table(block_id: str, *, caption: str, headers: list, cells: list, pattern: str | None = None) -> dict:
    block = {"block_id": block_id, "block_type": "data_table", "caption": caption, "headers": list(headers), "cells": [list(r) for r in cells]}
    if pattern is not None:
        block["pattern"] = pattern
    return block


def number_line(block_id: str, *, minimum, maximum, step, ticks: list, label: str | None = None) -> dict:
    block = {"block_id": block_id, "block_type": "number_line", "min": minimum, "max": maximum, "step": step, "ticks": list(ticks)}
    if label is not None:
        block["label"] = label
    return block


def source_card(block_id: str, *, title: str, body: str, source: str, citation: str | None = None) -> dict:
    block = {"block_id": block_id, "block_type": "source_card", "title": title, "body": body, "source": source}
    if citation is not None:
        block["citation"] = citation
    return block


def group_cohesion(block_id: str, *, group_label: str, members: list, shared_task_refs: list) -> dict:
    return {"block_id": block_id, "block_type": "group_cohesion", "group_label": group_label, "members": list(members), "shared_task_refs": list(shared_task_refs)}


def page_break(block_id: str) -> dict:
    return {"block_id": block_id, "block_type": "page_break"}


def student_note(block_id: str, *, text: str) -> dict:
    return {"block_id": block_id, "block_type": "student_note", "text": text}


def sentence_support(block_id: str, *, stems: list) -> dict:
    return {"block_id": block_id, "block_type": "sentence_support", "stems": list(stems)}


def exit_ticket(block_id: str, *, prompt: str, cognitive_demand: str) -> dict:
    return {"block_id": block_id, "block_type": "exit_ticket", "prompt": prompt, "cognitive_demand": cognitive_demand, "targets_hardest_case": True}


# --- deterministic physical-workload thresholds (RC1) --------------------------

GRADE_PERIOD_MINUTES = {"초등학교": 40, "중학교": 45, "고등학교": 50}
_TASK_MINUTES = {"recall": 2, "apply": 3, "analyze": 5, "evaluate": 6, "create": 8}
_ANSWER_MINUTES = {"short": 2, "sentence": 3, "paragraph": 6, "extended": 9}
MIN_LINES = {"short": 1, "sentence": 2, "paragraph": 4, "extended": 6}
MIN_HEIGHT_MM = {"short": 8, "sentence": 16, "paragraph": 32, "extended": 48}
MAX_BLOCKS_PER_PAGE = 14
MAX_PROMPT_CHARS_PER_PAGE = 1600
MIN_ANSWER_AREA_RATIO = 0.30
A4_CONTENT_MM = 257
_COGNITIVE_ORDINAL = {"recall": 1, "apply": 2, "analyze": 3, "evaluate": 4, "create": 5}

# Black/white safety: a color-only reference must ship a redundant non-color channel.
_COLOR_ONLY = re.compile(r"(빨간|파란|초록|노란|red|blue|green|yellow)\s*(색|칸|영역|부분|글씨|표시)")
GROUP_LABEL_RE = re.compile(r"^Group [ABC]$")


def block_minutes(block: dict) -> float:
    bt = block["block_type"]
    if bt == "student_task":
        return _TASK_MINUTES[block["cognitive_demand"]]
    if bt == "answer_box":
        return _ANSWER_MINUTES[block["response_demand"]]
    if bt == "fill_table":
        return 1.5 * len(block["rows"])
    if bt in ("data_table", "number_line", "source_card"):
        return 2
    if bt == "exit_ticket":
        return 5
    return 0


def estimated_minutes(blocks: list) -> float:
    return sum(block_minutes(b) for b in blocks)


def _pages(blocks: list) -> list:
    """Split the ordered block list into page segments delimited by page_break."""
    pages: list = [[]]
    for b in blocks:
        if b["block_type"] == "page_break":
            pages.append([])
        else:
            pages[-1].append(b)
    return [p for p in pages if p] or [[]]


def _page_prompt_chars(page: list) -> int:
    total = 0
    for b in page:
        for key in ("prompt", "body", "caption"):
            v = b.get(key)
            if isinstance(v, str):
                total += len(v)
    return total


def check_physical_workload(blocks: list, school_level: str) -> list:
    """Deterministic physical-workload gate. Returns a list of violation strings
    (empty == clean). Each violation is prefixed by the failing check name."""
    violations: list[str] = []
    if school_level not in GRADE_PERIOD_MINUTES:
        return [f"period_budget: unknown school_level {school_level!r}"]
    period = GRADE_PERIOD_MINUTES[school_level]

    # 1. Period budget: half a period .. one full period.
    est = estimated_minutes(blocks)
    if est > period:
        violations.append(f"period_budget: {est} min over one {school_level} period ({period})")
    if est < 0.5 * period:
        violations.append(f"period_budget: {est} min under half a {school_level} period ({0.5 * period})")

    # 2. Answer-space minimums per response_demand.
    for b in blocks:
        if b["block_type"] != "answer_box":
            continue
        rd = b["response_demand"]
        if b["min_lines"] < MIN_LINES[rd]:
            violations.append(f"answer_minimums: {b['block_id']} min_lines {b['min_lines']} < {MIN_LINES[rd]} for {rd}")
        if b["min_height_mm"] < MIN_HEIGHT_MM[rd]:
            violations.append(f"answer_minimums: {b['block_id']} min_height_mm {b['min_height_mm']} < {MIN_HEIGHT_MM[rd]} for {rd}")

    # 3. Page density: block count, prompt chars, answer-area ratio for writing pages.
    for i, page in enumerate(_pages(blocks)):
        if len(page) > MAX_BLOCKS_PER_PAGE:
            violations.append(f"page_density: page {i} has {len(page)} blocks > {MAX_BLOCKS_PER_PAGE}")
        chars = _page_prompt_chars(page)
        if chars > MAX_PROMPT_CHARS_PER_PAGE:
            violations.append(f"page_density: page {i} has {chars} prompt chars > {MAX_PROMPT_CHARS_PER_PAGE}")
        boxes = [b for b in page if b["block_type"] == "answer_box"]
        fill_tables = [b for b in page if b["block_type"] == "fill_table"]
        if boxes or fill_tables:
            answer_area = sum(b["min_height_mm"] for b in boxes)
            answer_area += sum(len(b["rows"]) * b["row_height_mm"] for b in fill_tables)
            ratio = answer_area / A4_CONTENT_MM
            if ratio < MIN_ANSWER_AREA_RATIO:
                violations.append(f"page_density: page {i} writing area ratio {ratio:.3f} < {MIN_ANSWER_AREA_RATIO}")

    # 4. Exit-ticket hardest-case rule.
    task_bearing = [b for b in blocks if b["block_type"] in ("student_task", "exit_ticket")]
    tickets = [b for b in blocks if b["block_type"] == "exit_ticket"]
    student_tasks = [b for b in blocks if b["block_type"] == "student_task"]
    if len(tickets) != 1:
        violations.append(f"exit_ticket: expected exactly one exit_ticket, found {len(tickets)}")
    else:
        ticket = tickets[0]
        if not ticket.get("targets_hardest_case"):
            violations.append(f"exit_ticket: {ticket['block_id']} must set targets_hardest_case=true")
        if task_bearing and task_bearing[-1] is not ticket:
            violations.append("exit_ticket: exit_ticket must be the last student task-bearing block")
        if student_tasks:
            hardest = max(_COGNITIVE_ORDINAL[t["cognitive_demand"]] for t in student_tasks)
            if _COGNITIVE_ORDINAL[ticket["cognitive_demand"]] != hardest:
                violations.append(
                    f"exit_ticket: demand {ticket['cognitive_demand']} != hardest task demand ordinal {hardest}"
                )

    # 5. Black/white safety: color-only references need a non-color redundant channel.
    for b in blocks:
        colored = any(_COLOR_ONLY.search(leaf) for leaf in iter_block_string_leaves([b]))
        if colored and not (b.get("pattern") or b.get("label")):
            violations.append(f"bw_safety: {b['block_id']} uses color-only reference with no pattern/label channel")

    # 6. Group cohesion + neutrality.
    for b in blocks:
        if b["block_type"] != "group_cohesion":
            continue
        labels = [b["group_label"], *b.get("members", [])]
        for label in labels:
            if not GROUP_LABEL_RE.match(label):
                violations.append(f"group_cohesion: {b['block_id']} label {label!r} not neutral ^Group [ABC]$")
        if not b.get("shared_task_refs"):
            violations.append(f"group_cohesion: {b['block_id']} has no shared_task_refs")
    return violations


# --- facet block-recursion helpers (RC2, consumed by builder.check_facet_separation) ---

# Structural keys that must never appear on a student-facet block (presence == leak).
STUDENT_FACET_FORBIDDEN_KEYS = {"answer_key", "solution", "rubric", "weight", "internal_level", "teacher_prompt", "misconception"}

# Separators an upstream model may insert *inside* a forbidden token. They are
# accepted only between the token's own characters; ordinary prose is never globally
# compacted, preventing cross-word false positives such as "발표 준비" -> "표준".
_TOKEN_SEPARATOR_CLASS = r"\s\u200b\u200c\u200d\u2060\ufeff"
_TOKEN_SEPARATOR = rf"[{_TOKEN_SEPARATOR_CLASS}]*"


def _token_body(token: str) -> str:
    compact = re.sub(rf"[{_TOKEN_SEPARATOR_CLASS}]+", "", token)
    return _TOKEN_SEPARATOR.join(re.escape(ch) for ch in compact)


def _ko_pattern(*tokens: str) -> re.Pattern:
    # A left Hangul boundary prevents joining the end of one Korean word to the
    # beginning of another, while allowing natural particles after the token.
    body = "|".join(_token_body(token) for token in tokens)
    return re.compile(rf"(?<![가-힣])(?:{body})", re.IGNORECASE)


def _en_pattern(*tokens: str) -> re.Pattern:
    body = "|".join(_token_body(token) for token in tokens)
    return re.compile(rf"(?<![A-Za-z0-9_])(?:{body})(?![A-Za-z0-9_])", re.IGNORECASE)


def contains_forbidden_term(value: str, term: str) -> bool:
    """Match one configured term with separator tolerance and language-safe bounds."""
    pattern = _ko_pattern(term) if re.search(r"[가-힣]", term) else _en_pattern(term)
    return pattern.search(value) is not None


# Leak-class regexes scan the original leaf. Only token-internal separators are
# tolerated, including zero-width characters; surrounding prose remains intact.
FACET_LEAK_PATTERNS = {
    "answer_key": re.compile(
        rf"{_ko_pattern('정답', '해설', '모범답안').pattern}|{_en_pattern('answer_key', 'solution').pattern}",
        re.IGNORECASE,
    ),
    "misconception": re.compile(
        rf"{_ko_pattern('오개념').pattern}|{_en_pattern('misconception').pattern}", re.IGNORECASE
    ),
    "weight": re.compile(
        rf"{_ko_pattern('배점', '가중치', '반영비율').pattern}|{_en_pattern('weight').pattern}", re.IGNORECASE
    ),
    "internal_level": re.compile(
        rf"{_ko_pattern('기초', '표준', '심화', '상중하').pattern}|{_en_pattern('tier', 'scaffold').pattern}", re.IGNORECASE
    ),
    "teacher_prompt": re.compile(
        rf"{_ko_pattern('교사용', '발문', '관찰기록', '채점', '루브릭', '교사노트').pattern}|{_en_pattern('rubric').pattern}",
        re.IGNORECASE,
    ),
}


def iter_block_string_leaves(blocks):
    """Recursively yield every string leaf value inside content.blocks."""
    def walk(node):
        if isinstance(node, str):
            yield node
        elif isinstance(node, dict):
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, (list, tuple)):
            for v in node:
                yield from walk(v)

    for block in blocks or []:
        yield from walk(block)


def iter_block_forbidden_keys(blocks):
    """Yield (block_id, key) for every forbidden structural key on a student block."""
    def walk(node, block_id):
        if isinstance(node, dict):
            for k, v in node.items():
                normalized_key = re.sub(rf"[{_TOKEN_SEPARATOR_CLASS}]+", "", k).casefold() if isinstance(k, str) else k
                if normalized_key in STUDENT_FACET_FORBIDDEN_KEYS:
                    yield (block_id, k)
                yield from walk(v, block_id)
        elif isinstance(node, (list, tuple)):
            for v in node:
                yield from walk(v, block_id)

    for block in blocks or []:
        yield from walk(block, block.get("block_id", "?"))


# --- worksheet IR composition + standalone quick-draft gate (RC7) --------------

STANDALONE_QUICK_DRAFT_MARKER = "standalone-quick-draft:unverified-provider"


def worksheet_document(*, document_id: str, title: str, task_ids: list, blocks: list,
                       sections: list | None = None, provenance_markers: list | None = None,
                       unresolved_boundary_markers: list | None = None, facet: str = "student") -> dict:
    return {
        "document_id": document_id,
        "document_class": "worksheet",
        "title": title,
        "source_task_ids": list(task_ids),
        "render_targets": ["hwpx", "docx", "html"],
        "content": {
            "facet": facet,
            "sections": sections or [],
            "provenance_markers": provenance_markers or [],
            "unresolved_boundary_markers": unresolved_boundary_markers or [],
            "blocks": blocks,
        },
    }


def build_worksheet_ir(base_ir: dict, document: dict, *, tasks: list) -> dict:
    """Compose a schema-valid lesson-package IR carrying one worksheet document with
    additive `content.blocks`, reusing base_ir's approved envelope."""
    ir = {k: v for k, v in base_ir.items() if k != "lesson_package"}
    ir["lesson_package"] = {"package_id": "pkg-worksheet", "tasks": tasks, "documents": [document]}
    return ir


def _handoff_blocked_boundary() -> dict:
    """A hard, open, handoff-scoped teacher-judgment boundary. Required by the IR schema
    whenever handoff_mode == 'blocked' so a standalone quick draft stays schema-valid."""
    return {
        "boundary_id": "tj-standalone-quick-draft",
        "category": "artifact-scope",
        "description": "Standalone worksheet quick draft: no verified curriculum provider and no teacher approval yet.",
        "affected_output_classes": ["handoff"],
        "blocking_severity": "hard",
        "resolution": {
            "status": "open",
            "teacher_confirmation": {
                "required": True,
                "confirmed": False,
                "confirmation_source": None,
                "confirmation_anchor": {"carrier": "null", "locator_type": "null", "locator_value": None},
            },
            "supporting_evidence": [],
        },
        "allowed_next_ops_while_open": ["ask-question", "summarize", "judgment-only"],
        "created_by": "workflow",
        "last_updated_round": 1,
    }


def build_quick_draft_worksheet_ir(base_ir: dict, *, title: str, standard_code: str,
                                   blocks: list | None = None, sections: list | None = None) -> dict:
    """A standalone (no verified provider, no teacher approval) worksheet request produces
    a CONTEXT-ONLY quick draft that is provably NOT downstream-ready:

    - content.unresolved_boundary_markers carries STANDALONE_QUICK_DRAFT_MARKER (handoff blocked),
    - handoff_mode is 'blocked' with a hard open handoff boundary,
    - CurriculumProvider.verify_standard(standard_code) stays fail-closed,
    - TeacherApprovalGate.evaluate(ir, None) stays fail-closed.
    """
    default_sections = [{"content_id": "quick-draft-note",
                         "text": f"빠른 초안: {standard_code} 관련 활동 아이디어(맥락 전용). 검증된 성취기준 provider와 교사 승인 전에는 배포 불가."}]
    doc = worksheet_document(
        document_id="stu-quick-draft",
        title=title,
        task_ids=["t-quick"],
        blocks=blocks or [],
        sections=sections or default_sections,
        unresolved_boundary_markers=[STANDALONE_QUICK_DRAFT_MARKER],
        facet="student",
    )
    ir = build_worksheet_ir(
        base_ir,
        doc,
        tasks=[{"task_id": "t-quick", "title": title, "document_ids": ["stu-quick-draft"]}],
    )
    ir["handoff_mode"] = "blocked"
    ir["teacher_judgment_boundaries"] = [_handoff_blocked_boundary()]
    return ir


# --- canonical [9과17-01] demo worksheet (중학교 과학) --------------------------
# One shared block sequence used both as the clean physical-gate case and the source
# for the committed extracted-semantic golden. Deterministic, teacher-language-free.

def demo_worksheet_blocks() -> list:
    return [
        student_note("b1", text="오늘은 대기권의 층 구조를 자료로 확인하고, 온실효과를 복사 평형으로 설명해 봅니다."),
        source_card(
            "b2",
            title="대기권 자료",
            body="대기권은 높이에 따라 온도 변화가 다른 네 개의 층으로 나뉩니다. 각 층의 특징을 자료에서 찾아봅니다.",
            source="학급 제공 읽기 자료",
        ),
        data_table(
            "b3",
            caption="높이별 평균 기온 변화 (막대는 빨간색 막대와 빗금 무늬로 함께 구분)",
            headers=["구간", "높이(km)", "기온 경향"],
            cells=[["A", "0~11", "감소"], ["B", "11~50", "증가"], ["C", "50~80", "감소"], ["D", "80 이상", "증가"]],
            pattern="빗금/점선 무늬로 색과 무관하게 구분",
        ),
        student_task("b4", task_ref="t-atmos", prompt="자료를 읽고 대기권을 네 개 층으로 구분하여 표시하시오.", cognitive_demand="analyze"),
        fill_table(
            "b6",
            caption="층 이름과 특징 채우기",
            headers=["층 이름", "높이 범위", "온도 특징"],
            rows=[["", "", ""], ["", "", ""], ["", "", ""]],
        ),
        page_break("b7"),
        sentence_support("b8", stems=["나는 ___ 자료를 근거로 ___라고 생각한다.", "왜냐하면 ___ 때문이다."]),
        student_task("b9", task_ref="t-green", prompt="온실효과가 커질 때 대기 온도 변화를 복사 평형으로 설명하시오.", cognitive_demand="evaluate"),
        answer_box("b10", response_demand="extended", min_lines=6, min_height_mm=48, label="설명 쓰기 칸"),
        answer_box("b11", response_demand="paragraph", min_lines=4, min_height_mm=32, label="근거 쓰기 칸"),
        group_cohesion("b12", group_label="Group A", members=["Group B", "Group C"], shared_task_refs=["t-green"]),
        exit_ticket("b13", prompt="온실효과가 계속 커지면 지표면 온도는 어떻게 될지 근거와 함께 쓰시오.", cognitive_demand="evaluate"),
    ]
