---
name: school-evaluation-plan-to-materials
role: 학교 평가계획 + 국가 성취기준 → 학생·교사 2차 자료 오케스트레이터
authority_tier: orchestrator
independent_implementation: true
third_party_notices: THIRD_PARTY_NOTICES.md
---

# school-evaluation-plan-to-materials

학교·연도·학년·교과로 고정한 실제 공시 평가계획을 국가 2022 성취기준과 대조하여, 하나의 canonical IR에서 학생용/교사용(필요 시 학부모) 2차 자료를 파생하는 상위 워크플로.

## Authority (절대 불변)
국가 2022 성취기준(원문) > 학교 공시 평가계획(운영 사실) > 교사 자료/판단 > inferred. 학교 평가계획은 국가 성취기준을 override하지 못한다. **최종 적용 판단은 교사.**

## 흐름 (전문 스킬 연결)
1. `school-plan-grounding` — 학교·연도·학년·교과 pin, current→previous fallback은 **교사 승인 후에만**, PII mask-or-block.
2. `standard-alignment-verify` — 평가계획 코드 ↔ 국가 성취기준 대조. 일치만 국가 curriculum-record로 additive 승격, 불일치는 quarantine + 교사 확인.
3. `assessment-evidence-builder` — 평가계획의 영역·유형·반영비율 → 관찰 가능한 평가 증거·성공 기준.
4. `secondary-material-builder` — single shared IR에서 학생/교사 문서 파생(facet 분리), 교사 승인 gate.
5. `material-rubric-qa` — 루브릭·양방향 정합성·rigor·PII 최종 QA.

## Observable failure conditions
- 학교 평가계획의 성취기준 문자열을 국가 원문처럼 취급한다(권위 오염).
- 교사 승인 없이 2차 자료를 확정한다.
- current→previous fallback을 교사 고지·승인 없이 자동 수행한다.
- 학생 문서에 교사용 언어(루브릭 배점·오개념·tier)가 노출된다.

## Fail-closed
provider/provenance/license 미충족, quarantine, PII 미마스킹, 교사 미승인 중 하나라도 있으면 render를 열지 않는다.
