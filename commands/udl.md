---
description: 수업 자료·활동·평가에 장벽이 있는 학생도 참여하도록 UDL(보편적 학습 설계) 관점으로 재설계하는 workflow.
---

# UDL accessible lesson redesign

K-Teacher Skills "udl-accessible-lesson-redesign" workflow를 시작한다.

**Chain:** `improve-lesson-architecture` → `udl-barrier-remover` → `lesson-prototype` → `to-lesson-brief`
**Default profile:** Standard (threshold 0.20, max 8 rounds)

사용자 요청:
```
$ARGUMENTS
```

## 진행 절차

1. **Round 0:** `skills/lesson-design/improve-lesson-architecture/SKILL.md` 로딩 → Gate v2 banner → topology 잠금.
2. **구조 점검:** 기존 자료의 public interface(핵심 질문·학습 증거·성공 기준) 식별.
3. **장벽 진단:** `udl-barrier-remover`로 참여(Engagement)·표상(Representation)·행동과 표현(Action/Expression) 장벽을 분류. 학생을 문제로 보지 않는다.
4. **대안 설계:** 목표는 유지하고 접근 경로를 다양화. 말하기·쓰기·그림·분류·선택 중 학생이 이해를 표현할 대안 추가.
5. **Prototype + Brief:** `lesson-prototype` → `to-lesson-brief`.

`references/udl-barrier-check.md` 참조.
