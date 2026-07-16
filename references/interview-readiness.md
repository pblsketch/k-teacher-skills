# Interview Readiness — Gate v2 (k-teacher-skills v2.5.1+)

이 문서는 K-Teacher Skills가 **언제까지 질문하고, 언제 산출물 생성으로 넘어갈지** 판단하는 공통 기준이다.

v2.5.1부터 OMC/OMX `deep-interview` 메커니즘을 한국 교사 맥락에 맞게 통합한 **Readiness Gate v2**를 운영한다. 17개 스킬 모두 이 문서를 단일 진실 원천(SSOT)으로 참조하며, 각 스킬의 `## Readiness gate v2` 블록은 본 문서의 메커니즘을 호출하는 얇은 포인터다.

`questioning-style.md`가 질문 *형식*을 다룬다면, 이 문서는 질문의 *종료 기준·평가 방법·전이 규칙*을 다룬다.

## Default loop

1. 요청을 받은 뒤 바로 자료를 만들지 않는다.
2. 현재 요청에 맞는 readiness profile을 고른다.
3. 관련 차원의 ambiguity score를 매긴다.
4. 가장 막히는 차원 하나만 골라 질문한다.
5. 답변 뒤 score를 다시 매긴다.
6. stop gate를 통과하면 먼저 이해 요약을 제시한다.
7. 사용자가 요청한 산출물로 넘어가되, 추정과 교사 판단 필요 항목을 표시한다.

## §1 — Threshold + source disclosure

세션 시작 시 **첫 줄**로 다음을 출력한다 (인사말 1줄은 선행 허용):

```
Readiness profile: {Quick|Standard|Deep} | threshold: {0.30|0.20|0.15} | source: {explicit|router-inferred|skill-default}
```

- `explicit` — 사용자가 직접 profile을 지정함 (예: `--deep`, "깊게 봐줘")
- `router-inferred` — `k-teacher-workflow-router`가 요청 키워드로 추론
- `skill-default` — 진입 스킬의 default profile (각 SKILL.md의 `## Readiness gate v2` 블록 참조)

profile별 운영 파라미터:

| Profile | Threshold (ambiguity) | Max rounds | 적용 상황 |
|---------|----------------------|-----------|-----------|
| Quick   | ≤ 0.30 | 4 | 작은 수정, 짧은 발문, 단일 활동 비교 |
| Standard| ≤ 0.20 | 8 | 일반 수업안·활동지·평가 장면 설계 |
| Deep    | ≤ 0.15 | 12 | 수행평가·루브릭·교육과정 재설계·실패 수업 복구 |

사용자가 빠른 초안을 원해도 mandatory gate(§4)와 개인정보 안전은 생략하지 않는다.

## §2 — Weighted scoring formula

각 차원을 0.0~1.0으로 평가하고 다음 가중치로 합산한다.

**Greenfield (새 수업 처음 설계):**
```
ambiguity = 1 - (intent·0.30 + learner·0.20 + evidence·0.25 + misconception·0.10 + constraints·0.10 + boundaries·0.05)
```

**Brownfield (성취기준·기존 자료 기반 재설계):**
```
ambiguity = 1 - (intent·0.25 + learner·0.15 + evidence·0.25 + misconception·0.10 + constraints·0.10 + boundaries·0.05 + curriculum_grounding·0.10)
```

가중치 합 = 1.00 (검증).

**Anchor — 각 차원의 score 해석:**

- `0.0` — 명확하다. 구체 예시·증거·경계가 있다.
- `0.3` — 대체로 명확. 산출물 생성 가능하지만 추정 표시 필요.
- `0.6` — 흐릿. 질문 하나가 더 필요하다.
- `1.0` — 비어 있거나 모순. 바로 만들면 딸깍식 산출물이 된다.

활성 차원만 평균 내어 `current_ambiguity`로 본다. 단, 아래 §4 mandatory gate가 막혀 있으면 평균이 낮아도 ready가 아니다.

## §3 — Stage priority (Intent-first)

차원을 단순 평균으로 다루지 않는다. **3단계 우선순위 격자**로 처리한다.

- **Stage 1 (priority):** Intent · Learner context · Non-goals · Decision boundaries
- **Stage 2:** Evidence · Misconception · Success criteria
- **Stage 3 (brownfield only):** Curriculum grounding · Existing material context

**규칙:**
- weakest-dimension 타깃팅은 *활성 stage 안에서만* 작동한다.
- Stage 1의 어떤 차원이라도 weak(≥0.6)이면 Stage 2 질문으로 넘어가지 않는다.
- Stage 3는 brownfield 작업(성취기준·기존 자료)에서만 활성화된다.

**근거:** 활동·평가는 의도와 학생 맥락에 종속된다. 의도가 흐릿한 상태에서 평가 증거를 묻기 시작하면 "어떤 활동이 좋을까"라는 도구적 대화로 미끄러진다.

## §4 — Mandatory gates (weighted ambiguity와 분리)

다음 5개는 *가중 ambiguity 점수와 무관하게* hard-gate다. 어느 하나라도 통과 못 하면 산출물 생성 금지.

1. **비목표 (Non-goals) explicit** — 사용자가 "이건 안 하겠다"를 최소 1개 이상 명시함
2. **결정경계 (Teacher decision boundaries) explicit** — 사용자가 "내가 최종 판단할 지점"을 명시함
3. **학생 개인정보 비요구 confirmed** — AI가 실명·민감정보 요청 없이 진행
4. **평가 증거 = 관찰 가능한 형태** — 산출물·발화·문제 해결·설명 중 하나 이상 명시
5. **압박 패스(§5) 1회 이상 완료** — 적어도 한 번은 evidence/assumption/boundary/essence 중 하나로 압박했음

가중 ambiguity ≤ threshold라도 위 5개 중 하나라도 비어 있으면 인터뷰 계속.

## §5 — Pressure Ladder (4단계 압박 사다리)

각 답변을 *주장(claim)*으로 다루고 다음 라더의 한 단을 적용해 다음 질문을 만든다.

1. **Evidence/example/counterexample 요구** — "이 주장의 구체 사례 하나만요?", "반대 사례는 없었나요?"
2. **Hidden assumption probe** — "이 활동이 통한다고 보는 근거는 어디서 오나요?", "당연하게 두고 있는 전제는 무엇인가요?"
3. **Boundary/tradeoff force** — "절대 *하지 않을* 것은 무엇인가요?", "이걸 얻기 위해 포기할 수 있는 것은?"
4. **Symptom → essence reframe** — "지금까지 묘사는 *행동*인데, 학습 *본질*로 보면 무엇인가요?", "활동이 아니라 학생 변화로 다시 말하면?"

**규칙 (커버리지 함정 방지):**
- 답변이 여전히 흐릿하면 차원을 *회전*하지 않는다. 같은 thread에서 한 단계 더 깊게 들어간다.
- 한 단계 깊어졌거나, 한 가정이 명확해졌거나, 한 경계가 분명해졌을 때만 다음 차원으로 이동.

## §6 — Practical closure audit

산출물 crystallize 직전에 AI는 자기에게 다음을 묻는다:

> 다음 질문이 수업·자료·평가를 *실질적으로* 바꿀까, 아니면 표현만 다듬을까?

- **실질적으로 바꿈** → 계속 질문.
- **표현만 다듬음** → crystallize.

낮은 ambiguity 점수는 *crystallize 허가*가 아니라 *closure audit 진입 신호*다. 점수가 낮아도 새 가지(branch)를 열어 인터뷰를 끝없이 늘리지 않는다.

**Stop condition (모두 만족해야 산출물 생성 또는 다음 스킬로 이동):**
1. `current_ambiguity` ≤ profile threshold (§2)
2. §4 mandatory gate 5개 모두 통과
3. §5 압박 패스 적어도 1회 완료
4. closure audit 결과 = "표현만 다듬음"
5. 사용자가 원래 요청한 산출물이나 다음 작업으로 넘어가는 것이 안전

## §7 — Fact routing labels

질문·답변·transcript의 모든 항목에 라벨을 부착한다. 라벨은 *누가 알 수 있는가*를 구분한다.

- `[from-curriculum]` — 성취기준·교육과정 문서 (사실, 검색·확인 가능)
  - AI가 알 수 있다면 *교사에게 묻지 말 것*. 진술 형태로 제공.
- `[from-textbook]` — 교과서 차시·예시·연습문제 (사실; 추정 표시 허용)
  - 추정일 경우 "추정"이라고 표시. 확인 가능하면 확인.
- `[from-class-context]` — 교사가 명시한 학급 맥락 (사용자 제공 사실)
  - 익명화된 학급 수준 정보. 실명·민감정보는 입력 금지.
- `[from-teacher-judgment]` — 평가 가치판단·비목표·학생 변화 목표·트레이드오프 (판단, 인터뷰 대상)
  - **인터뷰는 이 라벨을 위한 것이다.** 사실 항목은 AI가 진술한다.

**Provenance grading (v2.5.2+) — 사실 라벨 출처 등급 suffix.**

`[from-curriculum]`과 `[from-textbook]`은 어디서 왔는지에 따라 3개 등급 중 하나를 suffix로 부착한다:

- `:provided` — 사용자가 채팅창·첨부에 *원문*을 직접 제공함 (가장 안전). AI는 그 텍스트만 인용·해석.
- `:web` — WebFetch/WebSearch로 공식 출처(NCIC·교육청·교과서 출판사)에서 검색. URL 출처와 함께 인용. AI는 검색 결과의 신뢰성을 1줄 검증한다.
- `:inferred` — AI 사전 학습 지식만으로 추정. **"추정"** 표시 + 신뢰도 경고 + 교사 확인 요청 prompt가 필수.

`[from-class-context]`와 `[from-teacher-judgment]`는 출처가 본질적으로 사용자라 grading 없음.

**Hallucination guard for `:inferred` grade.**

사실 항목을 사전 학습 지식으로 진술할 때는 다음 형식을 *반드시* 따른다:

```
추정입니다. 제 학습 지식으로는 [내용]일 것 같습니다. 신뢰도는 낮습니다.
원문 또는 출처를 확인해주실 수 있을까요?
[from-curriculum:inferred]
```

확인 요청 없이 `:inferred` 진술을 transcript에 그대로 두면 §4 mandatory gate 위반으로 간주한다.

**Provenance escalation rule.**

- 시작 등급은 `:inferred`로 출발한다 (제공된 자료가 없을 때 기본값).
- 교사가 확인·정정하면 → `:provided`로 격상되어 transcript에 갱신 표시.
- 인터넷 검색으로 출처 확인되면 → `:web`으로 격상.
- `:inferred` 상태로는 산출물(활동지·평가지·루브릭)에 해당 사실 항목을 *직접 인용 금지*. 산출물에 등장할 때는 "(추정)" 표시 유지하거나 격상된 등급에서만 인용.
- unresolved `:inferred` 사실이 하나라도 남아 있으면 provenance가 아직 풀리지 않은 상태로 본다. 이 상태에서는 `to-lesson-brief` downstream-ready handoff, `author-ir`, `render`를 unblock하지 않는다. handoff에는 해당 항목을 blocking fact로 남긴다.
- provider가 제공한 원문·응답은 read-only input으로만 취급한다. downstream 단계는 이를 `provider` record로만 들고 가며 `read_only_input: true`를 유지한 채 provenance를 우회해 ready 상태를 만들면 안 된다.
- downstream-ready 결론은 summary 문구만으로 만들지 않는다. provider / provenance / license evidence를 각 record 단위로 보존하고, 각 record의 `provider` · `provenance_grade` · `source_reference` · `verification_evidence_type` · `verification_anchor` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input`이 모두 맞아야 clearance 근거가 된다.
- provider / provenance / license 중 하나라도 비어 있거나 unresolved면 fail-closed로 유지한다. 특히 `source_license.status`가 `verified-compatible`이 아니면 downstream-ready를 열지 않는다.
- `:provided`/`:web`로 provenance가 풀려도 downstream-ready 출력에는 별도의 `provider` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input` evidence가 계속 필요하다. provenance 해결만으로는 unblock되지 않는다.
- mixed-revision 또는 source/version/raw→normalized trace가 정리되지 않은 provider record는 `quarantined`로 격리한다. 이 상태에서는 downstream-ready handoff, `author-ir`, `render`를 unblock하지 않는다.

**Stateless dialectic rhythm heuristic (자기 검사, 매 라운드):**
- 직전 transcript의 *가장 최근 두 항목 라벨*을 점검한다.
- 둘 다 비-judgment(`[from-curriculum]`/`[from-textbook]`/`[from-class-context]`)이면 다음 발화는 `[from-teacher-judgment]` 질문을 우선한다.
- 턴 카운터·외부 상태에 의존하지 않는다. 매 라운드 transcript의 마지막 두 항목만 본다. stateless skill loader에서도 적용 가능한 휴리스틱이다.

**예시 (잘못된 라우팅):**
> ❌ AI가 "이 단원의 성취기준이 무엇인가요?"를 교사에게 묻는다 → `[from-curriculum]`인데 인터뷰화함. AI가 직접 진술해야 함.

**예시 (올바른 라우팅 — `:provided` case):**
> ✅ AI: "제공해주신 자료를 보면 성취기준은 '[5사03-04] 시민의 권리와 책임...'으로 보입니다. `[from-curriculum:provided]` 이 해석이 맞다면, 이 수업에서 학생의 *어떤 행동*이 '시민의 책임'을 입증할 증거인가요? `[from-teacher-judgment]`"

**예시 (올바른 라우팅 — `:inferred` case, 교사가 자료를 안 줬을 때):**
> ✅ AI: "추정입니다. 제 학습 지식으로는 이 단원이 [5사03-04] 정도일 것 같지만 신뢰도는 낮습니다. 원문 한 줄만 알려주실 수 있을까요? `[from-curriculum:inferred]` 확인되면 다음 질문으로 넘어가겠습니다."

격상 후:
> ✅ AI: "감사합니다. 성취기준이 '[5사03-03] 인권 보장의 중요성...'으로 갱신되었습니다. `[from-curriculum:provided]` 이제 학생이 '인권 보장'을 입증할 행동을 정의하겠습니다. `[from-teacher-judgment]`"

## §8 — Round 0 topology (수업 단위 잠금)

첫 ambiguity 점수 매기기 *전에* 단 한 번 묻는다:

```
이 요청의 단위는?
A. 1차시 활동·발문 1개
B. 단원 전체 (3~10차시)
C. 평가 체계 (수행평가·루브릭)
D. 학기·학년 흐름
E. 다중 구성요소 (직접 적기)
```

잠근 뒤 운영 규칙 — **Topology × Stage priority lattice:**

- **Rule 1 (Stage global):** Stage priority는 글로벌이다. 활성 구성요소 *전체*가 Stage 1 weakest를 통과하기 전에는 어떤 구성요소도 Stage 2 질문을 받지 않는다.
- **Rule 2 (Component rotation within stage):** 동일 stage 내에서 활성 구성요소가 N>1이면, 매 라운드 가장 약한 (component, dimension) 쌍을 타깃한다. 직전 라운드와 다른 구성요소를 우선해 회전한다 (depth-first 함정 방지).
- **Rule 3 (Component-A Stage-1 weak + Component-B Stage-2 weak 충돌):** Rule 1 우선. Component-A의 Stage 1을 먼저 해결한 뒤 Component-B의 Stage 2로 이동.
- **Rule 4 (Deferred components):** 사용자가 명시적으로 deferred로 설정한 구성요소는 ambiguity 계산에서 제외하되, topology 목록과 final brief에는 보존.

**비활성:** Tier 3 disabled-for-quick-profile 스킬(`k-teacher-workflow-router`, `zoom-out-lesson`, `lesson-prototype`, `to-lesson-brief`)은 Round 0 topology를 발동하지 않는다.

## §9 — Ontology convergence (핵심 개념·평가 증거 안정성)

매 라운드 transcript에서 4종 entity를 추출한다:
- 핵심 개념
- 평가 증거
- 학생 행동
- 자료 종류

**Stability ratio** = (stable entities + renamed entities) / total entities. 0.0~1.0.

**Convergence signal:** 2 라운드 연속 stability ≥ 0.8 → crystallize 안전 (가중 ambiguity가 threshold를 약간 넘어도 OK).

- *stable* — 같은 이름으로 두 라운드 연속 등장
- *renamed* — type 동일 + field 50% 이상 겹침, 이름만 다름
- *new* — 새 entity
- *removed* — 직전 라운드에 있었으나 사라짐

**비활성:** Tier 3 disabled-for-quick-profile 스킬에서는 ontology 추출 생략.

## §10 — Challenge modes (라운드 트리거)

다음 임계 라운드에 도달하면 질문 perspective를 한 번씩 전환한다 (인터뷰당 각 모드 1회).

- **Round 3+ Contrarian** — "반대 가정이라면? 교과서 순서가 정답이 아니라면? 이 활동이 *오히려 학생 사고를 막는다면?*"
  - Quick profile(최대 4라운드)에서는 한 번 발동 가능.
- **Round 5+ Simplifier** — "한 차시 5분으로 줄이면 핵심은 무엇이 남는가? 자료를 절반으로 줄여도 학습 증거가 보이는가?"
  - Standard·Deep profile에서 도달.
- **Round 7+ Ontologist** — "이 수업이 가르치는 것은 결국 무엇인가? 활동·자료가 아닌 *학습*으로 다시 정의하면?"
  - Deep profile에서 사실상 전용.

ambiguity가 3 라운드 연속 ±0.05 안에서 멈추면(stall) Ontologist를 강제 발동.

**비활성:** Tier 3 disabled-for-quick-profile 스킬에서는 challenge modes 발동 안 함.

## §11 — Stateless transparency rule

**이 저장소 스킬은 stateful runtime이 아니다.** 각 invocation은 fresh context로 시작한다. 따라서:

- AI는 "이전 세션 상태를 기억한다"라고 주장하지 않는다.
- 사용자가 "이어서" / "다시" / "다음에"라고 말하면 AI는 다음과 같이 응답한다:

  > 저는 영구 메모리가 없어 이전 인터뷰 상태를 자동 복원하지 못합니다. 다음 항목을 다시 알려주시면 이어가겠습니다: {프로파일, 잠금 단위, 직전 약점 dimension, 직전 답변 요약}.

- transcript가 같은 대화창에 남아 있으면 그 transcript를 단일 자료원으로 삼아 진행한다.
- `to-lesson-brief` 핸드오프 시에는 transcript의 마지막 §12 출력 블록 + topology 잠금 결과를 named context block으로 인계한다. 이건 *transcript-기반 인계*이지 별도 snapshot 저장소가 아니다.

## §12 — Per-round output template

인터뷰 라운드 종료 시 다음 형식으로 출력한다.

**Full form (Standard·Deep profile 기본):**

```
[프로파일: Standard | 잠금 단위: 단원전체 | 라운드 3]
Stage 1 · 약점: 비목표(0.6) | 근거: 사용자가 "다 다루고 싶다" 외엔 제외 항목 없음
다음 질문 대상: 비목표
[fact-routing: from-teacher-judgment]

{질문}
```

**Short form (Quick profile, Progress line 변형):**

```
현재는 평가 증거가 가장 불명확합니다.
이 부분만 확인되면 수업안 초안으로 넘어갈 수 있습니다.
[from-teacher-judgment]
```

내부적으로는 다음 형식으로 판단한다 (사용자에게 보이지 않아도 됨):

```
Readiness: Standard
current_ambiguity: 0.31
blocking_gate: learning evidence
next_question_target: students' observable evidence
```

---

## If max rounds are reached

최대 질문 라운드에 도달하면 질문을 계속 늘리지 않는다.

대신 다음 중 하나를 한다.

- ready가 아니면 `아직 생성하면 위험한 이유`를 짧게 요약하고, 가장 중요한 질문 하나만 남긴다.
- 사용자가 강하게 원하면 `안전한 최소 초안`만 만들고, 모든 추정을 명시한다.
- 다음 스킬로 넘길 때도 `미확정`과 `교사 판단 필요`를 함께 넘긴다.

## Red flags

- 질문 수를 많이 채웠다는 이유만으로 ready라고 판단한다.
- 교사가 "알아서 해줘"라고 했다는 이유로 평가 증거를 건너뛴다.
- 평균 score는 낮지만 mandatory gate가 비어 있는데 산출물을 만든다.
- 성취기준이나 교육과정 근거를 추정하면서 추정이라고 표시하지 않는다.
- 수업 실패를 관찰 증거 없이 학생 태도 문제로 결론낸다.

**Gate v2 위반 패턴 (v2.5.1 추가):**

- 첫 줄에 threshold/source를 출력하지 않고 인터뷰를 시작한다.
- Stage 1 weakest가 0.6 이상인데 Stage 2 질문을 던진다.
- `[from-curriculum]` 사실을 교사에게 인터뷰화한다.
- 사용자 답변을 압박 라더 없이 그대로 받아들이고 다음 차원으로 회전한다.
- "이전 세션 상태를 기억한다"고 주장한다 (stateless 위반).
