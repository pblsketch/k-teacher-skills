# 사회 활동지 skeleton (단일 IR content.blocks)

자료 해석 → 쟁점 분석 → 판단/제안 흐름을 블록 순서로 고정한다. 블록 어휘는 `providers/materials/worksheet.py`.

## 블록 순서
1. `student_note` — 오늘의 사회적 쟁점/맥락.
2. `source_card` — 통계·사례·지도 자료(출처 표기).
3. `data_table` — 통계 표. 색-전용 지시가 있으면 `pattern`으로 흑백 대체.
4. `student_task` (`analyze`) — 자료에서 쟁점의 원인/영향을 분석.
5. `fill_table` — 관점별 입장/근거 정리표.
6. `page_break`
7. `sentence_support` — 판단 문장틀("나는 ___ 근거로 ___를 제안한다").
8. `student_task` (`evaluate`) — 해결 방안을 근거와 함께 제안.
9. `answer_box` (`extended`) + `answer_box` (`paragraph`) — 제안 + 근거(쓰기 페이지 ratio ≥ 0.30).
10. `group_cohesion` — 중립 라벨 모둠 토론.
11. `exit_ticket` (`evaluate`, hardest-case) — 관점을 근거와 함께 정리.

## 물리성 규칙
- 지역/현장 맥락은 교사 최종 확정 대상(unresolved boundary marker)으로 남긴다.
- 분량은 차시의 0.5~1.0배, 근거 사용 인지 요구를 유지한다.
