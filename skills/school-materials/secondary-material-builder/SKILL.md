---
name: secondary-material-builder
role: single canonical IR → 학생·교사(·학부모) 2차 자료 파생
authority_tier: materials
independent_implementation: true
---

# secondary-material-builder

`providers/materials`로 하나의 shared registry(single source of truth)에서 학생용·교사용 문서를 파생하고 `renderers/`로 HWPX/DOCX/HTML을 만든다.

## 산출
- 학생용: 과제안내·활동지(쓰기 공간 포함)·자기점검·학생 언어 성취기준.
- 교사용: 운영안·루브릭·관찰/피드백/미제출 체크리스트.
- 필요 시: 학부모 안내(요약, PII 없음).

## Rules
- **Facet 분리**: 학생 문서에 교사용 언어(루브릭 배점·오개념·tier·scaffold) 금지.
- **양방향 정합성**: 모든 학생 과제가 교사 문서에, 모든 교사 과제가 학생 문서에 대응.
- **쓰기 공간 물리성**: 쓰기를 요구한 문항 옆에 실제 쓰기 공간 배치.
- **교사 승인 gate**: 승인 전에는 render downstream-ready 아님(fail-closed).
- **Quick draft/full packet**: 물으면 초안, 무응답이면 full packet 기본.
- 단일 IR에서만 파생하여 HWPX/DOCX/HTML parity 보장.

## Observable failure conditions
- 학생 문서에 교사용 언어가 노출된다.
- 교사 계획에는 있는 과제가 학생 활동지에 없다(또는 반대).
- 쓰기 과제인데 쓰기 공간이 없다.
