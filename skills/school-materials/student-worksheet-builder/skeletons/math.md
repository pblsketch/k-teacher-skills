# 수학 활동지 skeleton (단일 IR content.blocks)

표현 → 절차 → 추론/일반화 흐름을 블록 순서로 고정한다. 블록 어휘는 `providers/materials/worksheet.py`.

## 블록 순서
1. `student_note` — 오늘의 개념/문제 상황.
2. `number_line` — 수직선/좌표 표현(min/max/step/ticks). 시각 자료는 흑백에서도 구분되게.
3. `student_task` (`apply`) — 절차를 적용해 계산/작도.
4. `answer_box` (`sentence`) — 풀이 과정 쓰기.
5. `fill_table` — 값/규칙을 채우는 표(빈 셀은 학생 기입).
6. `page_break`
7. `sentence_support` — 추론 문장틀("나는 ___ 규칙을 발견했다. 이유는 ___").
8. `student_task` (`evaluate`) — 규칙을 정당화/일반화하는 과제.
9. `answer_box` (`paragraph`) + `answer_box` (`paragraph`) — 일반화 + 정당화(쓰기 페이지 ratio ≥ 0.30).
10. `group_cohesion` — 중립 라벨 모둠 검토.
11. `exit_ticket` (`evaluate`, hardest-case) — 규칙의 근거를 한 문장으로 설명.

## 물리성 규칙
- 계산 반복만으로 채우지 않는다. 추론/정당화(최난 인지 요구)를 반드시 남긴다.
- 색-전용 표시 대신 굵게/빗금 등 흑백 대체 채널을 사용한다.
