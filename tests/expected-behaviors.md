# Expected Behaviors

이 문서는 `K-Teacher AI Skills`가 최소한 지켜야 할 행동 기준입니다.

## Global checks

모든 스킬은 다음을 지켜야 합니다.

- `SKILL.md`가 존재한다.
- YAML frontmatter에 `name`과 `description`이 있다.
- 학생 실명, 민감정보, 실제 학생 사례를 요구하지 않는다.
- 자료를 바로 생성하지 않고 먼저 질문/검증/설계 루프를 수행한다.
- 질문을 계속할지 산출물로 넘어갈지 readiness gate로 판단한다.
- 교사의 최종 판단 지점을 남긴다.
- UDL 또는 접근성 관점에서 참여/표상/표현 장벽을 검토한다.

## Global checks v2 (v2.5.1+)

모든 스킬은 v2.5.0 Global checks에 더해 다음을 지킨다 (Readiness Gate v2 운영 규칙):

- **세션 첫 줄 threshold 공개** — 인사말 1줄 선행 허용. 정확한 형식:
  ```
  Readiness profile: {Quick|Standard|Deep} | threshold: {0.30|0.20|0.15} | source: {explicit|router-inferred|skill-default}
  ```
- **Stage priority 글로벌** — Stage 1의 어떤 차원이라도 weak(≥0.6)이면 Stage 2 질문 금지. `interview-readiness.md` §3 참조.
- **Mandatory gates 분리 hard-stop** — 비목표·결정경계·평가증거·개인정보비요구·압박패스 1회 중 어느 하나라도 비어 있으면 weighted ambiguity와 무관하게 인터뷰 계속. §4 참조.
- **Fact routing 라벨 명시** — 매 질문과 답변에 `[from-curriculum]`/`[from-textbook]`/`[from-class-context]`/`[from-teacher-judgment]` 중 하나를 transcript에 부착. 사실 항목은 AI가 진술, judgment 항목만 인터뷰 대상. §7 참조.
- **Weighted score dimension별 표시** — 매 라운드 종료 시 단일 평균이 아닌 dimension별 score · weight · weighted contribution 표 출력. §2 가중치 공식 적용. Quick profile에서는 short-form 변형 허용.
- **Pressure pass before crystallize** — 산출물 생성 전 최소 1회 Pressure Ladder 4단계 중 한 단계 적용. §5 참조.
- **Topology lock acknowledgement** — Tier 3 enabled 스킬은 Round 0 topology 결과를 `to-lesson-brief` 핸드오프 named context block에 포함. Tier 3 disabled-for-quick-profile 스킬 (router/zoom-out/lesson-prototype/to-lesson-brief)은 해당 안 됨. §8 참조.
- **Stateless transparency** — "이전 세션 상태를 기억한다"고 주장 금지. 사용자 resume 요청 시 transcript 기반 인계임을 명시. §11 참조.

## Global checks v2.1 (v2.5.2+)

v2.5.1 Global checks v2에 더해, 사실 라벨의 출처 등급 운영을 추가한다:

- **Provenance grade suffix 부착** — `[from-curriculum]`·`[from-textbook]` 인용은 매번 `:provided` / `:web` / `:inferred` 중 하나의 suffix를 붙인다. 등급 표시 없는 사실 라벨은 §7 위반.
- **`:inferred` 3요소 prompt 강제** — AI 추정 진술은 반드시 (1) "추정" 표시, (2) "신뢰도 낮음" 경고, (3) "원문/출처 확인 요청" 세 요소를 한 묶음으로 제시. 확인 요청 없는 `:inferred`는 §4 mandatory gate 위반.
- **Escalation 표시** — 교사가 확인·정정해 `:inferred → :provided`로 격상되면 transcript에 갱신을 명시한다 (예: "성취기준이 갱신되었습니다. `[from-curriculum:provided]`").
- **산출물 직접 인용 금지 (`:inferred`)** — `:inferred` 상태로는 활동지·평가지·루브릭 등 산출물에 해당 사실을 직접 인용하지 않는다. 산출물에 등장할 때는 격상 후이거나 "(추정)" 표시를 유지한다.
- **선택지 질문 금지 (`:inferred`)** — `:inferred` 사실은 객관식 선택지 형태로 묻지 않는다 (사용자가 무비판적으로 추정안을 택할 위험 차단). 자유 서술 형태로 원문 확인 요청만 허용.
- **Downstream-ready no-unblock (`:inferred`)** — unresolved `:inferred` 사실이 하나라도 남아 있으면 downstream-ready handoff, `author-ir`, `render`로 넘기지 않는다. handoff에는 blocking provenance 상태를 유지한다.
- **Provider output read-only 입력** — provider가 건넨 원문·응답은 read-only input으로만 취급한다. downstream 단계는 이를 `provider` record로만 들고 가며 `read_only_input: true`를 유지한 채 provenance를 우회해 ready 상태를 만들지 않는다.
- **Per-record clearance evidence** — downstream-ready 결론은 summary 문구만으로 열지 않는다. 각 record에 `provider` · `provenance_grade` · `source_reference` · `verification_evidence_type` · `verification_anchor` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input`을 남기고 그 record가 clearance 근거가 되어야 한다.
- **Provider/provenance/license fail-closed** — provider / provenance / license 중 하나라도 비어 있거나 unresolved면 fail-closed로 유지한다. 특히 `source_license.status`가 `verified-compatible`이 아니면 downstream-ready가 아니다.
- **Provider/license evidence 유지** — `:provided`/`:web`로 provenance가 풀려도 `provider` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input` evidence 없이는 downstream-ready가 아니다.
- **Provider quarantine fail-closed** — mixed-revision 또는 source/version/raw→normalized trace가 정리되지 않은 provider record는 `quarantined`로 격리한다. 이 상태에서는 downstream-ready handoff, `author-ir`, `render`를 열지 않는다.

## Skill-specific checks

### `grill-me-for-k-teacher`

Prompt:

```text
중2 국어 주장하는 글쓰기 활동지 만들어줘.
```

Expected:

- 바로 활동지를 만들지 않는다.
- 수업 의도, 학생 맥락, 평가 증거 중 하나를 먼저 질문한다.
- 가능하면 객관식 선택지를 제공한다.
- readiness gate를 통과하기 전에는 완성 활동지를 만들지 않는다.

### `grill-with-curriculum`

Prompt:

```text
성취기준은 "자료를 해석하여 사회 현상의 특징을 설명한다"야. 기존 활동지는 빈칸 채우기야.
```

Expected:

- 성취기준의 핵심 동사를 분석한다.
- 기존 활동과 성취기준의 어긋남을 지적한다.
- `CURRICULUM-CONTEXT.md` 또는 `LESSON-ADR.md` 기록 후보를 제안할 수 있다.

### `assessment-first-design`

Prompt:

```text
초5 과학 생태계 활동지를 만들어줘.
```

Expected:

- 활동지보다 학습 증거를 먼저 묻는다.
- 성공 기준과 최소 평가 장면을 먼저 설계한다.

### `diagnose-lesson-failure`

Prompt:

```text
오늘 비율 수업이 망했어. 애들이 하나도 못 따라왔어.
```

Expected:

- 학생 탓으로 단정하지 않는다.
- 관찰 가능한 증거를 먼저 묻는다.
- 가설을 "만약-수정-관찰" 형식으로 쓴다.

### `improve-lesson-architecture`

Prompt:

```text
PPT, 활동지, 퀴즈가 흩어져서 수업 흐름이 산만해.
```

Expected:

- 새 자료를 바로 만들지 않는다.
- 핵심 질문, 학습 증거, 성공 기준을 먼저 찾는다.
- 삭제 테스트와 후보 리포트를 사용한다.

### `zoom-out-lesson`

Prompt:

```text
이 카드뉴스 활동 괜찮을까?
```

Expected:

- 활동 자체를 바로 평가하지 않는다.
- 활동보다 한 단계 위 맥락을 묻는다.
- 목표, 단원 흐름, 평가 증거와의 연결을 확인한다.

### `lesson-prototype`

Prompt:

```text
도입 활동을 몇 가지 안으로 비교해줘.
```

Expected:

- 완성 수업안을 바로 만들지 않는다.
- 2~3개 prototype을 만든다.
- 각 prototype의 검증 질문, 장점, 위험을 비교한다.

### `to-lesson-brief`

Prompt:

```text
지금까지 이야기한 걸 수업 브리프로 정리해줘.
```

Expected:

- 새 인터뷰를 시작하지 않는다.
- 대화에 없는 정보는 `미확정`으로 표시한다.
- 확정/추정/교사 판단 필요 항목을 분리한다.

### `ai-resilient-assignment-redesign`

Prompt:

```text
학생들이 ChatGPT로 보고서를 복붙할까 봐 걱정돼. 과제를 바꾸고 싶어.
```

Expected:

- AI 탐지 도구 단독 사용을 권장하지 않는다.
- H→AI→H 구조로 과제를 재설계한다.
- AI 시대 취약점을 진단한다.
- 프롬프트 로그와 SHIFT 성찰지를 포함한다.
- 과정 중심 평가 비중을 50% 이상으로 둔다.
- 학생 개인정보 입력 금지를 안내한다.

### `thinking-routine-selector`

Prompt:

```text
학생 생각을 보이게 하는 사고 루틴을 추천해줘.
```

Expected:

- 루틴 이름만 나열하지 않는다.
- 사고 목적과 수업 단계를 먼저 확인한다.
- 루틴 결과를 평가 증거와 연결한다.

### `concept-based-inquiry-designer`

Prompt:

```text
이 단원을 개념 기반 탐구 질문 중심으로 바꾸고 싶어.
```

Expected:

- 성취기준을 지어내지 않는다.
- 핵심 개념, 일반화, 사실적/개념적/논쟁적 질문을 구분한다.
- 학생이 일반화를 도출할 흐름을 제안한다.

### `differentiate-lesson-pathways`

Prompt:

```text
학생 수준 차이가 커서 기초/표준/심화 활동이 필요해.
```

Expected:

- 같은 핵심 목표를 유지한다.
- 학생을 고정 수준으로 낙인찍지 않는다.
- 기초/표준/심화 경로와 공통 평가 증거를 제시한다.

### `rubric-quality-guard`

Prompt:

```text
이 루브릭의 채점 기준이 괜찮은지 봐줘.
```

Expected:

- 과제 구성요소와 평가 준거를 구분한다.
- 수준 기술을 관찰 가능한 수행으로 바꾼다.
- 성취기준과 평가 증거의 정렬을 확인한다.

### `hinge-question-designer`

Prompt:

```text
수업 중 오개념을 확인할 힌지 질문을 만들어줘.
```

Expected:

- 많은 문항을 바로 만들지 않는다.
- 확인하려는 오개념과 다음 수업 결정을 먼저 정한다.
- 선택지별 학생 사고와 교사 대응을 제시한다.

### `pbl-design-coach`

Prompt:

```text
지역 문제를 활용한 PBL을 설계하고 싶어.
```

Expected:

- 산출물부터 정하지 않는다.
- 실제 문제, driving question, 학생 역할, 청중을 정한다.
- 과정 평가와 개인 학습 증거를 포함한다.

### `udl-barrier-remover`

Prompt:

```text
말하기 부담이 큰 학생도 참여하게 UDL 관점으로 바꿔줘.
```

Expected:

- 학생을 문제로 보지 않는다.
- 참여/표상/행동과 표현 장벽을 구분한다.
- 목표는 유지하고 접근 경로를 다양화한다.

### `k-teacher-workflow-router`

Prompt:

```text
내일 수업 활동지 좀 만들어줘.
```

Expected:

- 활동지를 바로 만들지 않는다.
- 요청 유형을 분석한다.
- 적절한 workflow를 선택한다.
- 시작할 skill과 다음 skill 후보를 제시한다.
- 교사에게 질문할 때 선택지를 제공한다.
- workflow 선택 뒤 readiness 상태나 막힌 gate를 고려한다.
- AI 대응 과제 요청은 `ai-resilient-assignment-redesign`으로 라우팅한다.
- 사고 루틴, 개념 탐구, 개별화, 루브릭, 힌지 질문, PBL, UDL 요청을 각각 적절한 스킬로 라우팅한다.
