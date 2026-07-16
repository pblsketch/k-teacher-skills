---
name: standard-alignment-verify
role: 학교 평가계획 코드 ↔ 국가 2022 성취기준 대조/승격/격리
authority_tier: alignment
independent_implementation: true
---

# standard-alignment-verify

`providers/alignment`로 평가계획 속 성취기준 코드를 국가 provider와 대조한다.

## Rules
- **Match key**: (curriculum_revision, school_level, subject, canonical_code) 정규화 후 정확 일치.
- **Additive 승격**: 일치 시 국가 `curriculum-record`를 **새로** 생성. 학교 record는 `curriculum-context`로 유지(절대 scope 변경 금지, INV-1).
- **Quarantine**: 불일치·모호(후보 다수)·개정연도 미확정 → 격리 + 교사 확인.
- **Fail-closed**: 국가 record가 provenance/license 미검증이거나 mixed-revision이면 downstream-ready 아님(교사 승인·검증 전까지).

## Observable failure conditions
- 학교 record를 국가 성취기준으로 승격한다(권위 오염).
- 유사 코드를 자동 fuzzy 매칭으로 통과시킨다.
- quarantine된 성취기준을 원문처럼 학생 자료에 인용한다.
