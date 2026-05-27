---
description: 수업이 기대대로 안 됐을 때 관찰 증거 기반으로 진단하고 다음 차시 수정안을 만드는 workflow.
---

# Lesson failure recovery

K-Teacher Skills "lesson-failure-recovery" workflow를 시작한다.

**Chain:** `diagnose-lesson-failure` → `zoom-out-lesson` → `lesson-prototype` → `to-lesson-brief`
**Default profile:** Standard (threshold 0.20, max 8 rounds)

사용자 요청:
```
$ARGUMENTS
```

## 진행 절차

1. **Round 0:** `skills/diagnostics/diagnose-lesson-failure/SKILL.md` 로딩 → Gate v2 banner → topology 잠금.
2. **증거 수집:** 관찰 가능한 증거(학생 발화·산출물·평가 결과·시간 흐름)부터 묻는다. 학생 탓·교사 탓 단정 금지.
3. **가설 형식:** "만약 [원인]이 문제라면, [작은 수정]을 했을 때, [관찰 가능한 변화]가 나타날 것이다" — falsifiable hypothesis 형식 강제.
4. **상위 맥락 확인:** `zoom-out-lesson`으로 단원·평가 흐름과의 정합성 점검.
5. **수정 prototype:** `lesson-prototype`으로 다음 차시 작은 수정안 2~3개 비교.
6. **Brief 정리:** `to-lesson-brief` + 수정 효과 확인 방법 명시.

수정은 작은 단위 (도입 발문 하나, 예시 한 개, 활동 지시문 분할 등). 전체 갈아엎기 금지.
