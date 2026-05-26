# Expected Behaviors

이 문서는 `K-Teacher AI Skills`가 최소한 지켜야 할 행동 기준입니다.

## Global checks

모든 스킬은 다음을 지켜야 합니다.

- `SKILL.md`가 존재한다.
- YAML frontmatter에 `name`과 `description`이 있다.
- 학생 실명, 민감정보, 실제 학생 사례를 요구하지 않는다.
- 자료를 바로 생성하지 않고 먼저 질문/검증/설계 루프를 수행한다.
- 교사의 최종 판단 지점을 남긴다.
- UDL 또는 접근성 관점에서 참여/표상/표현 장벽을 검토한다.

## Skill-specific checks

### `grill-me-for-k-teacher`

Prompt:

```text
중2 국어 주장하는 글쓰기 활동지 만들어줘.
```

Expected:

- 바로 활동지를 만들지 않는다.
- 수업 의도, 학생 맥락, 평가 증거 중 하나를 먼저 질문한다.
- 가능하면 객관식 선택지를 제공한다.

### `grill-with-curriculum`

Prompt:

```text
성취기준은 "자료를 해석하여 사회 현상의 특징을 설명한다"야. 기존 활동지는 빈칸 채우기야.
```

Expected:

- 성취기준의 핵심 동사를 분석한다.
- 기존 활동과 성취기준의 어긋남을 지적한다.
- `CURRICULUM-CONTEXT.md` 또는 `LESSON-ADR.md` 기록 후보를 제안할 수 있다.

### `assessment-first-design`

Prompt:

```text
초5 과학 생태계 활동지를 만들어줘.
```

Expected:

- 활동지보다 학습 증거를 먼저 묻는다.
- 성공 기준과 최소 평가 장면을 먼저 설계한다.

### `diagnose-lesson-failure`

Prompt:

```text
오늘 비율 수업이 망했어. 애들이 하나도 못 따라왔어.
```

Expected:

- 학생 탓으로 단정하지 않는다.
- 관찰 가능한 증거를 먼저 묻는다.
- 가설을 "만약-수정-관찰" 형식으로 쓴다.

### `improve-lesson-architecture`

Prompt:

```text
PPT, 활동지, 퀴즈가 흩어져서 수업 흐름이 산만해.
```

Expected:

- 새 자료를 바로 만들지 않는다.
- 핵심 질문, 학습 증거, 성공 기준을 먼저 찾는다.
- 삭제 테스트와 후보 리포트를 사용한다.

### `zoom-out-lesson`

Prompt:

```text
이 카드뉴스 활동 괜찮을까?
```

Expected:

- 활동 자체를 바로 평가하지 않는다.
- 활동보다 한 단계 위 맥락을 묻는다.
- 목표, 단원 흐름, 평가 증거와의 연결을 확인한다.

### `lesson-prototype`

Prompt:

```text
도입 활동을 몇 가지 안으로 비교해줘.
```

Expected:

- 완성 수업안을 바로 만들지 않는다.
- 2~3개 prototype을 만든다.
- 각 prototype의 검증 질문, 장점, 위험을 비교한다.

### `to-lesson-brief`

Prompt:

```text
지금까지 이야기한 걸 수업 브리프로 정리해줘.
```

Expected:

- 새 인터뷰를 시작하지 않는다.
- 대화에 없는 정보는 `미확정`으로 표시한다.
- 확정/추정/교사 판단 필요 항목을 분리한다.

### `k-teacher-workflow-router`

Prompt:

```text
내일 수업 활동지 좀 만들어줘.
```

Expected:

- 활동지를 바로 만들지 않는다.
- 요청 유형을 분석한다.
- 적절한 workflow를 선택한다.
- 시작할 skill과 다음 skill 후보를 제시한다.
- 교사에게 질문할 때 선택지를 제공한다.
