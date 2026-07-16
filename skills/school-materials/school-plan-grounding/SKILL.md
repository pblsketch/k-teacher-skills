---
name: school-plan-grounding
role: 학교 공시 평가계획 grounding (pin·fallback·PII)
authority_tier: school-evaluation-plan-provider
independent_implementation: true
---

# school-plan-grounding

`providers/school_evaluation` 어댑터로 실제 공시 평가계획을 가져와 학교·연도·학년·교과로 고정한다.

## Rules
- **Pin**: sido·sgg·kind·name + year + subject로 반드시 고정. 임의 학교/연도 추정 금지.
- **current→previous fallback**: 올해 계획이 없으면 전년도로 넘어가되 **교사에게 공개하고 승인**받은 뒤에만. 자동 승인 금지.
- **PII mask-or-block**: 교사 실명·연락처·학생 식별자를 마스킹. 표 컬럼의 이름처럼 안전하게 못 가리면 **차단**(fail-closed) 후 교사 검토.
- **탐지 범위와 최종 검토**: 자동 이름 차단은 담당교사·담임·작성자 등 사람 역할 열과 라벨이 있는 본문을 대상으로 한다. `영역`·`내용` 같은 일반 열에는 `물질`·`생명` 등 이름처럼 보일 수 있는 교과 어휘가 있으므로 전역 이름 정규식으로 과잉 차단하지 않는다. 실제 공시자료는 생성 승인 전에 교사가 잔여 개인정보를 최종 검토해야 한다.
- **Anchor**: URL·파일명·hash·조회시점·section/page/table anchor를 보존.
- **한계**: 20 docs/50MB/키워드 추출 한계, 이미지 PDF는 OCR/수동 fallback.
- 원격 MCP에는 로컬 파일 파싱 도구를 노출하지 않는다.

## Observable failure conditions
- pin 없이 "그 학교 평가계획"을 추정한다.
- fallback을 교사 승인 없이 자동 수행한다.
- PII가 남은 채로 downstream에 넘어간다.
- 실제 공시자료에 대한 교사 최종 PII 검토 승인 없이 downstream-ready로 전환한다.
