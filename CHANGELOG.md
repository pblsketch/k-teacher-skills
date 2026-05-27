# Changelog

본 저장소는 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다.

## v2.5.3 — 2026-05-27

### Added (Claude Cowork / Claude Code plugin support)

K-Teacher Skills를 **Claude Cowork**와 **Claude Code**의 공식 plugin marketplace protocol에 부합하도록 plugin manifest를 도입했다. 기존 17개 SKILL.md와 폴더 구조는 *변경 없이*, 메타 파일과 명령 셸만 추가했다.

- **`.claude-plugin/plugin.json`** — Plugin manifest. 17개 skill 경로 명시(2단계 폴더 계층 유지), commands 디렉토리 선언, keywords·license·repository 메타데이터.
- **`.claude-plugin/marketplace.json`** — Self-hosted marketplace 메타. GitHub repo 자체를 marketplace로 노출할 때 사용. Team/Enterprise는 private marketplace로 사내 배포 가능.
- **`commands/` 디렉토리** — 11개 slash command 추가. 각 command는 workflow chain의 진입점이며 첫 스킬을 로딩하고 Readiness Gate v2 banner 출력을 강제한다:
  - `commands/k-teacher.md` — 최상위 router 진입점 (어떤 스킬 쓸지 모를 때)
  - `commands/new-lesson.md` — new-lesson-design (Standard)
  - `commands/redesign.md` — curriculum-grounded-redesign (Deep)
  - `commands/failure.md` — lesson-failure-recovery (Standard)
  - `commands/architecture.md` — material-architecture-improvement (Standard)
  - `commands/ai-assignment.md` — ai-resilient-assignment-redesign (Deep)
  - `commands/inquiry.md` — conceptual-inquiry-lesson (Deep)
  - `commands/differentiate.md` — differentiated-lesson-redesign (Standard)
  - `commands/assessment.md` — assessment-quality-upgrade (Deep)
  - `commands/pbl.md` — pbl-design-workflow (Deep)
  - `commands/udl.md` — udl-accessible-lesson-redesign (Standard)

### Changed

- `README.md` — Quick install 위에 "Install as Claude Cowork / Claude Code plugin (v2.5.3+)" 섹션 추가. Option 1 marketplace add + install, Option 2 `--plugin-dir` 로컬 로딩, Option 3 manual copy 호환.
- `skill-pack.json` — `version`: `2.5.2` → `2.5.3`. (skill-pack.json은 자체 manifest로 유지, plugin.json은 Claude 공식 manifest로 신규 추가 — 두 manifest 공존, 단일 진실 원천은 plugin.json.)
- `tests/validate_skill_pack.py` — 5개 새 assertion 추가:
  - `.claude-plugin/plugin.json` 존재 + `name`/`version`/`skills` 필드 검증
  - `.claude-plugin/marketplace.json` 존재 + plugins 배열 길이 = 1
  - plugin.json의 `skills` 배열 길이 = 17 + 각 경로 실존 확인
  - `commands/` 디렉토리에 11개 `.md` 파일 존재
  - version assertion: skill-pack.json + plugin.json + marketplace.json 모두 `2.5.3`

### Plugin installation pathways (after v2.5.3)

| Surface | Installation |
|---------|-------------|
| Claude Cowork (desktop) | `/plugin marketplace add pblsketch/k-teacher-skills` → `/plugin install k-teacher-skills@k-teacher` |
| Claude Code (CLI) | 동일 marketplace 명령 또는 `claude --plugin-dir ./k-teacher-skills` 로컬 로딩 |
| Claude.ai Skills (web) | 각 스킬 폴더 zip → 업로드 (기존 호환) |
| Manual copy | `install-claude.ps1` / `install-codex.ps1` / `install-antigravity.ps1` (기존 호환) |

### Namespaced slash command UX

Plugin 설치 시 스킬·command 호출이 namespaced로 바뀐다:

```
/k-teacher-skills:k-teacher 내일 수업 활동지 만들어줘
/k-teacher-skills:new-lesson 단원 전체 설계
/k-teacher-skills:assessment 수행평가 루브릭 검토
```

이는 plugin 간 충돌 방지 목적. 직접 `Skill("k-teacher-skills:grill-me-for-k-teacher")` 호출도 가능.

### Preserved (no breaking change)

- 17 SKILL.md (`name`/`description` frontmatter), 7-group 폴더 계층, sample dialogues, references, install scripts — 모두 그대로.
- v2.5.0/v2.5.1/v2.5.2의 모든 validator assertion 통과 유지.
- v2.5.2 Readiness Gate v2 + provenance grading 메커니즘 그대로.
- `skill-pack.json`은 자체 manifest로 유지(역사적 호환). plugin.json이 추가됐을 뿐 대체 안 됨.

### Migration

v2.5.2 → v2.5.3은 patch-level. AI 행동 변화 없음. 사용자가 추가로 얻는 것:
- Cowork/Code marketplace를 통한 1-line 설치
- 11개 workflow slash command shortcut
- private marketplace를 통한 팀·기관 배포

기존 manual copy 사용자도 그대로 작동.

---

## v2.5.2 — 2026-05-27

### Added (Provenance grading)

`[from-curriculum]`·`[from-textbook]` 사실 라벨에 출처 등급 suffix를 도입했다. v2.5.1의 fact routing 라벨이 "이 정보가 사실인가 판단인가"를 구분했다면, v2.5.2는 "이 사실이 *어디서* 왔는가"까지 추적한다.

- **3개 출처 등급** (`references/interview-readiness.md` §7):
  - `:provided` — 사용자가 채팅창·첨부에 원문을 직접 제공함 (가장 안전, AI는 인용·해석만)
  - `:web` — WebFetch/WebSearch로 공식 출처(NCIC·교육청·교과서 출판사)에서 검색, URL 인용
  - `:inferred` — AI 사전 학습 지식 기반 추정, 환각 위험
- **Hallucination guard** — `:inferred` 진술은 반드시 "추정 / 신뢰도 낮음 / 교사 확인 요청" 3요소 prompt 형식 강제. 확인 요청 없이 transcript에 남기면 §4 mandatory gate 위반.
- **Provenance escalation rule** — 시작은 `:inferred` → 교사 확인 시 `:provided` 격상 → 인터넷 출처 확인 시 `:web` 격상. `:inferred` 상태로는 활동지·평가지·루브릭 산출물에 직접 인용 금지.
- **선택지 질문 금지 (v2.5.2 추가 룰)** — `:inferred` 사실은 선택지 형식으로 묻지 않는다. 사용자가 객관식에서 무비판적으로 추정안을 택할 위험 차단.

### Changed

- `references/interview-readiness.md` §7 — Provenance grading 섹션 + Hallucination guard 형식 + Escalation rule 추가. §7 예시 2개 갱신 (`:provided` case + `:inferred → :provided` 격상 case).
- `references/questioning-style.md` — Fact routing in questions 섹션 뒤에 Provenance grading 짧은 cross-reference 추가 (선택지 사용 금지 룰 포함).
- `README.md` — Readiness Gate v2 (v2.5.1+) 섹션의 Fact routing 라벨 항목에 v2.5.2 등급 suffix 명시.
- `skill-pack.json` — `version`: `2.5.1` → `2.5.2`.
- `tests/validate_skill_pack.py` — Loop α에 3개 grade marker 추가 (`:provided`, `:web`, `:inferred`) — Loop α total markers 14 → 17.
- `tests/expected-behaviors.md` — `Global checks v2.1 (v2.5.2+)` 섹션 추가. 4개 새 행동 기준 (provenance grade 부착, `:inferred` 3요소 prompt, escalation 표시, 산출물 직접 인용 금지).
- `skills/entry/grill-me-for-k-teacher/examples/sample-dialogue-gate-v2.md` — v2.5.2 부록 섹션 추가. AI가 `:inferred`로 출발 → 교사 정정 → `:provided`로 격상되는 한 라운드 시연.

### Why this matters (정직성 보강)

v2.5.1의 `[from-curriculum]` 라벨은 "AI가 사실을 책임지고 진술한다"는 행동 규약이었지만, 실제로 AI가 *어떻게* 그 사실에 도달하는지 (사용자 제공 / 검색 / 추정)는 불투명했다. 한국 교육과정·교과서 데이터베이스가 spec에 통합돼 있지 않은 상황에서, `:inferred` 등급과 hallucination guard는 AI 환각의 가시화·확인·격상 경로를 만든다. v2.6.0의 진짜 grounding (NCIC API·교육과정 인덱스 캐시)을 향한 중간 단계.

### Preserved (no breaking change)

- v2.5.1의 모든 4 라벨 (`from-curriculum`/`from-textbook`/`from-class-context`/`from-teacher-judgment`) 의미 유지.
- 17 SKILL.md의 `## Readiness gate v2` 블록 *수정 없음* (블록은 base label만 선언; grade suffix는 runtime per-statement 부착).
- `tests/readiness_gate_v2_mapping.json` 변경 없음.
- v2.5.1 validator의 모든 assertion 통과 유지 (Loop α는 markers 추가만, 기존 14개 모두 유지).
- v2.5.1 sample-dialogue-gate-v2.md의 본문 흐름 유지; v2.5.2 시연은 부록으로 추가.

### Migration

v2.5.1 → v2.5.2는 patch-level이라 별도 마이그레이션 작업 불필요. AI 행동에는 다음이 추가됨:
- `[from-curriculum]` 또는 `[from-textbook]` 사실을 인용할 때마다 출처 등급 suffix 부착
- 추정 진술 시 3요소 prompt 형식 의무화

---

## v2.5.1 — 2026-05-27

### Added (Readiness Gate v2)

OMC/OMX `deep-interview` 메커니즘을 한국 교사 맥락에 맞게 통합한 Readiness Gate v2를 도입했다.

- **가중치 공식** (`references/interview-readiness.md` §2) — 단순 평균 대신 차원별 가중치 합산. Greenfield 6 dimension, Brownfield 7 dimension (curriculum_grounding 추가).
- **Stage priority (Intent-first)** (§3) — Stage 1 (Intent/Learner/Non-goals/Boundaries) → Stage 2 (Evidence/Misconception/Success) → Stage 3 (Brownfield curriculum grounding). 약한 stage가 있으면 다음 stage 질문 금지.
- **Mandatory gates 분리** (§4) — 비목표·결정경계·평가증거·개인정보비요구·압박패스 5개를 weighted ambiguity와 별개 hard-gate로 운영.
- **Pressure Ladder 4단계** (§5) — Evidence → Hidden assumption → Boundary/tradeoff → Symptom→essence reframe. 답변이 흐릿하면 차원 회전 대신 같은 thread에서 한 단계 더 깊게.
- **Practical closure audit** (§6) — 점수 낮음 = crystallize 허가가 아니라 closure audit 진입 신호. "다음 질문이 실질적으로 바꿀까, 표현만 다듬을까?" 자기 점검.
- **Fact routing 4 라벨** (§7) — `[from-curriculum]` / `[from-textbook]` / `[from-class-context]` / `[from-teacher-judgment]`. 인터뷰는 마지막 라벨에만, 사실 항목은 AI가 진술. Dialectic rhythm heuristic (stateless): 직전 두 라벨이 비-judgment면 다음은 judgment 우선.
- **Round 0 topology** (§8) — 1차시 / 단원 / 평가체계 / 학기흐름 / 다중 중 하나로 수업 단위 잠금. Topology × Stage priority 4-rule lattice 정의.
- **Ontology convergence** (§9) — 핵심 개념·평가 증거·학생 행동·자료 종류 4종 entity 안정성 추적. 2 라운드 연속 stability ≥ 0.8 시 crystallize 안전.
- **Challenge modes** (§10) — Round 3+ Contrarian / Round 5+ Simplifier / Round 7+ Ontologist (각 인터뷰당 1회).
- **Stateless transparency** (§11) — "이전 세션 상태 기억" 주장 금지. Resume은 transcript 기반.
- **Per-round output template** (§12) — `[프로파일 | 잠금 단위 | 라운드]` + Stage 약점 + dimension별 가중치 표 + fact-routing 라벨.

### Added (Tooling)

- `tests/readiness_gate_v2_mapping.json` — 17 스킬의 (profile, stage, labels, tier3) 매핑 SSOT. 새 스킬 추가 시 이 파일에 row 추가 후 validator 통과 확인.
- `skills/entry/grill-me-for-k-teacher/examples/sample-dialogue-gate-v2.md` — 8개 transcript 요소를 시연하는 v2 sample dialogue (behavioral anchor for v2.5.1).

### Changed

- `references/interview-readiness.md` — Readiness Gate v2 spec으로 전면 재작성. v2.5.0의 `Default loop`, `If max rounds are reached`, `Red flags` 섹션은 보존; `Readiness profiles`, `Core dimensions`, `Mandatory stop gates`, `Progress line`은 §1~§12로 흡수.
- `references/questioning-style.md` — `Pressure Ladder reference` 와 `Fact routing in questions` 두 cross-reference 섹션 추가. 내용 중복 없이 v2 spec을 가리키도록.
- 17개 SKILL.md 전체 — `## Non-negotiables` 다음에 `## Readiness gate v2 (v2.5.1+)` 블록 (6줄) 삽입. 각 스킬의 default profile, active stage, applicable fact-routing labels, Tier 3 enabled/disabled, full spec pointer, mapping JSON pointer 선언.
- `README.md` — `Interview readiness` 섹션 뒤에 `Readiness Gate v2 (v2.5.1+)` 서브섹션 추가. 9개 신규 메커니즘 요약 + 첫 줄 threshold 출력 형식 + Tier 3 면제 4개 스킬 명시.
- `skill-pack.json` — `version`: `2.5.0` → `2.5.1`.
- `tests/validate_skill_pack.py` — Readiness Gate v2 검증을 위한 4개 새 validator loop 추가:
  - Loop α: 14개 v2 vocabulary marker 존재
  - Loop β: 17 SKILL.md에 `## Readiness gate v2` 블록 존재
  - Loop γ: `interview-readiness.md` §1~§12 섹션 순서 검증 (regex)
  - Loop δ: 각 SKILL.md 블록의 (profile, stage, labels, tier3) 4-tuple이 mapping JSON과 일치
- `tests/expected-behaviors.md` — `Global checks v2 (v2.5.1+)` 섹션 추가. 8개 새 행동 기준 (threshold 첫 줄 출력, Stage priority 글로벌, mandatory gate hard-stop, fact-routing 라벨, weighted 점수 표시, pressure pass, topology lock acknowledgement, stateless transparency).

### Preserved (no breaking change)

- 모든 v2.5.0 스킬 이름, description, 7-group 폴더 계층 (`entry/`, `lesson-design/`, `inquiry-pbl/`, `assessment/`, `individualization/`, `diagnostics/`, `ai-era/`).
- v2.5.0 sample-dialogue.md 16개 (grill-me 제외 — 새 `sample-dialogue-gate-v2.md` append-alongside).
- v2.5.0 mandatory safety gates — 학생 개인정보 비요구, 평가 증거 우선, 실명·민감정보 요구 금지.
- 10개 workflow chain — `new-lesson-design`, `curriculum-grounded-redesign`, `lesson-failure-recovery`, `material-architecture-improvement`, `ai-resilient-assignment-redesign`, `conceptual-inquiry-lesson`, `differentiated-lesson-redesign`, `assessment-quality-upgrade`, `pbl-design-workflow`, `udl-accessible-lesson-redesign`.
- v2.5.0 validator의 모든 assertion — 새 v2 loop은 *추가*된 것이지 *대체*가 아님.
- 설치 스크립트 (`install-codex.ps1`, `install-claude.ps1`, `install-antigravity.ps1`, `install-all.ps1`) — 동일 작동.

### Tier 3 면제 (Quick-profile skills)

다음 4개 스킬은 Tier 3 메커니즘 (Round 0 topology, Ontology convergence, Challenge modes)을 발동하지 않는다:

- `k-teacher-workflow-router` (Quick, routing only)
- `zoom-out-lesson` (Quick, single-activity comparison)
- `lesson-prototype` (Quick, prototype comparison)
- `to-lesson-brief` (Quick, output-only)

사유: Quick profile은 최대 4-5 라운드로 종결되어 Challenge modes 트리거 (Round 3+/5+/7+) 도달이 비현실적이며, 이들 스킬은 단일 결정·단일 활동 비교에 한정되어 multi-component topology가 부적합하다. 매핑 JSON에 `"tier3": "disabled-for-quick-profile"`로 명시.

### Open follow-ups (deferred)

- **v2.5.2**: 나머지 16개 스킬에 대한 v2-style `sample-dialogue.md` 작성. Tier 3 fallback decision rubric 정밀화 (`0 markers = Option D` → `≥2/3 markers required`로 dry-run 필드 데이터 수집 후 조정).
- **v2.6.0** (조건부): 만약 v2.5.1 dry-run에서 Tier 3 mechanisms이 실제 AI 응답에 거의 등장하지 않으면 retroactive하게 v2.5.1을 Tier 1+2-only로 재정의하고 Tier 3을 v2.6.0으로 minor bump.
- **v2.7.0** (옵션): 교사용 1-page cheat sheet (PDF + github.io 페이지).

### Migration

v2.5.0 → v2.5.1은 patch-level이라 별도 마이그레이션 작업 불필요. 설치 스크립트를 다시 실행하거나 `git pull` 후 사용 가능.

기존 v1.x로 설치한 사용자도 새 스크립트를 그대로 실행하면 됨. v2.0의 7-group 계층 + v2.5.1의 Readiness Gate v2가 함께 적용된다.

---

## v2.5.0 (이전)

7-group 폴더 계층 도입, 10개 workflow 정리, 첫 공개 릴리스. 자세한 내용은 `research-evaluation.md` 및 git log 참조.
