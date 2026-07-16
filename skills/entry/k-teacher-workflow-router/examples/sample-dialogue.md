# Sample Dialogue: k-teacher-workflow-router

## User

내일 중2 국어 수업 활동지 좀 만들어줘.

## Assistant

바로 활동지를 만들면 딸깍식 산출물이 될 위험이 있습니다. 먼저 적절한 workflow를 선택하겠습니다.

요청 유형: 새 수업 준비 / 자료 생성 요청  
선택한 workflow: new-lesson-package  
선택 이유: 새 수업 패키지 vertical slice로 들어가야 하며, readiness를 먼저 고정한 뒤 평가 증거와 prototype 비교를 거쳐 lesson brief로 정리하는 흐름이 맞다.  
시작할 skill: `grill-me-for-k-teacher`  
다음 skill 후보: `assessment-first-design` → `lesson-prototype` → `to-lesson-brief`  
참여/표상/표현 장벽에 대한 주의점: 아직 학생 맥락이 비어 있으므로 특정 장벽 대응을 확정하지 말고 초기 질문에서 접근성·참여 장벽부터 확인한다.  
교사에게 던질 첫 질문: 이 수업에서 학생이 무엇을 이해하거나 할 수 있게 되길 바라나요?  
readiness 상태 또는 막힌 gate: intent/learner/evidence가 아직 충분히 고정되지 않아 readiness gate가 인터뷰 단계에 머물러 있다.

이 수업 설계를 어느 방향으로 시작할까요?

A. 수업 목표와 학생 맥락부터 정한다  
B. 평가 증거와 루브릭부터 정한다  
C. 활동 후보 2~3개를 먼저 비교한다  
D. 지금까지 생각한 내용을 브리프로 정리한다  
E. 기타: 직접 적기

추천은 A입니다. 아직 수업 의도와 학생 맥락이 확인되지 않았기 때문입니다.
