---
name: to-lesson-brief
description: 지금까지의 대화, 수업 아이디어, 성취기준, 학생 맥락, 평가 기준을 새 질문 없이 수업 설계 브리프로 정리한다. 사용자가 "정리해줘", "브리프로 만들어줘", "동료에게 공유", "다음 AI 작업에 넘기기", "수업 설계안 요약"을 원할 때 사용한다.
---

# To Lesson Brief

대화 내용을 수업 설계 브리프로 정리한다.

이 스킬은 새로 인터뷰하지 않는다. 이미 나온 맥락을 종합하고, 모르는 것은 추정하지 않고 `미확정`으로 표시한다.

## Non-negotiables

- 새 질문을 먼저 던지지 않는다.
- 대화에 없는 정보를 지어내지 않는다.
- 학생 개인정보를 포함하지 않는다.
- AI가 추정한 부분과 교사가 확인해야 할 부분을 분리한다.
- 활동보다 목표·학생 맥락·평가 증거가 먼저 보이게 정리한다.
- 참여/표상/표현 장벽 검토 항목을 포함한다.
- 다음 질문이 필요하다고 판단될 때는 가능한 한 3~5개의 선택지와 `기타: 직접 적기`를 제공한다.
- 새 질문이 필요한지 판단할 때는 `../../../references/interview-readiness.md`의 readiness gate를 사용한다.

## Readiness gate v2 (v2.5.1+)
- Default profile: Quick
- Active stage: Stage 1 · Intent-first (output-only)
- Fact routing in this skill: from-curriculum, from-textbook, from-class-context, from-teacher-judgment
- Tier 3 (Topology/Ontology/Challenge): disabled-for-quick-profile
- Full spec: `../../../references/interview-readiness.md`
- Canonical mapping: `../../../tests/readiness_gate_v2_mapping.json`

## Use when

- `grill-me-for-k-teacher` 이후 정리가 필요하다.
- `assessment-first-design` 이후 수업안으로 넘기기 전 브리프가 필요하다.
- 교사 연구회나 동료 교사에게 수업 아이디어를 공유해야 한다.
- 다음 AI 작업에 맥락을 넘겨야 한다.
- 긴 대화를 한 페이지 설계 문서로 압축해야 한다.

## Workflow

### 1. Extract known context

대화에서 확인된 것만 뽑는다.

- 학교급/학년/과목/단원
- 수업 의도
- 성취기준 또는 핵심 개념
- 학생 맥락
- 예상 오개념
- 학습 증거
- 평가 기준
- 활동 방향
- 제약 조건

### 2. Mark unknowns

모르는 것은 `미확정`으로 표시한다.

나쁜 예:

```text
학생들은 기본 개념을 알고 있다.
```

좋은 예:

```text
선행 지식: 미확정. 다음 설계 전에 확인 필요.
```

### 3. Separate teacher decisions

교사가 판단해야 할 항목을 따로 둔다.

- 목표 우선순위
- 평가 방식
- 난이도 조정
- 활동 시간
- 민감한 주제 처리
- 보충/심화 제공 방식

### 4. Produce the brief

브리프는 다음 구조를 따른다.

```text
Lesson Brief

1. 수업 의도
2. 학생 맥락
3. 성취기준/핵심 개념
4. 학습 증거
5. 평가 기준
6. 예상 오개념
7. 수업 흐름
8. UDL/accessibility 검토
9. 미확정 사항
10. 다음 AI 작업에 넘길 프롬프트
```

## Output format

1. 한 문장 요약
2. 수업 설계 브리프
3. 미확정/추정/확정 분리
4. 교사 판단 필요 항목
5. 다음 작업 추천
6. 다음 AI에게 넘길 압축 프롬프트

## Review checklist

- 대화에 없는 정보를 지어내지 않았는가?
- 학생 개인정보가 제거되었는가?
- 목표, 학생 맥락, 평가 증거가 먼저 보이는가?
- 참여/표상/표현 장벽 검토가 들어갔는가?
- 다음 AI 작업자가 바로 이어받을 수 있는가?

## Related example

이 스킬의 실제 대화 흐름은 `examples/sample-dialogue.md`를 참고한다.

## Red flags

- 미확정 정보를 확정처럼 쓴다.
- 브리프가 활동 순서만 나열한다.
- 학생 개인정보나 실제 사례를 포함한다.
- 다음 작업에 필요한 결정 사항을 숨긴다.
- 새 인터뷰를 시작해 버린다.
