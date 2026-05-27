---
name: zoom-out-lesson
description: 교사가 활동, 자료, 발문, 평가 일부에 매몰됐을 때 단원·차시·성취기준·학기 흐름의 상위 맥락으로 올려 수업의 위치와 목적을 다시 정렬한다. 사용자가 "이 활동 괜찮아?", "수업 흐름이 맞나?", "단원에서 어디에 놓이지?", "수업을 큰 그림에서 봐줘", "zoom out"을 말할 때 사용한다.
---

# Zoom Out Lesson

부분을 고치기 전에 상위 맥락을 본다.

이 스킬은 활동 하나, 활동지 하나, 발문 하나를 바로 개선하지 않는다. 먼저 그것이 단원·차시·성취기준·평가 흐름에서 어떤 역할인지 확인한다.

## Non-negotiables

- 새 활동이나 자료를 바로 만들지 않는다.
- 먼저 현재 사용자가 보고 있는 층위를 확인한다.
- 활동의 재미보다 수업 전체에서의 기능을 묻는다.
- 학생 개인정보를 요구하지 않는다.
- 참여/표상/표현 장벽을 확인한다.
- 상위 맥락 없이 "좋다/나쁘다"를 단정하지 않는다.
- 질문할 때는 가능한 한 3~5개의 선택지와 `기타: 직접 적기`를 제공한다.
- 질문을 더 할지, 한 단계 위 맥락 판단으로 넘어갈지는 `../../../references/interview-readiness.md`의 readiness gate로 판단한다.

## Readiness gate v2 (v2.5.1+)
- Default profile: Quick
- Active stage: Stage 1 · Intent-first
- Fact routing in this skill: from-teacher-judgment
- Tier 3 (Topology/Ontology/Challenge): disabled-for-quick-profile
- Full spec: `../../../references/interview-readiness.md`
- Canonical mapping: `../../../tests/readiness_gate_v2_mapping.json`

## Workflow

### 1. Identify the current layer

사용자가 지금 보고 있는 것이 무엇인지 확인한다.

```text
지금 점검하려는 것은 어느 층위인가요?

A. 활동 하나
B. 발문 하나
C. 활동지/자료 하나
D. 차시 전체
E. 단원 전체
F. 평가 흐름
```

### 2. Move one layer up

현재 층위보다 한 단계 위를 묻는다.

- 활동 → 차시 목표
- 발문 → 학생 사고 흐름
- 활동지 → 평가 증거
- 차시 → 단원 핵심 질문
- 단원 → 학기/교육과정 흐름
- 평가 → 학습 증거와 피드백 루프

### 3. Map the lesson position

다음 세 가지를 정리한다.

1. 이 활동/자료는 무엇을 준비시키는가?
2. 이 활동/자료는 무엇을 드러내는가?
3. 이 활동/자료 다음에 무엇이 가능해지는가?

### 4. Detect local optimization

다음 신호가 있으면 경고한다.

- 활동은 재미있지만 목표와 약하다.
- 자료는 예쁘지만 평가 증거가 없다.
- 발문은 많지만 학생 사고가 깊어지지 않는다.
- 평가 문항은 있지만 다음 피드백으로 이어지지 않는다.
- 교과서 순서를 따르지만 학급 맥락과 연결되지 않는다.

### 5. Return with options

큰 그림을 본 뒤 선택지를 제시한다.

```text
이 활동은 단원 핵심 질문과 약하게 연결됩니다.
선택지는 세 가지입니다.

A. 활동을 유지하되 마지막 질문을 평가 증거와 연결한다.
B. 활동을 도입으로 낮추고 핵심 활동을 따로 만든다.
C. 활동을 제거하고 단원 핵심 질문에 직접 연결되는 탐구로 바꾼다.
```

## Output format

1. 현재 층위
2. 한 단계 위 맥락
3. 수업 흐름에서의 역할
4. 끊긴 연결
5. UDL/accessibility 장벽
6. 선택지 2~3개
7. 추천안과 이유
8. 교사가 결정해야 할 지점

## Review checklist

- 활동/자료가 어느 차시·단원에 놓이는지 분명한가?
- 목표, 활동, 평가 증거가 연결되는가?
- 지금 고치려는 부분이 진짜 병목인가?
- 학생 참여/표상/표현 장벽을 낮추는가?
- 개인정보 없이 맥락을 설명했는가?

## Related example

이 스킬의 실제 대화 흐름은 `examples/sample-dialogue.md`를 참고한다.

## Red flags

- 활동 하나만 보고 바로 좋다/나쁘다 말한다.
- 자료를 더 추가하는 것을 개선으로 착각한다.
- 단원 핵심 질문 없이 세부 활동을 고친다.
- 평가 증거 없이 수업 흐름을 판단한다.
- 학생 개인정보를 요구한다.
