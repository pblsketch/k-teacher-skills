# Workflow: new-lesson-package

새 수업을 준비하거나 활동지/수업안을 바로 만들어 달라는 요청을 받았을 때 사용하는 canonical vertical slice다.
이 workflow는 기존 공개 경로와 체인은 유지한 채, workflow envelope와 lesson-package IR로 이어질 `new-lesson-package` 식별자를 기준으로 수업 설계 산출물을 정리한다.

## Chain

```text
grill-me-for-k-teacher
→ assessment-first-design
→ lesson-prototype
→ to-lesson-brief
```

## Entry signals

- 수업안 만들어줘
- 활동지 만들어줘
- 내일 수업 준비 도와줘
- 이 주제로 수업하고 싶어

## Handoff intent

- router/command surface에서는 canonical workflow id `new-lesson-package`로 선택·호출한다.
- 인터뷰와 설계 결과는 이후 workflow-envelope / lesson-package IR handoff에 맞게 묶일 수 있는 lesson brief, 평가 증거, prototype 결정을 남긴다.
- 이 문서는 체인 자체를 바꾸지 않으며, readiness semantics도 그대로 유지한다.

## Exit artifact

- Lesson Brief
- 평가 증거
- prototype 선택 결과
- 다음 수업자료 생성용 압축 프롬프트