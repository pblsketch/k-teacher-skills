# K-Teacher Prompts v2.2 — Quality Review

**검토자**: ULTRAQA + Critic (oh-my-claudecode)
**대상**: `docs/index.html` (라인 453~783), 17개 한국어 프롬프트
**원본 기준**: `skills/<group>/<skill>/SKILL.md` 17개
**검토일**: 2026-05-27

---

## Summary

- **총평**: 17개 프롬프트는 전반적으로 챗봇 실행 가능한 압축이 잘 되어 있고 핵심 non-negotiables(즉시 자료 금지, 선택지 기반 질문, PII 금지)가 거의 일관되게 반영됨. 외부 `references/*.md` 잔재 0건, Claude Code 도구 코드 0건으로 호환성은 양호. 그러나 (1) `k-teacher-workflow-router`의 라우팅 매핑 누락 (Critical), (2) 첫 질문 객관식 강제 패턴이 7/17만 적용된 비대칭 (Major systemic), (3) `ai-resilient`의 H-AI-H 정의 압축 손실 등 즉시 손볼 가치 있음.
- **평균 점수**: 4.70 / 5 (32.9/35 평균)
- **Critical 이슈**: 1개
- **Major 이슈**: 4개
- **Minor 이슈**: 8개
- **Verdict**: REVISE — Critical 1개 즉시 패치 후 ACCEPT 가능

## Score Matrix (17 × 7)

| Skill | 자기완결 | 첫질문 | 톤 | 선택지 | PII | 길이 | 호환성 | 합 |
|-------|---------|--------|-----|--------|-----|------|--------|-----|
| grill-me-for-k-teacher | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 34 |
| grill-with-curriculum | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 34 |
| k-teacher-workflow-router | 3 | 5 | 5 | 5 | 5 | 4 | 5 | **32** |
| assessment-first-design | 5 | 5 | 5 | 5 | 5 | 4 | 5 | 34 |
| diagnose-lesson-failure | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **35** |
| improve-lesson-architecture | 5 | 3 | 5 | 4 | 5 | 5 | 5 | 32 |
| zoom-out-lesson | 5 | 5 | 5 | 5 | 5 | 4 | 5 | 34 |
| lesson-prototype | 4 | 5 | 5 | 5 | 5 | 5 | 5 | 34 |
| to-lesson-brief | 5 | 3 | 5 | 3 | 5 | 5 | 5 | 31 |
| thinking-routine-selector | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **35** |
| concept-based-inquiry-designer | 5 | 3 | 5 | 4 | 5 | 5 | 5 | 32 |
| pbl-design-coach | 5 | 5 | 5 | 5 | 5 | 4 | 5 | 34 |
| differentiate-lesson-pathways | 5 | 3 | 5 | 4 | 5 | 5 | 5 | 32 |
| rubric-quality-guard | 5 | 3 | 5 | 4 | 5 | 5 | 5 | 32 |
| hinge-question-designer | 4 | 3 | 5 | 4 | 5 | 5 | 5 | 31 |
| udl-barrier-remover | 5 | 3 | 5 | 4 | 5 | 5 | 5 | 32 |
| ai-resilient-assignment-redesign | 4 | 3 | 5 | 4 | 5 | 4 | 5 | 30 |

## Critical Issues

### 1. k-teacher-workflow-router — 워크플로별 시작 스킬 매핑 누락 (즉시 수정)

라우터 압축본이 분류 라벨 11개를 나열하지만 분류 결과 → 시작 스킬 매핑이 사라짐. 사용자가 "사고 루틴 추천해줘"라고 했을 때 챗봇이 분류는 하지만 어느 스킬로 보낼지 모름.

**패치 적용 완료** — 12개 워크플로 매핑 명시.

## Major Issues

### 1. 10개 프롬프트 — 첫 질문 객관식 강제 비대칭 (systemic, v2.3으로 미룸)
강제O 7개 (diagnose / zoom-out / prototype / thinking-routine / pbl / assessment-first / grill-me 부분), 강제X 10개.
다음 PR에서 일괄 처리.

### 2. ai-resilient-assignment-redesign — H→AI→H 정의 손실 (즉시 수정)
"학생 재가공" → "인간 성찰·성장"으로 복원.
**패치 적용 완료**.

### 3. lesson-prototype — "검증 질문 명시" non-negotiable 누락 (즉시 수정)
prototype마다 무엇을 검증하는지 명시 규칙 추가.
**패치 적용 완료**.

### 4. modal-tips 안내문 — 8개 프롬프트와 불일치 (즉시 수정)
"마지막 부분 채우기" 가정이 일부 프롬프트와 안 맞음. 빈칸 유무 모두 커버하도록 문구 수정.
**패치 적용 완료**.

## Minor Issues (v2.3 권고)

1. to-lesson-brief — 첫 동작 모호
2. 17개 입력 라벨 일관성 부족
3. assessment-first-design — 입력 라벨 위치
4. ai-resilient — SHIFT 약어 풀이 누락
5. zoom-out-lesson — "+ 점검할 내용 한 줄" 모호
6. concept-based-inquiry — "거시/미시" 모호
7. udl-barrier-remover — "디지털 없는 대안" 보너스로 보임
8. PII 가드 길이 차이

## What's Missing (Gap Analysis)

- readiness gate 개념 — 17개 압축본 모두 누락 (모든 SKILL.md에 있음)
- UDL 3축 점검 — 12개에서 누락
- Red flags 섹션 — 압축본 0개
- rubric — 성취기준 정렬 점검 약화
- router — "선택 이유 설명" 누락

## Recommendations

1. **v2.2 (이번 PR, 즉시)**: Critical 1 + Major 2,3,4 패치 (4건 적용 완료)
2. **v2.3 (다음 PR)**: 10개 프롬프트에 객관식 첫 질문 패턴 일괄 적용
3. **v2.3**: 입력 라벨 / PII 가드 / readiness gate 압축 표준화
4. **v2.4**: `docs/prompt-compression-style.md` 작성 — 7개 차원 압축 규약
5. **검증 인프라**: GitHub Pages에 1-클릭 피드백 추가 (어디서 챗봇 응답 이탈하는지 측정)

## Verdict

**ACCEPT after Critical+Major 2,3,4 patches applied. Major 1 (systemic) → v2.3 deferred.**
