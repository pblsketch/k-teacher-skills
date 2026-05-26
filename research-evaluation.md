# Research Evaluation: K-Teacher AI Skills

작성일: 2026-05-26  
평가 대상: `k-teacher-ai-skills` 1차 Skill Pack  
평가 관점: Matt Pocock 개발자용 skills, Claude/OpenAI Skills 공식 문서, 교육 설계 레퍼런스, 교육 AI 안전 원칙과 비교

## Executive Summary

전체 평가는 **7.6 / 10**입니다.

판정:

- **콘셉트 수준**: 매우 강함
- **교육적 전환 수준**: 강함
- **스킬 작성 품질**: 실사용 가능한 베타
- **레퍼런스 대비 완성도**: Matt Pocock 원본 철학의 핵심은 잘 이식했으나, 원본 고급 스킬들이 가진 "문서 업데이트", "검증 루프", "시각적 리포트", "설치/테스트 경험"은 아직 부족함
- **GitHub 공개 가능성**: 공개는 가능하지만, v0.1.0으로 배포하고 "검증 중"임을 표시하는 것이 안전함

핵심 판단:

> 이 스킬셋은 "딸깍 생성"을 막고 교사의 전문적 판단을 끌어내는 방향은 매우 선명하다.  
> 다만 레퍼런스급 스킬팩이 되려면, 각 스킬이 실제 대화에서 어떻게 작동하는지 보여주는 예시 transcript와 self-test 시나리오가 필요하다.

## References Used

### Agent skill references

- OpenAI Academy, "Using skills": Skills are reusable workflows with name/description, workflow instructions, resources, required inputs, output format, and final checks.  
  https://openai.com/academy/skills/

- Claude Code Docs, "Extend Claude with skills": Claude skills use `SKILL.md`, YAML frontmatter, optional supporting files, progressive disclosure, and concise instructions.  
  https://code.claude.com/docs/en/skills

- Matt Pocock `grill-me`: one-question-at-a-time interviewing until shared understanding, with recommended answers.  
  https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md

- Matt Pocock `grill-with-docs`: domain glossary, `CONTEXT.md`, ADRs, precise language, and inline documentation updates.  
  https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md

- Matt Pocock `tdd`: red-green-refactor, vertical slices, public-interface behavior testing.  
  https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md

- Matt Pocock `diagnose`: reproduce → hypothesize → instrument → fix → regression-test, with falsifiable hypotheses.  
  https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnose/SKILL.md

- Matt Pocock `improve-codebase-architecture`: deepening opportunities, shallow/deep module vocabulary, deletion test, and architecture report.  
  https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md

### Education design references

- Backward Design / Understanding by Design: identify desired results, determine acceptable evidence, then plan learning activities and materials.  
  https://teaching.uic.edu/cate-teaching-guides/syllabus-course-design/backward-design/

- CAST Universal Design for Learning: clear goals, anticipating barriers, meaningful options, learner variability, engagement/representation/action-expression.  
  https://www.cast.org/what-we-do/universal-design-for-learning/

### AI in education safety references

- UNESCO AI Competency Framework for Teachers: teacher AI competencies include human-centred mindset, ethics of AI, AI pedagogy, and professional learning.  
  https://www.unesco.org/en/articles/ai-competency-framework-teachers

- UNESCO Guidance for Generative AI in Education and Research: emphasizes human-centred use, data privacy protection, ethical validation, and pedagogical design.  
  https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research

## Scoring Criteria

총점은 다음 8개 기준으로 판단했습니다.

1. Skill format compatibility
2. Trigger clarity
3. Workflow executability
4. Faithfulness to Matt Pocock skill philosophy
5. Educational design alignment
6. Safety/privacy/human agency
7. Progressive disclosure and maintainability
8. Evidence of validation

## Overall Score: 7.6 / 10

### 1. Skill format compatibility: 8.0 / 10

강점:

- 각 스킬이 별도 폴더와 `SKILL.md`를 갖고 있음.
- YAML frontmatter에 `name`, `description`이 있음.
- OpenAI/Claude의 기본 skill 구조와 맞음.
- README, LICENSE, examples가 있어 GitHub 배포 기본 요건은 충족함.

부족:

- Claude용 설치 구조가 직접적으로 `.claude/skills/<skill>/SKILL.md` 형태로 안내되지 않음.
- Codex용 설치 경로도 구체 명령 예시가 부족함.
- 각 skill 내부에서 `examples/` 템플릿을 언제 참조할지 명시하지 않음.

개선:

- README에 `cp -r skills/grill-me-for-k-teacher ~/.claude/skills/` 같은 설치 예시 추가.
- Codex용 `~/.codex/skills/` 또는 사용 중인 skill installer 흐름을 별도 섹션으로 정리.
- 각 `SKILL.md` 끝에 "Related templates" 섹션 추가.

### 2. Trigger clarity: 8.0 / 10

강점:

- description에 사용 상황과 트리거 표현이 잘 들어가 있음.
- "수업안", "활동지", "평가지", "루브릭", "수업 실패" 등 교사 언어가 반영됨.

부족:

- 일부 스킬은 서로 겹칠 수 있음.
  - `grill-me-for-k-teacher`와 `assessment-first-design`
  - `grill-with-curriculum`과 `improve-lesson-architecture`

개선:

- README에 "어떤 상황에서 어떤 스킬을 쓸까?" 의사결정 가이드 추가.
- 각 스킬 description 첫 문장에 더 강한 구분점 추가.

### 3. Workflow executability: 7.5 / 10

강점:

- 각 스킬이 Non-negotiables, Workflow, Output format, Review checklist, Red flags를 갖고 있음.
- 교사가 바로 쓸 수 있는 객관식 질문 예시가 있음.
- "먼저 묻고 나중에 만든다"는 실행 절차가 명확함.

부족:

- 실제 사용 transcript가 없음.
- 성공/실패 예시 출력이 없음.
- 스킬 간 연결 흐름이 아직 약함.

개선:

- 각 스킬마다 `examples/sample-dialogue.md` 추가.
- `grill-me-for-k-teacher → assessment-first-design → improve-lesson-architecture` 같은 체인 예시 추가.

### 4. Faithfulness to Matt Pocock skill philosophy: 8.2 / 10

강점:

- `grill-me`의 핵심인 "공유된 이해", "한 번에 한 질문", "추천 답변 제공"을 잘 이식함.
- `tdd`의 피드백 루프를 assessment-first로 잘 전환함.
- `diagnose`의 재현/가설/계측/수정/회귀 흐름을 수업 진단으로 잘 바꿈.
- `improve-codebase-architecture`의 deep/shallow 개념을 수업 모듈에 적용한 점이 좋음.

부족:

- 원본 고급 스킬들은 codebase/docs를 직접 탐색하고 문서를 업데이트하는데, 교사용 버전은 아직 "제공 자료를 읽는다" 수준에 머묾.
- `grill-with-curriculum`은 `CONTEXT.md`/ADR 대응물이 있으나 실제 파일 업데이트 규칙이 약함.
- `improve-lesson-architecture`는 원본처럼 후보 리포트를 만들고 선택 후 grilling loop로 들어가는 구조가 없음.

개선:

- `grill-with-curriculum`에 `CURRICULUM-CONTEXT.md`, `CLASS-CONTEXT.md`, `LESSON-ADR.md` 업데이트 규칙을 더 구체화.
- `improve-lesson-architecture`에 "후보 3개를 먼저 제시하고, 교사가 고른 후보만 깊게 파는" 원본 구조 추가.

### 5. Educational design alignment: 8.5 / 10

강점:

- Backward Design의 "목표 → 증거 → 활동" 흐름과 강하게 맞음.
- 평가 증거, 루브릭, 오개념, 피드백 루프가 반복적으로 들어감.
- 교과서 순서나 자료 생성 중심 수업을 비판하는 방향이 명확함.

부족:

- UDL 관점이 아직 약함.
- 학생 다양성, 접근성, 표현 방식 선택, 참여 장벽 제거가 별도 체크로 충분히 들어가지 않음.

개선:

- 각 스킬 Review checklist에 다음 질문 추가:
  - 학생이 이해를 표현할 수 있는 방식이 하나뿐인가?
  - 접근 장벽을 낮추는 대안이 있는가?
  - 참여, 표상, 표현 중 어느 장벽을 줄였는가?

### 6. Safety/privacy/human agency: 8.8 / 10

강점:

- 학생 개인정보, 실명, 민감정보를 요구하지 않는다는 문구가 모든 스킬에 있음.
- AI가 교사 판단을 대체하지 않는다는 철학이 README에 있음.
- UNESCO의 human-centred, privacy, ethical validation 방향과 잘 맞음.

부족:

- AI 산출물의 사실 오류, 편향, 교육과정 오인 위험에 대한 검증 루프가 더 필요함.
- "AI 사용 기록을 어떻게 남길지"는 아직 없음.

개선:

- README에 "AI 산출물 검토 원칙" 추가.
- 각 스킬 output에 "AI가 추정한 부분 / 교사가 확인해야 할 부분"을 분리하도록 명시.

### 7. Progressive disclosure and maintainability: 6.8 / 10

강점:

- 현재 `SKILL.md`들은 2~5KB 수준이라 과도하게 크지는 않음.
- 파일 수가 적고 구조가 단순함.

부족:

- Claude 문서가 권장하는 supporting files 활용이 아직 약함.
- 예시 템플릿이 별도 폴더에 있지만 스킬 내부에서 적극적으로 참조하지 않음.
- 같은 철학과 안전 문구가 여러 파일에 반복됨.

개선:

- 공통 안전 원칙을 `references/safety.md`로 분리하고, 각 스킬에서 필요할 때 참조.
- 각 스킬에 1개씩 `examples/`를 두어 SKILL.md 본문을 더 얇게 만들기.

### 8. Evidence of validation: 4.8 / 10

강점:

- 파일 구조, frontmatter, privacy guard, anti-click guard는 자동 검증함.

부족:

- 실제 프롬프트를 넣고 스킬이 어떻게 반응하는지 테스트하지 않음.
- 교사 사용성 테스트가 없음.
- 레퍼런스급 스킬은 "작동 증거"가 중요한데 아직 부족함.

개선:

- 5개 스킬 각각에 대해 최소 2개 test prompt를 만들어 실행 결과를 저장.
- "좋은 응답 / 나쁜 응답" 기준을 추가.
- 실제 교사 1~3명에게 README만 주고 사용 가능한지 확인.

## Skill-by-Skill Evaluation

### `grill-me-for-k-teacher`: 8.6 / 10

가장 완성도 높음. 원본 `grill-me`의 핵심 DNA가 잘 살아 있음.

좋은 점:

- 바로 만들지 않는다는 원칙이 선명함.
- 한 번에 한 질문 원칙이 명시됨.
- 추천 답변을 제공한다는 원본 핵심이 반영됨.
- 교육 맥락 질문이 적절함.

아쉬운 점:

- 원본은 매우 짧고 강한데, 이 버전은 설명이 많아 약간 무거움.
- 실제 "Round 1, Round 2" 대화 예시가 있으면 더 강해짐.

개선 우선순위:

- sample dialogue 추가.
- "질문이 막히면 객관식으로 전환" 규칙 추가.

### `grill-with-curriculum`: 7.8 / 10

방향은 좋지만 원본 `grill-with-docs`에 비해 문서 업데이트 메커니즘이 약함.

좋은 점:

- 성취기준을 지어내지 말라는 규칙이 중요함.
- 추정 표시 원칙이 있음.
- 교육과정 용어, 핵심 개념, 평가 증거를 추출하도록 함.

아쉬운 점:

- `CURRICULUM-CONTEXT.md`를 실제로 언제 업데이트할지 규칙이 약함.
- `LESSON-ADR.md`를 언제 만들지 기준이 부족함.

개선 우선순위:

- "용어가 확정되면 즉시 context 파일에 반영" 규칙 추가.
- "되돌리기 어렵고, 나중에 의문이 생기며, 실제 대안이 있었던 결정만 ADR로 기록" 규칙 추가.

### `assessment-first-design`: 8.3 / 10

교육 설계 레퍼런스와 가장 잘 맞는 스킬.

좋은 점:

- Backward Design과 정렬이 강함.
- 활동보다 증거가 먼저라는 메시지가 분명함.
- 루브릭 품질 기준이 있음.

아쉬운 점:

- TDD 원본의 vertical slice 감각이 아직 약함.
- "하나의 증거 → 하나의 최소 활동 → 피드백" 루프가 더 반복적으로 표현되어야 함.

개선 우선순위:

- "한 번에 전체 수행평가를 만들지 말고, 한 증거 장면부터 설계" 규칙 강화.
- 예시 루브릭과 exit ticket 샘플 추가.

### `diagnose-lesson-failure`: 8.0 / 10

수업 성찰용으로 실전성이 높음.

좋은 점:

- 관찰 증거를 먼저 묻는 구조가 좋음.
- 학생 탓/교사 탓 단정을 막음.
- 원인 범주가 교육적으로 설득력 있음.

아쉬운 점:

- 원본 diagnose처럼 "가설은 반드시 falsifiable prediction을 가져야 한다"가 약함.
- 수정 후 재검증 기준이 더 구체적이어야 함.

개선 우선순위:

- 각 가설을 "만약 X가 원인이라면, Y를 바꾸면 Z가 관찰될 것이다" 형식으로 쓰도록 강제.
- 다음 차시 확인 지표를 숫자/산출물/발화 기준으로 쓰게 하기.

### `improve-lesson-architecture`: 7.5 / 10

아이디어는 매우 좋지만 레퍼런스 대비 가장 보강 여지가 큼.

좋은 점:

- shallow/deep module을 수업 구조로 바꾼 전환이 강함.
- 자료를 더 만드는 것이 아니라 구조를 깊게 한다는 메시지가 좋음.
- 자료별 역할 재배치가 실용적임.

아쉬운 점:

- 원본의 "삭제 테스트", "후보 리포트", "추천 강도", "선택 후 grilling loop"가 충분히 이식되지 않음.
- "깊은 수업 모듈"의 평가 기준이 더 명확해야 함.

개선 우선순위:

- "이 자료를 지우면 복잡성이 사라지는가, 아니면 다른 곳에 흩어지는가?"라는 삭제 테스트 추가.
- 개선 후보를 Strong / Worth exploring / Speculative로 분류.
- 후보 3개를 제시하고 교사가 하나를 고르면 세부 설계로 들어가기.

## Reference-Level Gap Analysis

레퍼런스 대비 가장 큰 격차는 세 가지입니다.

### Gap 1. 실제 작동 예시 부족

Matt Pocock의 좋은 스킬은 짧아도 실행 궤도가 매우 선명합니다. 우리 스킬은 철학과 구조는 강하지만, 사용자가 README만 보고 "아 이렇게 대화가 흘러가는구나"를 즉시 보기는 어렵습니다.

필요 작업:

- 각 스킬별 sample dialogue 1개
- 각 스킬별 bad prompt → corrected workflow 예시 1개

### Gap 2. 문서화 루프 부족

`grill-with-docs`는 용어가 확정되면 `CONTEXT.md`에 반영하고, 중요한 결정은 ADR로 남깁니다. 우리 `grill-with-curriculum`은 이 철학을 언급하지만 실행 규칙이 약합니다.

필요 작업:

- `references/context-files.md` 추가
- `CURRICULUM-CONTEXT.md`, `CLASS-CONTEXT.md`, `LESSON-ADR.md` 작성 규칙 구체화

### Gap 3. 검증 증거 부족

현재 검증은 파일 구조와 키워드 존재 확인입니다. 레퍼런스급 배포에는 실제 사용 테스트가 필요합니다.

필요 작업:

- `tests/prompts/` 추가
- `tests/expected-behaviors.md` 추가
- 최소 10개 프롬프트로 수동 테스트 기록

## Release Recommendation

현재 상태로는 **v0.1.0-beta** 공개를 권합니다.

이유:

- 철학과 핵심 workflow는 충분히 강함.
- MIT 라이선스와 README가 있음.
- 5개 스킬이 실제 `SKILL.md`로 존재함.
- 다만 실제 교사 사용성 검증과 transcript 예시가 없어 "stable"이라고 부르기엔 이름.

권장 릴리스 문구:

```text
K-Teacher AI Skills v0.1.0-beta

AI로 수업자료를 바로 생성하는 대신, 교사의 수업 의도·학생 맥락·평가 증거를 먼저 질문하게 만드는 한국 교사용 Skill Pack입니다.

현재 버전은 교사/AI 활용가의 피드백을 받기 위한 beta입니다.
```

## Priority Fix List

1. README에 설치법 추가
   - Claude
   - Codex
   - 수동 복사

2. 각 스킬에 sample dialogue 추가
   - 5개 파일 또는 각 skill 내부 `examples/sample-dialogue.md`

3. `grill-with-curriculum` 문서화 규칙 강화
   - `CURRICULUM-CONTEXT.md`
   - `CLASS-CONTEXT.md`
   - `LESSON-ADR.md`

4. `diagnose-lesson-failure`에 falsifiable hypothesis 형식 추가

5. `improve-lesson-architecture`에 deletion test와 후보 리포트 구조 추가

6. UDL 체크 추가
   - 참여 장벽
   - 표상 장벽
   - 표현/행동 장벽

7. `tests/expected-behaviors.md` 작성

## Bottom Line

이 스킬셋은 단순 프롬프트 모음이 아니라, 개발자 agent skill 철학을 교사 전문성의 언어로 꽤 설득력 있게 옮긴 결과물입니다.

레퍼런스와 비교했을 때:

- **철학 이식**은 상위권
- **교육 설계 정렬**은 강함
- **안전/개인정보 가드**도 좋음
- **실제 배포 완성도**는 아직 beta
- **검증 증거**는 부족

따라서 지금은 "공개 가능한 v0.1.0-beta" 수준이고, sample dialogue와 테스트 프롬프트까지 추가하면 "실사용 권장 v0.2.0" 수준으로 올라갈 수 있습니다.
