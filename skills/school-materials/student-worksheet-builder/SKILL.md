---
name: student-worksheet-builder
role: direct-entry 학생 활동지(worksheet) 오케스트레이터 — 단일 IR content.blocks 기반
authority_tier: materials
direct_entry: true
independent_implementation: true
dependencies:
  - standard-alignment-verify
  - secondary-material-builder
  - material-rubric-qa
---

# student-worksheet-builder

직접 진입(direct-entry) 가능한 **학생 활동지** 오케스트레이터입니다. `school-evaluation-plan-to-materials`와 같은 provider-orchestration 클래스에 속하지만, 학교 평가계획 전체가 아니라 하나의 성취기준에서 바로 학생 활동지를 만드는 좁은 입구입니다.

단일 canonical `lesson-package-ir`의 **추가적(additive) `content.blocks`** 위에서만 동작합니다. 두 번째 IR도, 두 번째 renderer도 만들지 않습니다. 블록은 `providers/materials/worksheet.py`가 정의하고, 물리적 게이트(`tests/validate_worksheet_physical.py`)와 `$defs/worksheetBlock`가 형태를 고정합니다.

## 산출
- 학생 활동지: 학습 과제(student_task)·쓰기 공간(answer_box)·채우기 표(fill_table)·자료 표(data_table)·수직선·자료 카드·모둠(group_cohesion)·문장 지원·출구표(exit_ticket).
- HWPX/DOCX/HTML 실제 표/쓰기 공간으로 렌더링되며 3-way parity로 검증됩니다.

## Dependencies (own subset)
- `standard-alignment-verify` — 성취기준 검증/격리(국가 provider 대조).
- `secondary-material-builder` — 단일 IR 파생·facet 분리·교사 승인 게이트.
- `material-rubric-qa` — rigor·PII·양방향 정합성 최종 QA.

## Rules
- **단일 IR / 단일 renderer**: worksheet 의미는 `content.blocks`로만 추가한다(별도 IR/renderer 금지).
- **물리성 게이트**: 차시 분량(초 40/중 45/고 50분의 0.5~1.0배), 쓰기 공간 최소 줄/높이, 페이지 밀도, 출구표 최난도, 흑백 안전(색-전용 지시는 pattern 필요), 모둠 중립성(`^Group [ABC]$`)을 모두 통과해야 한다.
- **Facet 분리(블록 재귀)**: 학생 블록의 모든 문자열 leaf와 구조 key를 검사한다. 정답/해설/오개념/배점/가중치/기초·표준·심화/발문·채점·루브릭·교사 노트 누출 금지.
- **다운스트림 준비 = 검증된 provider + 교사 승인**: 둘 중 하나라도 없으면 render는 downstream-ready가 아니다(fail-closed).
- **Standalone quick draft**: 검증된 provider·교사 승인이 없는 단독 요청은 `content.unresolved_boundary_markers`에 `standalone-quick-draft:unverified-provider`를 남긴 **맥락 전용 초안**만 만들며, 절대 downstream-ready가 아니다.
- 국가 성취기준 원문·학교 평가계획 원문·PII·인증키·GEPAI 원본은 노출/커밋하지 않는다.

## Observable failure conditions
- worksheet가 한 차시 분량을 넘거나(또는 절반 미만), 쓰기 과제인데 쓰기 공간이 최소치 미만이다.
- 출구표가 최난도 과제를 겨냥하지 않거나, 색-전용 지시에 흑백 대체 채널이 없다.
- 학생 블록에 교사용 언어(정답/오개념/배점/기초·심화/발문 등)나 금지 구조 key가 노출된다.
- 검증된 provider·교사 승인 없이 render가 downstream-ready로 표시된다.
