# Sample Dialogue — `grill-me-for-k-teacher` × Readiness Gate v2

이 파일은 K-Teacher Skills v2.5.1 **Readiness Gate v2**를 시연하는 sample-dialogue다.

v2.5.0 스타일 대화 흐름은 같은 폴더의 `sample-dialogue.md`를 참고하라. AI 학습 시스템이 `examples/` 폴더를 glob할 경우 두 파일 모두 노출되며, 본 파일이 새 진입점이다.

8개 시연 요소(아래 transcript 안에 [태그]로 표시):
1. 세션 첫 줄 threshold + source 출력
2. Round 0 topology 질문 (수업 단위 잠금)
3. Stage 1 weakest-dimension 라운드 with rationale
4. 매 라운드 weighted 점수 dimension별 표시
5. 매 질문 fact-routing 라벨
6. Pressure Ladder step 2 (assumption probe)
7. Practical closure audit 결정
8. `to-lesson-brief` 핸드오프 named context

---

## 입력 프롬프트

> 교사: 내일 중2 국어 활동지 만들어줘. 단원은 "주장하는 글쓰기"인데 학생들이 자기 의견을 잘 못 써.

---

## AI 응답

> 안녕하세요. 바로 활동지를 만들기 전에 readiness gate v2로 함께 정리하겠습니다.
>
> **`Readiness profile: Standard | threshold: 0.20 | source: skill-default`** [#1 threshold + source]
>
> 이 스킬(grill-me-for-k-teacher)은 Standard profile, Stage 1 · Intent-first가 기본입니다.

### Round 0 — Topology lock [#2 Round 0 topology]

> 먼저 이 요청의 단위를 잠그겠습니다.
>
> 이 요청의 단위는?
> A. 1차시 활동·발문 1개 (예: 내일 1교시 활동지만)
> B. 단원 전체 (3~10차시 — 주장하는 글쓰기 단원 통합 설계)
> C. 평가 체계 (수행평가·루브릭 중심)
> D. 학기·학년 흐름
> E. 다중 (직접 적기)
>
> 추천은 **A**입니다. "내일 활동지"라는 표현이 즉시 사용할 1차시 자료를 가리키는 것으로 보입니다.
> `[fact-routing: from-teacher-judgment]`

> 교사: A. 내일 1교시 50분 수업에서 쓸 활동지요.

---

### Round 1 [#3 Stage 1 weakest-dim with rationale]

```
[프로파일: Standard | 잠금 단위: 1차시 활동지 1개 | 라운드 1]
Stage 1 · 약점: Intent (0.7) | 근거: "의견을 잘 못 써"는 증상 묘사이며, 이 활동지가 학생의 *어떤 변화*를 끌어내야 하는지가 비어 있음
다음 질문 대상: Intent
[fact-routing: from-teacher-judgment]
```

> 1교시 50분 안에 학생이 보여야 할 *가장 중요한 행동 변화*는 무엇인가요?
>
> A. 자기 의견을 한 문장으로 명확하게 진술한다
> B. 의견에 근거 2개를 붙인다
> C. 반대 의견을 예상하고 응답한다
> D. 다른 학생 의견을 듣고 자기 의견을 수정한다
> E. 기타 (직접 적기)
>
> 추천은 **B**입니다. "의견을 잘 못 쓴다"는 표면 신호 뒤에는 보통 *근거 부재*가 있어, 의견-근거 연결을 끌어내는 게 중2 단계에서 가장 가성비 높습니다.

> 교사: B인 거 같긴 한데, 그렇다고 C(반대 의견 응답)도 너무 어렵게는 안 들리거든요. 둘 다 살리면 안 돼요?

---

### Round 2 [#6 Pressure Ladder step 2 — assumption probe]

```
[프로파일: Standard | 잠금 단위: 1차시 활동지 1개 | 라운드 2]
Stage 1 · 약점: Non-goals (0.8) | 근거: 학생 변화 목표가 B+C로 확장되면서 1교시 50분 안에 들어갈 수 있는지가 흐려짐
다음 질문 대상: Non-goals (Pressure Ladder step 2 — 숨은 가정)
[fact-routing: from-teacher-judgment]
```

> "B+C 둘 다 살린다"는 결정이 *통한다고 보시는 근거*가 어디서 오나요? 한 가지 확인하고 싶습니다.
>
> A. 작년에 같은 학생들이 비슷한 활동을 해본 적이 있다
> B. 50분 안에 의견 진술 → 근거 → 반대 응답까지 들어가는 게 가능하다는 경험이 있다
> C. 활동지를 두 페이지로 늘리면 된다고 가정하고 있다
> D. 사실은 둘 다 못 한다는 가능성도 열어두지만, 일단 시도해보고 싶다
> E. 기타
>
> 추천 없음. 이 질문은 *교사 판단의 근거*를 드러내기 위한 것이라 답이 D여도 좋은 정보입니다.

> 교사: 솔직히 D예요. 작년에 B는 됐는데 C까지 가본 적은 없어요. 1차시에서는 B 확실히, C는 다음 차시 도입으로 미루는 게 맞겠네요.

---

### Round 3 [#4 dimension별 weighted score 표시]

```
[프로파일: Standard | 잠금 단위: 1차시 활동지 1개 | 라운드 3]

| Dimension | Score | Weight | Weighted | Gap |
|-----------|-------|--------|----------|-----|
| Intent | 0.2 | 0.30 | 0.060 | 의견-근거 연결로 좁혀짐 |
| Learner | 0.5 | 0.20 | 0.100 | 학생 선행 지식 불명확 |
| Evidence | 0.6 | 0.25 | 0.150 | "잘 쓴 의견"의 관찰 형태 미정의 |
| Misconception | 0.5 | 0.10 | 0.050 | 흔한 오류 패턴 미파악 |
| Constraints | 0.3 | 0.10 | 0.030 | 50분 / 1교시 / 활동지 형식 확정 |
| Boundaries | 0.2 | 0.05 | 0.010 | 비목표(C는 다음 차시) 명시됨 |
| **Total clarity** | | | **0.400** | |
| **Ambiguity** | | | **0.600** | Stage 2 약함 |

Stage 1 · 약점: Learner (0.5) | 근거: "의견을 잘 못 써"의 구체 양상이 비어 있음
다음 질문 대상: Learner context
[fact-routing: from-class-context]
```

> 학생들의 현재 의견 글쓰기 양상은 보통 어느 쪽에 가깝나요? (작년 비슷한 학급 기준으로 익명화해 알려주시면 됩니다.)
>
> A. 의견은 쓰지만 근거를 빠뜨린다 ("저는 좋다고 생각합니다." 끝)
> B. 근거를 쓰지만 의견과 어긋난다 (찬성한다면서 반대 근거를 씀)
> C. 의견·근거 자체를 정하지 못해 1줄 쓰고 멈춘다
> D. 형식은 갖추지만 내용이 동어반복이다
> E. 기타

> 교사: A하고 D가 섞여 있어요. 의견은 한 줄 쓰는데 근거 자리에 같은 말을 다시 풀어 써요.

---

### Round 4

```
[프로파일: Standard | 잠금 단위: 1차시 활동지 1개 | 라운드 4]

| Dimension | Score | Weight | Weighted | Gap |
|-----------|-------|--------|----------|-----|
| Intent | 0.2 | 0.30 | 0.060 | 명확 |
| Learner | 0.2 | 0.20 | 0.040 | A+D 패턴 확인됨 |
| Evidence | 0.4 | 0.25 | 0.100 | "근거 2개"의 관찰 기준 필요 |
| Misconception | 0.2 | 0.10 | 0.020 | 동어반복이 핵심 오류로 식별됨 |
| Constraints | 0.3 | 0.10 | 0.030 | 명확 |
| Boundaries | 0.2 | 0.05 | 0.010 | 명확 |
| **Total clarity** | | | **0.740** | |
| **Ambiguity** | | | **0.260** | threshold 0.20에 근접 |

Stage 2 · 약점: Evidence (0.4) | 근거: Stage 1 통과. 활동지가 "근거 2개"를 *어떻게 보일지* 미정의
다음 질문 대상: Evidence
[fact-routing: from-teacher-judgment]
```

> "근거를 붙였다"를 활동지에서 *어떻게* 확인하시겠어요?
>
> A. 근거 칸을 2개로 나눠 각 칸에 다른 *사실/예시/경험* 중 하나를 적게 한다
> B. 근거 옆에 "의견과 같은 말은 아닌가?" 자가 점검 체크박스를 둔다
> C. 짝과 근거를 교환해 *동어반복인지* 표시하게 한다
> D. A+B 결합
> E. 기타
>
> 추천은 **D**입니다. 학생 오류가 "근거 자리에 의견을 푼다"라서, 다른 근거 *2개*라는 구조적 강제(A)와 *동어반복 점검*(B)이 둘 다 필요해 보입니다.

> 교사: D 좋아요. 짝 교환은 부담스럽다는 학생이 많아서 일단 빼고 갈게요.

---

### Round 5 — Closure audit [#7 Practical closure audit]

```
[프로파일: Standard | 잠금 단위: 1차시 활동지 1개 | 라운드 5]

| Dimension | Score | Weight | Weighted | Gap |
|-----------|-------|--------|----------|-----|
| Intent | 0.2 | 0.30 | 0.060 | 명확 |
| Learner | 0.2 | 0.20 | 0.040 | 명확 |
| Evidence | 0.2 | 0.25 | 0.050 | A+B 결합으로 명확 |
| Misconception | 0.2 | 0.10 | 0.020 | 명확 |
| Constraints | 0.3 | 0.10 | 0.030 | 명확 |
| Boundaries | 0.2 | 0.05 | 0.010 | C는 다음 차시 명시 |
| **Total clarity** | | | **0.790** | |
| **Ambiguity** | | | **0.210** | threshold 0.20 도달 직전 |

§4 mandatory gates 점검:
- ✅ 비목표 explicit (C는 다음 차시)
- ✅ 결정경계 explicit (짝 교환 빼는 결정)
- ✅ 개인정보 비요구
- ✅ 평가 증거 = 관찰 형태 (근거 2칸 + 자가 체크박스 산출물)
- ✅ 압박 패스 1회 완료 (Round 2 assumption probe)
```

> **Practical closure audit:** 다음 질문이 활동지 설계를 *실질적으로 바꿀까, 표현만 다듬을까?*
>
> 검토: 남은 흐릿함은 "도입 발문 어떻게 시작할지"인데, 이건 활동지 구조 결정(근거 2칸 + 자가 점검) 이후의 *수정 가능한 표현* 범주입니다. → **표현만 다듬음** → crystallize 진입.

---

### 공유된 이해 요약

제가 이해한 1차시 50분 활동지의 설계는 다음과 같습니다.

1. **Intent:** 학생이 의견을 1문장으로 진술하고 *서로 다른* 근거 2개를 붙인다. 동어반복은 피한다.
2. **Learner context:** 작년 비슷한 학급에서 의견 1줄 + 근거 자리에 동어반복 패턴이 흔함.
3. **Evidence:** 활동지에 (a) 의견 칸 1개 + (b) 근거 칸 2개 (각 사실/예시/경험 중 하나로 라벨링) + (c) "의견과 같은 말은 아닌가?" 자가 점검 체크박스.
4. **Misconception 신호:** 근거 자리에 의견을 다시 푸는 동어반복.
5. **Non-goals:** 반대 의견 응답(C)은 다음 차시 도입으로 미룸. 짝 교환은 이번 1교시 활동지에서 제외.
6. **Constraints:** 50분, 1교시, 종이 활동지 1장.

위 이해가 맞다면 활동지 초안을 만들겠습니다. 어떤 부분 수정·확장이 필요하면 알려주세요.

---

### 핸드오프 — `to-lesson-brief` 인계 [#8 named context block]

```
[handoff:to-lesson-brief]

Named context block (transcript-based, no persistent state):
- 프로파일: Standard
- 잠금 단위: 1차시 활동지 1개 (단원: 주장하는 글쓰기, 학년: 중2)
- 직전 출력 §12: Round 5 closure audit = crystallize 진입
- Topology: 1 component (active), 0 deferred
- Stage 1 통과 / Stage 2 통과
- mandatory gates 5/5 ✅
- 압박 패스 완료 (Round 2)
- 다음 차시 미정 항목: 반대 의견 응답 도입, 짝 교환 도입
- 교사 최종 판단 필요: 활동지 자가 점검 문구 톤(엄격 vs 격려)
```

---

## 검증 marker (validate via grep)

이 dialogue가 v2.5.1 Global checks v2를 모두 통과하는지 검증할 grep 패턴:
- `Readiness profile:` (#1)
- `Round 0` 또는 `이 요청의 단위는` (#2)
- `Stage 1 · 약점` (#3)
- `\| Weighted \|` (#4)
- `\[fact-routing:` (#5)
- `Pressure Ladder` 또는 `assumption probe` (#6)
- `Practical closure audit` (#7)
- `\[handoff:to-lesson-brief\]` (#8)

8개 marker 모두 본 파일에서 매치해야 한다.

---

## 부록 (v2.5.2+) — Provenance grading 시연

본 transcript는 국어 단원이라 성취기준이 큰 쟁점이 아니었다. v2.5.2에서 도입된 출처 등급(`:provided` / `:web` / `:inferred`)이 실제로 어떻게 작동하는지 짧은 대체 시나리오를 첨부한다.

### 시나리오: 교사가 성취기준 원문을 안 주고 단원명만 던진 경우

> 교사: 5학년 사회 "시민의 권리와 책임" 단원 활동지 만들어줘.

AI는 성취기준 원문을 받지 못했다. 사전 학습 지식으로 추정해야 한다. 이때 v2.5.2 hallucination guard가 발동한다.

> **AI:** Readiness profile: Standard | threshold: 0.20 | source: skill-default
>
> 시작 전 한 가지 확인이 필요합니다.
>
> **추정입니다.** 제 학습 지식으로는 이 단원이 2022 개정 사회과 [5사03-04] 정도 ("시민의 권리와 책임을 ...")일 것 같지만 **신뢰도는 낮습니다**. 시도·출판사별 단원 번호 차이가 있을 수 있습니다.
> **원문 한 줄만 알려주실 수 있을까요?** 확인되면 다음 질문으로 넘어가겠습니다.
> `[from-curriculum:inferred]`

> 교사: 미래엔 5학년 2학기 3단원이고 성취기준은 [6사03-04] "인권 보장의 중요성을 인식하고 인권 신장을 위해 노력한 다양한 사례를 탐구한다."예요.

> **AI:** 감사합니다. 성취기준이 갱신되었습니다.
> "[6사03-04] 인권 보장의 중요성을 인식하고 인권 신장을 위해 노력한 다양한 사례를 탐구한다." (미래엔 5학년 2학기 3단원)
> `[from-curriculum:provided]`
>
> 이제 핵심 동사는 *인식한다 / 탐구한다* 두 개로 좁혀집니다. Stage 1 첫 질문으로 넘어가겠습니다.
> `[from-teacher-judgment]` ...

### v2.5.2 운영 포인트

위 시연에서 확인된 hallucination guard 요소:
1. **추정 표시** — "추정입니다" 시작.
2. **신뢰도 경고** — "신뢰도는 낮습니다, 시도·출판사별 차이".
3. **확인 요청** — "원문 한 줄만 알려주실 수 있을까요?".
4. **선택지 사용 금지** — 객관식이 아닌 자유 서술 요청 (학생이 무비판적으로 추정안을 택할 위험 차단).
5. **격상 표시** — 교사 정정 후 `[from-curriculum:inferred]` → `[from-curriculum:provided]` 명시.

### 산출물 단계 룰

활동지·평가지·루브릭 *산출물*에 등장할 때:
- `:provided` 또는 `:web` 등급 → 그대로 인용 가능.
- `:inferred` 격상 안 된 채로 → 산출물에 직접 인용 금지. 격상 후이거나 "(추정)" 표시 유지.

이 운영 룰은 `references/interview-readiness.md` §7 Provenance grading + Hallucination guard + Escalation rule을 따른다.
