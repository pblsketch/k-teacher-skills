---
description: 평가 증거·힌지 질문·루브릭 품질을 함께 높이는 workflow. 오개념 확인 + 채점 기준 정렬.
---

# Assessment quality upgrade

K-Teacher Skills "assessment-quality-upgrade" workflow를 시작한다.

**Chain:** `assessment-first-design` → `hinge-question-designer` → `rubric-quality-guard` → `to-lesson-brief`
**Default profile:** Deep (threshold 0.15, max 12 rounds)

사용자 요청:
```
$ARGUMENTS
```

## 진행 절차

1. **Round 0:** `skills/assessment/assessment-first-design/SKILL.md` 로딩 → Gate v2 banner → topology 잠금(보통 평가체계).
2. **학습 증거 정의:** 학생이 무엇을 하면 배웠다고 볼 것인가? 관찰 가능한 행동·산출물·발화.
3. **최소 평가 장면:** Exit ticket·한 문장 설명·짝 토론 발화 등 가장 작은 평가 단위부터.
4. **힌지 질문:** `hinge-question-designer`로 수업 중 오개념을 빠르게 판별하는 형성평가 문항 + 선택지별 교사 대응 설계.
5. **루브릭 검토:** `rubric-quality-guard`로 평가 준거·수준 기술·배점·학생 친화성·성취기준 정렬 검토.
6. **Brief 정리:** `to-lesson-brief`.

태도·성실성 같은 목표 무관 기준 배제. `references/hinge-question-design.md` + `references/rubric-quality.md` 참조.
