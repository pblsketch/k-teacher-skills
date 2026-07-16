---
name: individualized-material-package-builder
role: direct-entry 개별화 수업 자료 패키지 오케스트레이터 — 단일 IR·단일 renderer
authority_tier: materials
direct_entry: true
independent_implementation: true
dependencies:
  - standard-alignment-verify
  - secondary-material-builder
  - material-rubric-qa
core_skill_links:
  - differentiate-lesson-pathways
---

# individualized-material-package-builder

직접 진입(direct-entry) 가능한 **개별화(individualized) 수업 자료 패키지** 오케스트레이터입니다. 하나의 성취기준·공통 수업에서 교사용 `개별화 수업 운영안` 1개와 학생용 `Group A/B/C 활동지` 3개를 **하나의 canonical `lesson-package-ir`** 위에서 조립하고, 기존 renderer로 HWPX/DOCX/HTML 12개를 만듭니다.

> 용어 계약: 사용자 표면에서는 **개별화**라는 표현을 일관되게 사용합니다.

병렬 IR이나 두 번째 renderer를 만들지 않습니다. 네 문서는 모두 기존 IR의 일반 document이며, `providers/materials/individualized.py`가 `SharedRegistry`와 worksheet 블록 어휘를 재사용해 조립합니다. `renderers.render_package()`가 네 문서를 각각 3형식으로 렌더링합니다.

## 산출
- `teacher-individualized-plan` (document_class `individualized-plan`, facet teacher): 공통 목표·과제·성공기준·가장 어려운 사례 출구표, 임시 모둠 편성 정책, 재편성 근거, 그리고 Group A/B/C 각각의 pathway 프로파일(교사 프로파일 라벨·접근/표상/반응 지원·엄격성 유지 근거·확장 이동)을 담습니다.
- `worksheet-group-a/b/c` (document_class `worksheet`, facet student): 동일한 핵심 과제와 동일한 최난도 출구표를 그대로 담고, **모둠별로 다른 것은 학생 안전 지원과 반응 방식뿐**입니다.
- HWPX/DOCX/HTML 12개 파일: 문서별 3형식 parity, 문서 간 공통 계약(fingerprint) 동일.

## Dependencies (own subset)
- `standard-alignment-verify` — 성취기준 검증/격리(국가 provider 대조).
- `secondary-material-builder` — 단일 IR 파생·facet 분리·교사 승인 게이트.
- `material-rubric-qa` — rigor·PII·양방향 정합성 최종 QA.

## Core skill link
- `differentiate-lesson-pathways` (17개 Gate-v2 설계 스킬 중 개별화 경로 설계 스킬) — 교사 pathway 프로파일과 지원 설계의 교육학적 입력을 제공합니다. 이 링크는 provider closed-world 의존이 아니라 설계 단계 연결이며, core projection(17)은 변경하지 않습니다.

## Rules
- **단일 IR / 단일 renderer**: 네 문서는 하나의 `lesson-package-ir`의 document이다. 별도 IR/renderer를 만들지 않는다.
- **공통 계약 불변**: 공통 목표(target)·과제(task_ids)·성공기준(success)·가장 어려운 사례 출구표(exit)의 ID와 본문은 네 문서에서 동일해야 한다(`package_core_fingerprint` 일치).
- **학생 표면 = 중립 라벨만**: 학생 활동지는 `^Group [ABC]$` 중립 라벨만 노출한다. 진단·수준(기초/표준/심화/below/tier/scaffold/수준별/진단)·교사 프로파일 언어는 절대 노출하지 않는다.
- **교사 전용 의미 격리**: pathway 의미와 엄격성 근거는 교사 운영안(`content.pathway_profiles`)에만 존재한다. 학생 문서에는 `pathway_profiles`가 없어야 한다.
- **엄격성 유지**: 지원은 달라도 rigor는 떨어지지 않는다. 각 모둠은 모든 핵심 과제와 최난도 출구표를 그대로 수행한다. 확장(extension)은 **인지 조작을 바꿔야** 하며 분량만 늘리는 확장은 금지한다.
- **물리성 게이트**: 각 학생 활동지는 차시 분량·쓰기 공간·페이지 밀도·출구표 최난도·흑백 안전·모둠 중립성 게이트(`check_physical_workload`)를 모두 통과해야 한다(중학교 45분 기준 검증).
- **fail-closed**: 검증된 provider와 교사 승인이 모두 있어야 downstream-ready이다. 미검증/추론 provenance는 canonical IR로 성립하지 않는다(schema fail-closed).
- 국가 성취기준 원문·학교 평가계획 원문·PII·인증키·원본 소스는 노출/커밋하지 않는다.

## Observable failure conditions
- 문서가 4개가 아니거나 렌더 파일이 12개가 아니다.
- 학생 활동지에 진단/수준/교사 프로파일 언어가 노출된다.
- 모둠 간 공통 목표·과제·성공기준·출구표가 달라진다.
- 특정 모둠에서 핵심 과제가 빠지거나 최난도 출구표가 약화된다.
- 확장이 인지 조작 변화 없이 분량만 늘린다.
- 미검증 provider·교사 승인 없이 render가 downstream-ready로 표시된다.
