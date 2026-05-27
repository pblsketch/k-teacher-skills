---
description: 성취기준·교육과정·기존 자료(활동지·PPT·평가계획)를 기준으로 수업을 재설계하는 workflow.
---

# Curriculum-grounded redesign

K-Teacher Skills "curriculum-grounded-redesign" workflow를 시작한다.

**Chain:** `grill-with-curriculum` → `zoom-out-lesson` → `assessment-first-design` → `improve-lesson-architecture` → `to-lesson-brief`
**Default profile:** Deep (threshold 0.15, max 12 rounds)

사용자 요청:
```
$ARGUMENTS
```

## 진행 절차

1. **Round 0:** `skills/entry/grill-with-curriculum/SKILL.md` 로딩 → Gate v2 banner → topology 잠금.
2. **자료 점검:** 사용자가 제공한 성취기준·교과서·활동지를 `[from-curriculum:provided]` / `[from-textbook:provided]`로 인용. 미제공 시 `:inferred`로 출발 + 확인 요청.
3. **정렬 검토:** 성취기준 핵심 동사 ↔ 활동 ↔ 평가 증거의 어긋남 지적.
4. **Zoom-out:** 활동 단위에서 단원·차시·성취기준 흐름으로 확대.
5. **평가 증거 설계:** `assessment-first-design`으로 학습 증거 재정의.
6. **구조 개선:** `improve-lesson-architecture`로 자료 재배치(deletion test + 후보 리포트).
7. **Brief 정리:** `to-lesson-brief`.

`CURRICULUM-CONTEXT.md` / `LESSON-ADR.md` 후보 기록은 `grill-with-curriculum` SKILL.md 규칙 따름.
