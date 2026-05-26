---
name: k-teacher-workflow-router
description: 교사의 수업 준비, 평가 설계, 자료 개선, 수업 실패 진단 요청을 분석해 적절한 K-Teacher Skills workflow를 선택하고 첫 스킬로 연결한다. 사용자가 명시적으로 스킬 이름을 부르지 않아도 교사 맥락의 요청이면 사용한다.
---

# K-Teacher Workflow Router

교사 요청을 단일 스킬이 아니라 **워크플로우**로 라우팅한다.

이 스킬은 수업자료를 만들지 않는다. 먼저 요청의 성격을 분석하고, 적절한 workflow를 선택한 뒤 첫 번째 스킬로 연결한다.

## Non-negotiables

- 교사 요청을 받으면 바로 자료를 만들지 않는다.
- 먼저 요청이 어느 workflow에 속하는지 판단한다.
- 애매하면 선택지를 제공한다.
- 질문할 때는 `../../references/questioning-style.md`의 선택지 기반 질문 규칙을 따른다.
- workflow를 바로 실행할지, 첫 질문을 던질지, 다음 스킬로 넘길지는 `../../references/interview-readiness.md`의 readiness gate로 판단한다.
- 학생 개인정보를 요구하지 않는다.
- 외부 서비스 연동을 제안하지 않는다.
- workflow 선택 시 학생의 참여/표상/표현 장벽을 낮출 수 있는 흐름인지 확인한다.
- workflow를 선택한 이유를 짧게 설명한다.

## Available workflows

### 1. New lesson design

사용자가 새 수업을 준비하려고 할 때.

```text
grill-me-for-k-teacher
→ assessment-first-design
→ lesson-prototype
→ to-lesson-brief
```

### 2. Curriculum-grounded redesign

성취기준, 교육과정, 기존 자료를 기준으로 수업을 점검하거나 재설계할 때.

```text
grill-with-curriculum
→ zoom-out-lesson
→ assessment-first-design
→ improve-lesson-architecture
→ to-lesson-brief
```

### 3. Lesson failure recovery

수업이 잘 안 되었고 다음 차시 수정을 원할 때.

```text
diagnose-lesson-failure
→ zoom-out-lesson
→ lesson-prototype
→ to-lesson-brief
```

### 4. Material architecture improvement

기존 PPT, 활동지, 퀴즈, 루브릭이 흩어져 있고 구조 개선이 필요할 때.

```text
improve-lesson-architecture
→ assessment-first-design
→ lesson-prototype
→ to-lesson-brief
```

## Routing logic

### If the user asks for a lesson plan/material immediately

Example:

```text
내일 수업 활동지 만들어줘.
```

Route:

```text
New lesson design
```

Start:

```text
grill-me-for-k-teacher
```

### If the user mentions standards/curriculum/existing materials

Example:

```text
이 활동이 성취기준이랑 맞는지 봐줘.
```

Route:

```text
Curriculum-grounded redesign
```

Start:

```text
grill-with-curriculum
```

### If the user says a lesson failed

Example:

```text
오늘 수업이 망했어. 다음 차시 어떻게 바꾸지?
```

Route:

```text
Lesson failure recovery
```

Start:

```text
diagnose-lesson-failure
```

### If the user has too many disconnected materials

Example:

```text
PPT, 활동지, 퀴즈가 많은데 흐름이 산만해.
```

Route:

```text
Material architecture improvement
```

Start:

```text
improve-lesson-architecture
```

## Ambiguous request handling

애매하면 선택지를 준다.

```text
요청을 보니 네 가지 방향이 가능합니다.

A. 새 수업을 처음부터 설계한다
B. 성취기준/교육과정 기준으로 기존 수업을 점검한다
C. 실패한 수업을 진단하고 다음 차시를 수정한다
D. 흩어진 자료를 하나의 수업 모듈로 재구조화한다
E. 기타: 직접 적기

추천은 A입니다. 지금 요청은 "자료 만들기"보다 수업 의도와 평가 증거를 먼저 정해야 하는 상황으로 보입니다.
```

## Output format

1. 요청 유형
2. 선택한 workflow
3. 선택 이유
4. 시작할 skill
5. 다음 skill 후보
6. 참여/표상/표현 장벽에 대한 주의점
7. 교사에게 던질 첫 질문
8. readiness 상태 또는 막힌 gate

## Review checklist

- 단일 스킬이 아니라 workflow를 선택했는가?
- 선택 이유가 교사에게 이해 가능한가?
- 질문이 선택지 기반인가?
- 참여/표상/표현 장벽을 낮추는 workflow인지 확인했는가?
- 개인정보를 요구하지 않았는가?
- 바로 자료 생성으로 뛰어들지 않았는가?
- readiness gate를 고려했는가?

## Related recipes

- `../../workflows/new-lesson-design.md`
- `../../workflows/curriculum-grounded-redesign.md`
- `../../workflows/lesson-failure-recovery.md`
- `../../workflows/material-architecture-improvement.md`
- `../../references/interview-readiness.md`

## Red flags

- 요청을 보자마자 활동지를 만든다.
- workflow를 고르지 않고 아무 스킬이나 시작한다.
- 애매한 요청에 자유서술 질문만 던진다.
- 교사에게 왜 그 스킬을 쓰는지 설명하지 않는다.
