# K-Teacher Skills Workflows

이 문서는 K-Teacher Skills를 개별 스킬 묶음이 아니라 **workflow pack**으로 사용하기 위한 연결 규칙이다.

기본 진입점은 `k-teacher-workflow-router`다.

```text
k-teacher-workflow-router로 내 요청을 분석하고 적절한 K-Teacher Skills workflow를 시작해줘.
```

## Router-first rule

사용자가 스킬 이름을 모르면 router를 먼저 사용한다.

Router는 다음을 판단한다.

1. 요청 유형
2. 선택한 workflow
3. 선택 이유
4. 시작할 skill
5. 다음 skill 후보
6. 참여/표상/표현 장벽에 대한 주의점
7. 교사에게 던질 첫 질문
8. readiness 상태 또는 막힌 gate

## Workflow index

### 1. `new-lesson-package`
`skill-pack.json` canonical workflow id · path: `new-lesson-package` → `workflows/new-lesson-design.md`

```text
grill-me-for-k-teacher
→ assessment-first-design
→ lesson-prototype
→ to-lesson-brief
```

Use when:

- 새 수업안, 활동지, 평가지를 만들고 싶다.
- 목표, 학생 맥락, 평가 증거가 아직 흐릿하다.

### 2. Curriculum-grounded redesign

```text
grill-with-curriculum
→ zoom-out-lesson
→ assessment-first-design
→ improve-lesson-architecture
→ to-lesson-brief
```

Use when:

- 성취기준, 기존 자료, 평가계획을 기준으로 재설계한다.
- 교과서 흐름을 그대로 쓰지 않고 새 학급 맥락에 맞추고 싶다.

### 3. Lesson failure recovery

```text
diagnose-lesson-failure
→ zoom-out-lesson
→ lesson-prototype
→ to-lesson-brief
```

Use when:

- 수업이 기대대로 되지 않았다.
- 다음 차시 수정을 관찰 증거 기반으로 설계하고 싶다.

### 4. Material architecture improvement

```text
improve-lesson-architecture
→ assessment-first-design
→ lesson-prototype
→ to-lesson-brief
```

Use when:

- PPT, 활동지, 퀴즈, 루브릭이 흩어져 있다.
- 자료는 많지만 핵심 질문과 평가 증거가 약하다.

### 5. AI-resilient assignment redesign

```text
ai-resilient-assignment-redesign
→ assessment-first-design
→ to-lesson-brief
```

Use when:

- ChatGPT 복붙이 걱정된다.
- AI 대응 과제와 프롬프트 로그, SHIFT 성찰지가 필요하다.

### 6. Conceptual inquiry lesson

```text
grill-with-curriculum
→ concept-based-inquiry-designer
→ thinking-routine-selector
→ assessment-first-design
→ to-lesson-brief
```

Use when:

- 단원을 핵심 개념, 일반화, 탐구 질문 중심으로 바꾸고 싶다.
- 학생 사고를 보이게 하는 루틴과 평가 증거를 연결하고 싶다.

### 7. Differentiated lesson redesign

```text
diagnose-lesson-failure
→ udl-barrier-remover
→ differentiate-lesson-pathways
→ lesson-prototype
→ to-lesson-brief
```

Use when:

- 학생 편차, 참여 장벽, 기초학력 지원이 중요하다.
- 같은 목표를 유지하면서 경로를 다르게 설계하고 싶다.

### 8. Assessment quality upgrade

```text
assessment-first-design
→ hinge-question-designer
→ rubric-quality-guard
→ to-lesson-brief
```

Use when:

- 평가 증거, 형성평가, 루브릭 품질을 함께 높이고 싶다.
- 오개념을 수업 중 확인할 힌지 질문이 필요하다.

### 9. PBL design

```text
zoom-out-lesson
→ pbl-design-coach
→ assessment-first-design
→ rubric-quality-guard
→ to-lesson-brief
```

Use when:

- 실생활·지역사회 문제 기반 프로젝트 수업을 설계한다.
- driving question, 학생 역할, 청중, 과정 평가가 필요하다.

### 10. UDL accessible lesson redesign

```text
improve-lesson-architecture
→ udl-barrier-remover
→ lesson-prototype
→ to-lesson-brief
```

Use when:

- 수업 활동은 있지만 일부 학생에게 장벽이 크다.
- 참여·표상·행동과 표현 대안을 추가하고 싶다.

## Stop rule

모든 workflow는 `references/interview-readiness.md`를 따른다.

다음이 비어 있으면 완성 산출물로 넘어가지 않는다.

- 수업 의도
- 학생 맥락
- 평가 증거
- 예상 오개념 또는 학습 장벽
- 핵심 제약
- 교사 판단 필요 지점

## Final handoff

긴 workflow의 마지막은 기본적으로 `to-lesson-brief`다.

이 스킬은 다음을 정리한다.

- 확정된 설계
- 추정
- 미확정
- 다음 AI 작업에 넘길 정보
- 교사 최종 판단 필요 항목
