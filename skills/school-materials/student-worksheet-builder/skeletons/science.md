# 과학 활동지 skeleton (중학교 기준, 단일 IR content.blocks)

관찰 → 탐구 → 증거 → 설명 흐름을 블록 순서로 고정한다. 블록 어휘는 `providers/materials/worksheet.py`.

## 블록 순서
1. `student_note` — 오늘의 탐구 맥락(정답 설명 금지).
2. `source_card` — 관찰/자료(그림·데이터 출처).
3. `data_table` — 정량 자료. 색-전용 지시가 있으면 `pattern`(빗금/점선)로 흑백 대체 채널을 반드시 둔다.
4. `student_task` (`analyze`) — 자료에서 패턴/구조를 표시하는 과제.
5. `fill_table` — 관찰 결과를 학생이 채우는 표.
6. `page_break`
7. `sentence_support` — 설명 문장틀("나는 ___ 자료를 근거로 ___").
8. `student_task` (`evaluate`) — 증거로 현상을 설명하는 과제.
9. `answer_box` (`extended`, min_lines≥6, min_height≥48mm) — 설명 쓰기.
10. `answer_box` (`paragraph`) — 근거 쓰기(쓰기 페이지 answer-area ratio ≥ 0.30 확보).
11. `group_cohesion` — `^Group [ABC]$` 중립 라벨 + `shared_task_refs`.
12. `exit_ticket` (`evaluate`, `targets_hardest_case:true`) — 성취기준 최난 구조 겨냥, 마지막 과제 블록.

## 물리성 규칙
- 총 예상 분량은 45분의 0.5~1.0배. 설명/추론 과제를 삭제하지 않는다(rigor 보존).
- 설명 과제 옆에는 실제 쓰기 공간(answer_box)을 배치한다.
