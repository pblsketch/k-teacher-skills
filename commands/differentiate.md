---
description: 학생 편차·참여 장벽·기초/심화 경로가 필요할 때 같은 목표를 유지하면서 경로를 다르게 설계하는 workflow.
---

# Differentiated lesson redesign

K-Teacher Skills "differentiated-lesson-redesign" workflow를 시작한다.

**Chain:** `diagnose-lesson-failure` → `udl-barrier-remover` → `differentiate-lesson-pathways` → `lesson-prototype` → `to-lesson-brief`
**Default profile:** Standard (threshold 0.20, max 8 rounds)

사용자 요청:
```
$ARGUMENTS
```

## 진행 절차

1. **Round 0:** `skills/diagnostics/diagnose-lesson-failure/SKILL.md` 로딩 → Gate v2 banner → topology 잠금.
2. **관찰 증거:** 학생 편차·막힘 지점을 관찰 가능한 증거로 진단(`[from-class-context]`로 익명화).
3. **장벽 분류:** `udl-barrier-remover`로 참여(Engagement)·표상(Representation)·행동과 표현(Action/Expression) 장벽 진단.
4. **경로 설계:** `differentiate-lesson-pathways`로 기초·표준·심화 경로 + 선택형 과제 + 소그룹 지원 설계. 같은 핵심 평가 증거 유지.
5. **Prototype + Brief:** `lesson-prototype` → `to-lesson-brief`.

학생을 고정 수준으로 낙인찍기 금지. KSL/다국어 학습자 지원 옵션 검토. `references/differentiation-patterns.md` + `references/udl-barrier-check.md` 참조.
