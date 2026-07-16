---
description: 새 수업 패키지 workflow — canonical id `new-lesson-package`; 목표·학생 맥락·평가 증거가 흐릿한 상태에서 1차시 또는 단원을 처음 만들 때.
---

# New lesson package

K-Teacher Skills canonical workflow id `new-lesson-package`를 시작한다.

**Chain:** `grill-me-for-k-teacher` → `assessment-first-design` → `lesson-prototype` → `to-lesson-brief`
**Default profile:** Standard (threshold 0.20, max 8 rounds)

사용자 요청:
```
$ARGUMENTS
```

## 진행 절차

1. **Round 0:** `skills/entry/grill-me-for-k-teacher/SKILL.md` 로딩 → Readiness Gate v2 banner 첫 줄 출력 → Round 0 topology 잠금(1차시 / 단원 / 평가체계 / 학기 / 다중).
2. **Stage 1 인터뷰:** Intent · Learner context · Non-goals · Decision boundaries부터 시작. weakest dimension부터 1라운드 1질문.
3. **Crystallize:** §6 closure audit 통과 시 `assessment-first-design`으로 인계.
4. **평가 증거 설계:** 활동보다 학습 증거·루브릭을 먼저 정의.
5. **Prototype 비교:** `lesson-prototype`으로 2~3개 활동·발문 후보 비교.
6. **Brief 정리:** `to-lesson-brief`로 동료 공유·다음 AI 작업용 정리.

매 라운드 §12 output template 형식 사용. fact-routing 라벨(`[from-curriculum:provided|inferred|web]` 등) 명시. `:inferred` 사실은 hallucination guard 3요소(추정·신뢰도·확인 요청) 포함.
