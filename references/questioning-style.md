# Questioning Style

교사에게 질문할 때는 기본적으로 **선택지를 제공**한다.

질문을 몇 번까지 이어갈지, 언제 산출물로 넘어갈지는 `interview-readiness.md`를 따른다.

## Default rule

질문이 교사의 판단을 요구한다면 다음 형식을 따른다.

```text
질문:

A. 선택지 1
B. 선택지 2
C. 선택지 3
D. 기타: 직접 적기

추천은 B입니다. 이유는 ...
```

## Why

- 교사의 응답 부담을 줄인다.
- AI가 어떤 판단 축을 보고 있는지 드러낸다.
- 막연한 자유서술보다 빠르게 수업 설계 결정을 좁힌다.
- "딸깍 생성"이 아니라 교사 판단을 구조화한다.

## When to use choices

선택지를 제공한다.

- 수업 목표를 정할 때
- 평가 증거를 정할 때
- 활동 방향을 고를 때
- 진단 가설을 좁힐 때
- workflow를 선택할 때
- 다음 스킬로 넘어갈지 결정할 때

## When not to force choices

선택지를 강제하지 않는다.

- 사용자가 이미 명확히 답했다.
- 교사의 고유한 맥락 서술이 더 중요하다.
- 감정적 성찰이나 수업 실패 경험을 먼저 들어야 한다.
- 제공된 문서에서 답을 찾을 수 있다.

## Option quality

좋은 선택지는 다음 조건을 만족한다.

- 3~5개를 기본으로 한다.
- 서로 구분되는 판단 축을 가진다.
- "기타: 직접 적기"를 포함한다.
- 가능하면 추천 선택지를 제시한다.
- 추천은 확정이 아니라 교사의 검토 대상임을 밝힌다.

## Pressure Ladder reference (v2.5.1+)

선택지 기반 질문이 표면을 다룬다면, 답변에 *압박*을 거는 방식은 `interview-readiness.md` §5 Pressure Ladder를 따른다.

4단계 라더 (본 문서는 명칭만 인용):
1. Evidence/example/counterexample 요구
2. Hidden assumption probe
3. Boundary/tradeoff force
4. Symptom → essence reframe

규칙: 답변이 흐릿하면 차원을 *회전*하지 말고 같은 thread에서 한 단계 더 깊게. 자세한 운영 규칙은 `interview-readiness.md` §5 참조.

## Fact routing in questions (v2.5.1+)

선택지 기반 질문은 **`[from-teacher-judgment]` 라벨에만 사용**한다.

- `[from-curriculum]`·`[from-textbook]` 같은 사실 항목은 AI가 *진술* 형태로 제공해야 한다 — 질문화하면 교사를 불필요하게 검색·확인 노동에 끌어들인다.
- `[from-class-context]`는 교사가 명시한 학급 맥락이므로 질문 대상이지만, 보통 한 번 묻고 transcript에 저장된 뒤 재인용한다.
- 평가 가치판단·비목표·트레이드오프처럼 *인간의 판단*이 필요한 항목만 선택지로 좁힌다.

라벨 정의와 dialectic rhythm은 `interview-readiness.md` §7 참조.

### Provenance grading (v2.5.2+)

사실 라벨은 출처에 따라 3개 등급 중 하나를 suffix로 부착한다 — `:provided` / `:web` / `:inferred`. 자세한 정의·hallucination guard·escalation rule은 `interview-readiness.md` §7 참조.

**질문 형식에서의 함의:**
- `:provided`·`:web` 사실은 AI가 진술 형태로 제공하고 *확인 질문*만 짧게 따라붙인다 ("이 해석이 맞나요?").
- `:inferred` 사실은 *반드시* 추정·신뢰도·확인 요청을 한 묶음 prompt로 제시한다. 선택지 형식 사용 금지 (사용자가 객관식에서 추정안을 무비판적으로 택할 위험).

## Red flags

- 질문 10개를 한 번에 던진다.
- 선택지가 모두 비슷하다.
- 추천 없이 막연히 고르라고 한다.
- 선택지가 교사의 수업 철학을 강제로 제한한다.
- 교사가 자유서술해야 할 맥락을 억지로 객관식화한다.
- 성취기준·교과서 사실(`[from-curriculum]`/`[from-textbook]`)을 객관식 질문으로 만든다.
