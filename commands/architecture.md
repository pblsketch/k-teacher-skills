---
description: PPT·활동지·퀴즈·루브릭이 흩어져 있어 수업 흐름이 산만할 때 자료를 하나의 깊은 수업 모듈로 재구조화하는 workflow.
---

# Material architecture improvement

K-Teacher Skills "material-architecture-improvement" workflow를 시작한다.

**Chain:** `improve-lesson-architecture` → `assessment-first-design` → `lesson-prototype` → `to-lesson-brief`
**Default profile:** Standard (threshold 0.20, max 8 rounds)

사용자 요청:
```
$ARGUMENTS
```

## 진행 절차

1. **Round 0:** `skills/lesson-design/improve-lesson-architecture/SKILL.md` 로딩 → Gate v2 banner → topology 잠금(보통 단원 또는 다중).
2. **자료 inventory:** 설명·활동·평가·피드백·보충·심화 자료를 분류.
3. **Public interface 정의:** 핵심 질문 · 학습 증거 · 성공 기준 3가지 잠금.
4. **Deletion test:** 자료를 지웠을 때 복잡성이 사라지는지, 다른 자료로 흩어지는지 판단(Delete / Merge / Deepen / Keep).
5. **후보 리포트:** Strong / Worth exploring / Speculative 3등급으로 개선 후보 보고.
6. **평가 증거 설계:** `assessment-first-design`으로 학습 증거 재정의.
7. **Prototype + Brief:** `lesson-prototype` → `to-lesson-brief`.

자료 수를 늘리는 것을 개선으로 착각 금지. 구조의 깊이가 목표.
