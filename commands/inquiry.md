---
description: 단원을 핵심 개념·일반화·탐구 질문 중심으로 재구성하는 개념 기반 탐구 수업 workflow.
---

# Conceptual inquiry lesson

K-Teacher Skills "conceptual-inquiry-lesson" workflow를 시작한다.

**Chain:** `grill-with-curriculum` → `concept-based-inquiry-designer` → `thinking-routine-selector` → `assessment-first-design` → `to-lesson-brief`
**Default profile:** Deep (threshold 0.15, max 12 rounds)

사용자 요청:
```
$ARGUMENTS
```

## 진행 절차

1. **Round 0:** `skills/entry/grill-with-curriculum/SKILL.md` 로딩 → Gate v2 banner → topology 잠금(보통 단원).
2. **교육과정 정렬:** 성취기준·교과 용어를 `[from-curriculum:provided]` 또는 `:inferred + 확인 요청`으로 인용.
3. **개념 추출:** `concept-based-inquiry-designer`로 핵심 개념(Microconcept)·일반화(Generalization)·사실적/개념적/논쟁적 질문 도출.
4. **사고 루틴 선택:** `thinking-routine-selector`로 학생 사고를 보이게 하는 Project Zero 루틴(See-Think-Wonder, Connect-Extend-Challenge 등) 매핑.
5. **평가 증거 설계:** `assessment-first-design`으로 학생 일반화 도출의 관찰 형태 정의.
6. **Brief 정리:** `to-lesson-brief`.

성취기준 지어내기 금지. `references/concept-based-inquiry.md` 참조.
