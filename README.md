# K-Teacher Skills(딸깍 레지스탕스 교사 스킬)

AI로 수업자료를 "딸깍" 생성하는 대신, 교사의 수업 의도·학생 맥락·평가 기준을 먼저 묻고 검증하게 만드는 한국 교사용 Skill Pack입니다.

## Target users

1차 대상은 Claude, ChatGPT, Codex 같은 AI 도구를 조금 써본 교사입니다.

특히 다음 상황에 있는 선생님을 돕습니다.

- 수업 준비가 어렵다.
- 새로운 교실 맥락에 맞게 수업을 바꾸기보다 과거 방식이나 교과서 흐름에 의존한다.
- AI에게 활동지나 수업안을 바로 만들게 하고 나중에 검토하다가 오히려 시간이 더 걸린다.
- 평가 기준, 학생 오개념, 수업 목표가 자료 생성 이후에야 드러난다.

## Philosophy

> 좋은 교사는 AI에게 "자료 만들어줘"라고 바로 말하지 않는다.  
> 좋은 교사는 AI에게 "내 수업 설계를 끝까지 질문해줘"라고 말한다.

이 Skill Pack은 다음 원칙을 따릅니다.

1. **자료 생성보다 질문이 먼저**
   - 수업안, 활동지, 평가지, 루브릭을 바로 만들지 않습니다.
   - 먼저 목표, 학생 맥락, 평가 증거, 예상 오개념을 확인합니다.

2. **평가 증거가 활동보다 먼저**
   - 학생이 무엇을 하면 배웠다고 볼 것인지 먼저 정합니다.
   - 활동은 그 증거가 나오도록 설계합니다.

3. **학생 개인정보를 요구하지 않음**
   - 실명, 민감정보, 실제 학생 사례 입력을 전제로 하지 않습니다.
   - 필요한 경우 익명화된 학급 수준의 맥락만 사용합니다.

4. **교사의 판단을 대체하지 않음**
   - AI는 질문하고, 정리하고, 대안을 제안합니다.
   - 최종 판단은 교사가 합니다.

5. **질문에도 종료 기준이 있음**
   - 질문을 많이 던지는 것이 목적이 아닙니다.
   - `references/interview-readiness.md`의 readiness gate로 더 물을지, 요약할지, 산출물로 넘어갈지 판단합니다.

## Migration to v2.0

v2.0부터 `skills/` 폴더는 7개 그룹(`entry/`, `lesson-design/`, `inquiry-pbl/`, `assessment/`, `individualization/`, `diagnostics/`, `ai-era/`)으로 계층화되었습니다. **개별 스킬의 내용(SKILL.md)은 변경되지 않았고**, 폴더 경로만 바뀝니다.

설치 스크립트(`install-claude.ps1`, `install-codex.ps1`)는 자동으로 새 계층을 walk하면서 기존처럼 `~/.claude/skills/<skill-name>/` 평면 구조로 복사합니다. **이미 v1.x로 설치한 사용자도 그냥 새 스크립트를 다시 실행하면 됩니다** (덮어쓰기). 수동 `cp -r skills/<skill> ~/.claude/skills/` 명령을 쓰던 경우만 새 경로(`skills/<group>/<skill>`)로 갱신하면 됩니다.

| v1.x 경로 | v2.0 경로 |
|-----------|-----------|
| `skills/grill-me-for-k-teacher/` | `skills/entry/grill-me-for-k-teacher/` |
| `skills/grill-with-curriculum/` | `skills/entry/grill-with-curriculum/` |
| `skills/k-teacher-workflow-router/` | `skills/entry/k-teacher-workflow-router/` |
| `skills/lesson-prototype/` | `skills/lesson-design/lesson-prototype/` |
| `skills/to-lesson-brief/` | `skills/lesson-design/to-lesson-brief/` |
| `skills/improve-lesson-architecture/` | `skills/lesson-design/improve-lesson-architecture/` |
| `skills/zoom-out-lesson/` | `skills/lesson-design/zoom-out-lesson/` |
| `skills/thinking-routine-selector/` | `skills/lesson-design/thinking-routine-selector/` |
| `skills/concept-based-inquiry-designer/` | `skills/inquiry-pbl/concept-based-inquiry-designer/` |
| `skills/pbl-design-coach/` | `skills/inquiry-pbl/pbl-design-coach/` |
| `skills/assessment-first-design/` | `skills/assessment/assessment-first-design/` |
| `skills/rubric-quality-guard/` | `skills/assessment/rubric-quality-guard/` |
| `skills/hinge-question-designer/` | `skills/assessment/hinge-question-designer/` |
| `skills/differentiate-lesson-pathways/` | `skills/individualization/differentiate-lesson-pathways/` |
| `skills/udl-barrier-remover/` | `skills/individualization/udl-barrier-remover/` |
| `skills/diagnose-lesson-failure/` | `skills/diagnostics/diagnose-lesson-failure/` |
| `skills/ai-resilient-assignment-redesign/` | `skills/ai-era/ai-resilient-assignment-redesign/` |

## Install as Claude Cowork / Claude Code plugin (v2.5.3+)

v2.5.3부터 K-Teacher Skills는 **Claude Cowork**와 **Claude Code** 양쪽 공식 plugin marketplace protocol을 지원합니다. Plugin으로 설치하면 자동 업데이트·namespace 격리·marketplace 배포가 가능합니다.

### Option 1 — Self-hosted GitHub marketplace (권장)

Claude Cowork 또는 Claude Code에서:

```text
/plugin marketplace add pblsketch/k-teacher-skills
/plugin install k-teacher-skills@k-teacher
```

설치 후 namespaced 호출:

```text
/k-teacher-skills:k-teacher 내일 중2 국어 활동지 만들어줘
/k-teacher-skills:new-lesson 단원 전체 처음부터 설계
/k-teacher-skills:assessment 수행평가 루브릭 개선
```

11개 workflow 명령 + 17개 skill 사용 가능 (`commands/` 폴더 + `skills/` 폴더).

### Option 2 — Local plugin (개발용)

저장소를 clone한 뒤:

```bash
claude --plugin-dir ./k-teacher-skills
```

설치 없이 한 세션에서만 로딩.

### Option 3 — Manual copy (Quick install 아래 참조)

Plugin marketplace를 안 쓰고 `~/.claude/skills/`에 직접 복사. 기존 사용자 호환.

---

## Quick install

Windows PowerShell에서 저장소 루트에서 실행합니다.

Codex에 설치:

```powershell
.\scripts\install-codex.ps1
```

Claude Code에 설치:

```powershell
.\scripts\install-claude.ps1
```

Google Antigravity에 설치 (글로벌):

```powershell
.\scripts\install-antigravity.ps1
```

(Antigravity는 워크스페이스 로컬 설치도 가능 — 임의 스킬 폴더를 `<workspace>/.agents/skills/`로 복사)

셋 다 설치:

```powershell
.\scripts\install-all.ps1
```

설치 후 첫 프롬프트는 router-first 방식으로 시작하는 것을 권장합니다.

```text
k-teacher-workflow-router로 내 요청을 분석하고 적절한 K-Teacher Skills workflow를 시작해줘.
```

## Skill pack manifest

`skill-pack.json`은 이 저장소를 하나의 Skill Pack으로 설명하는 파생 manifest입니다.
- entry skill: `k-teacher-workflow-router`
- skills: 17개
- workflows: 10개
- canonical new-lesson workflow: `new-lesson-package` → `workflows/new-lesson-design.md`
- install targets: Codex, Claude Code, Google Antigravity
- validation lane (8 validators): `python tests/validate_skill_pack.py && python tests/validate_workflow_envelope.py && python tests/validate_lesson_package_ir.py && python tests/validate_backport_marker.py && python tests/validate_renderer_parity.py && python tests/validate_release_gate_assets.py && python tests/validate_public_surface_regressions.py && python tests/validate_provider_skills.py`
- release-gate fixtures: `tests/golden/semantic-eval/valid.json`, `tests/golden/release-observability/valid.json`
- semantic eval은 `workflow-envelope`, `lesson-package-ir`, `kteacher-backport-marker`, `renderer-parity` deterministic validator가 모두 통과된 뒤에만 실행되며, deterministic 실패를 override하지 않습니다.
- semantic eval dimensions: `workflow-selection-quality`, `pedagogy-quality`, `rigor-preservation`, `usability-accessibility`, `post-verification-curriculum-alignment-quality`
- observability counters: `entry_mode_counts`, `resume_mode_counts`, `open_boundary_counts_by_category_output_class`, `blocked_output_reasons_by_class`, `backport_enforcement_failures_by_format`, `udl_vs_differentiated_workflow_entry_counts`, `public_surface_drift_failures` (README / `skill-pack.json` / `.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` 포함)

자세한 workflow 연결은 `WORKFLOWS.md`를 참고하세요.

## Curriculum & school-plan providers (grounding)

이 저장소는 provider/provenance/license/fail-closed **계약과 fixture**를 갖추고 있으며, `providers/`에 실제 조회 provider가 연결됩니다.

- **국가 2022 성취기준 provider** (`providers/curriculum`): GEPAI 백업을 정규화(대괄호·학년군 오기·혼합개정 격리)해 read-only 조회(`lookup_standard_by_code`/`search_standards`/`list_standards`/`verify_standard`)를 제공합니다. 정규화 공개 번들 `providers/curriculum/bundle/2022/{normalized.jsonl,manifest.json}`은 소스 SHA 검증 후 결정론적으로 생성한 **owner-authorized-MIT 재배포**(저작권 사실일 뿐 공식 출처 아님, `official_source:false`)이며, 원본 GEPAI 소스는 커밋하지 않습니다(gitignored `providers/_local/` 로컬 임포트만). 모든 레코드는 `source.license_status:unverified`·`verified:false`·`url:null`로 fail-closed이고, 국가 원문은 공식 NCIC/교육부 웹 검증(`:web`)으로만 downstream-ready가 됩니다.
- **학교 공시 평가계획 adapter** (`providers/school_evaluation`): [schoolinfo-mcp](https://github.com/chrisryugj/schoolinfo-mcp)(MIT) 계약(`find_school`/`get_evaluation_plan`/local `parse_evaluation_file`)을 독자 구현으로 미러링합니다. 학교·연도·학년·교과 pin, current→previous fallback은 **교사 승인 후에만**, PII는 mask-or-block(불가 시 차단), 원문은 anchor(URL·파일명·hash·조회시점·section/page/table)로만 참조합니다.
- **정렬/승격/격리** (`providers/alignment`): 평가계획 코드는 국가 성취기준과 정확 대조된 경우에만 **별도** 국가 `curriculum-record`로 additive 승격되고, 불일치·혼합개정은 격리됩니다.

### Authority hierarchy (권위 계층)

```
국가 2022 성취기준 provider  >  학교 공시 평가계획  >  교사 제공 자료/판단  >  inferred
```

학교 운영계획은 국가 성취기준을 override할 수 없습니다. **최종 적용 판단은 항상 교사**입니다. 자세한 QA·안전장치 설명은 설명 문서 <https://pblsketch.github.io/k-teacher-skills/qa-remediation-explained.html> 를 참고하세요.

### Provider-orchestration skills (별도 클래스, `skills/school-materials/`)

17개 Gate-v2 인터뷰/설계 스킬과 **분리된 provider-orchestration 클래스**(2개의 direct-entry 오케스트레이터 포함, 총 7개)입니다. `registry.provider_skills` + `skill-pack.json`의 `providerSkills`로 정식 등록되며(closed-world 검증 `tests/validate_provider_skills.py` + negative mutation regression), 17개 인터뷰 스킬의 registry·plugin projection은 불변입니다. 각 오케스트레이터는 자신의 의존 서브셋만 선언합니다.

- `school-evaluation-plan-to-materials` (오케스트레이터) — 학교 평가계획+국가 성취기준 → 학생·교사 2차 자료
- `school-plan-grounding` — 학교 공시 평가계획 pin·교사승인 fallback·PII mask-or-block
- `standard-alignment-verify` — 평가계획 코드 ↔ 국가 성취기준 대조/additive 승격/격리
- `assessment-evidence-builder` — 관찰 가능한 평가 증거·성공 기준·최난 출구표
- `secondary-material-builder` — single IR → 학생·교사·학부모 문서, HWPX/DOCX/HTML parity
- `material-rubric-qa` — 루브릭·양방향 정합성·rigor·PII 최종 QA
- `student-worksheet-builder` (오케스트레이터, direct-entry) — 단일 IR `content.blocks` 기반 학생 활동지: 물리성 게이트(분량·쓰기공간·페이지밀도·출구표·흑백안전·모둠중립), facet 블록 재귀, standalone quick-draft fail-closed. 의존: `standard-alignment-verify`·`secondary-material-builder`·`material-rubric-qa`.

### Constraints / license / provenance

- GEPAI **원본** 소스는 커밋하지 않습니다. **정규화 공개 번들**(`providers/curriculum/bundle/2022/`)만 owner-authorized-MIT로 커밋하며(소스 SHA 검증·결정론적 생성·hermetic 재집계 3274=2952 ok+322 quarantine), 이는 저작권 사실일 뿐 공식 출처가 아니고 레코드는 fail-closed로 유지됩니다. 학교 평가계획 원문·PII·인증키는 커밋하지 않습니다.
- 차용 출처·경계는 `THIRD_PARTY_NOTICES.md`에 기록합니다(anthropics Apache-2.0 아이디어 차용·비복사, schoolinfo MIT). 미국 표준 프레임워크는 사용하지 않습니다.
- provider/provenance/license 중 하나라도 비면 fail-closed. AR-1 `license_authority`로 공개 라이선스와 교사 승인 공시를 구분합니다.

### Roadmap

- 국가 성취기준 `:web` 라이브 검증 확대(현재 공식 소스 자동 매칭은 환경 의존), 학교 평가계획 라이브 조회(유효 인증키 필요).

## Included skills

### `grill-me-for-k-teacher`

수업/평가/자료를 만들기 전에 교사를 집요하게 인터뷰합니다. 목표는 교사와 AI가 수업 의도, 학생 맥락, 평가 기준에 대해 공유된 이해에 도달하는 것입니다.

### `grill-with-curriculum`

성취기준, 교육과정, 학급 맥락, 기존 자료를 기준으로 수업 설계를 검토합니다. 교육과정 문서가 있을 때 `grill-me-for-k-teacher`보다 더 강하게 작동합니다.

### `assessment-first-design`

개발자의 TDD를 교사용으로 전환한 스킬입니다. 활동지를 먼저 만들지 않고, 학습 증거와 루브릭을 먼저 정한 뒤 수업 활동을 설계합니다.

### `diagnose-lesson-failure`

수업이 잘 안 되었을 때 "학생들이 집중을 안 했다"로 끝내지 않고, 관찰 가능한 증거를 바탕으로 원인을 가설화하고 다음 차시 수정안을 만듭니다.

### `improve-lesson-architecture`

흩어진 PPT, 활동지, 퀴즈, 루브릭, 피드백 문장을 하나의 깊은 수업 모듈로 재구조화합니다.

### `zoom-out-lesson`

활동·자료·발문 하나에 매몰됐을 때, 단원·차시·성취기준·평가 흐름의 상위 맥락에서 다시 보게 합니다.

### `lesson-prototype`

완성 수업안 전에 2~3개의 작고 버릴 수 있는 활동안·발문·평가 장면을 만들어 비교합니다.

### `to-lesson-brief`

지금까지의 대화와 설계 맥락을 동료 공유나 다음 AI 작업에 넘길 수 있는 수업 설계 브리프로 정리합니다.

### `ai-resilient-assignment-redesign`

AI로 쉽게 대체되는 보고서, 활동지, 수행평가를 H→AI→H 구조로 재설계합니다. 프롬프트 로그, SHIFT 성찰지, AI 오용 대응, 학생용 안내문까지 포함합니다.

### `thinking-routine-selector`

학생 사고를 보이게 하는 Project Zero 사고 루틴을 수업 목표, 사고 목적, 학교급에 맞게 선택하고 발문·기록·평가 증거로 연결합니다.

### `concept-based-inquiry-designer`

성취기준과 단원을 핵심 개념, 일반화, 사실적·개념적·논쟁적 질문으로 재구성해 개념 기반 탐구 수업을 설계합니다.

### `differentiate-lesson-pathways`

같은 학습 목표를 유지하면서 기초·표준·심화 경로, 선택형 과제, 소그룹 지원, KSL/다국어 학습자 지원을 설계합니다.

### `rubric-quality-guard`

루브릭의 평가 준거, 수준 기술, 배점, 학생 친화성, 성취기준 정렬을 검토하고 개선합니다.

### `hinge-question-designer`

수업 중 학생 이해와 오개념을 빠르게 판별하는 힌지 질문, 형성평가 문항, 선택지별 교사 대응을 설계합니다.

### `pbl-design-coach`

실생활·지역사회 문제를 중심으로 PBL의 driving question, 학생 역할, 청중, 산출물, 과정 평가를 설계합니다.

### `udl-barrier-remover`

수업 활동, 자료, 평가에서 학생의 참여·표상·행동과 표현 장벽을 진단하고 UDL 기반 대안을 설계합니다.

### `k-teacher-workflow-router`

교사의 요청을 분석해 단일 스킬이 아니라 적절한 workflow를 선택하고 첫 스킬로 연결합니다. 교사가 스킬 이름을 명시하지 않아도 자동 진입점을 제공합니다.

## Workflow recipes

이 저장소는 개별 스킬뿐 아니라 스킬 체인도 제공합니다.

### `new-lesson-package`

```text
grill-me-for-k-teacher
→ assessment-first-design
→ lesson-prototype
→ to-lesson-brief
```

### Curriculum-grounded redesign

```text
grill-with-curriculum
→ zoom-out-lesson
→ assessment-first-design
→ improve-lesson-architecture
→ to-lesson-brief
```

### Lesson failure recovery

```text
diagnose-lesson-failure
→ zoom-out-lesson
→ lesson-prototype
→ to-lesson-brief
```

### Material architecture improvement

```text
improve-lesson-architecture
→ assessment-first-design
→ lesson-prototype
→ to-lesson-brief
```

### AI-resilient assignment redesign

```text
ai-resilient-assignment-redesign
→ assessment-first-design
→ to-lesson-brief
```

### Conceptual inquiry lesson

```text
grill-with-curriculum
→ concept-based-inquiry-designer
→ thinking-routine-selector
→ assessment-first-design
→ to-lesson-brief
```

### Differentiated lesson redesign

```text
diagnose-lesson-failure
→ udl-barrier-remover
→ differentiate-lesson-pathways
→ lesson-prototype
→ to-lesson-brief
```

### Assessment quality upgrade

```text
assessment-first-design
→ hinge-question-designer
→ rubric-quality-guard
→ to-lesson-brief
```

### PBL design

```text
zoom-out-lesson
→ pbl-design-coach
→ assessment-first-design
→ rubric-quality-guard
→ to-lesson-brief
```

### UDL accessible lesson redesign

```text
improve-lesson-architecture
→ udl-barrier-remover
→ lesson-prototype
→ to-lesson-brief
```

## Questioning style

교사에게 질문할 때는 기본적으로 선택지를 제공합니다.

```text
A. 선택지 1
B. 선택지 2
C. 선택지 3
D. 기타: 직접 적기
```

가능하면 추천 선택지도 함께 제시합니다. 자세한 규칙은 `references/questioning-style.md`를 참고하세요.

## Interview readiness

질문은 무한히 이어지지 않습니다.

`references/interview-readiness.md`는 다음을 정합니다.

- Quick / Standard / Deep readiness profile
- ambiguity score와 threshold
- 최대 질문 라운드
- 산출물 생성 전 mandatory stop gates
- 답변 후 재평가 방식

핵심 기준은 간단합니다.

- 수업 의도, 학생 맥락, 평가 증거, 오개념/장벽, 제약, 교사 판단 경계가 충분히 명확해야 합니다.
- mandatory gate가 비어 있으면 평균 점수가 낮아도 ready가 아닙니다.
- 최대 라운드에 도달하면 질문을 계속 늘리지 않고 `미확정`과 `교사 판단 필요`를 표시합니다.

### Readiness Gate v2 (v2.5.1+)

v2.5.1부터 readiness gate가 OMC/OMX `deep-interview` 메커니즘을 한국 교사 맥락에 맞춰 통합한 **Gate v2**로 확장되었습니다.

- **가중치 공식** — 단순 평균 대신 차원별 가중치 합산 (Greenfield: intent·0.30 + learner·0.20 + evidence·0.25 + misconception·0.10 + constraints·0.10 + boundaries·0.05)
- **Stage priority (Intent-first)** — Stage 1(Intent·Learner·Non-goals·Boundaries) → Stage 2(Evidence·Misconception·Success) → Stage 3(Brownfield curriculum grounding). 약한 stage가 있으면 다음 stage 질문 금지.
- **Mandatory gates 분리** — 비목표·결정경계·평가증거·개인정보·압박패스 5개를 weighted ambiguity와 별개 hard-gate로 운영
- **Pressure Ladder 4단계** — Evidence → Assumption → Boundary → Essence; 같은 thread에서 깊이 들어가지 차원 회전 금지
- **Fact routing 4 라벨 + 출처 등급(v2.5.2+)** — `[from-curriculum]` / `[from-textbook]` / `[from-class-context]` / `[from-teacher-judgment]`; 인터뷰는 마지막 라벨에만 사용. 사실 라벨은 `:provided` / `:web` / `:inferred` 3등급 suffix로 출처 명시; `:inferred`(AI 추정)에는 신뢰도 경고와 교사 확인 요청 prompt 강제
- **Round 0 토폴로지** — 1차시 / 단원 / 평가체계 / 학기흐름 / 다중 중 하나로 수업 단위 잠금
- **Ontology convergence** — 핵심 개념·평가 증거·학생 행동·자료 종류의 안정성 추적
- **Challenge modes** — Round 3+ Contrarian / Round 5+ Simplifier / Round 7+ Ontologist (각 1회)
- **Stateless transparency** — 영구 메모리 없음을 명시; resume은 transcript 기반

세션 첫 줄에 다음을 출력해 운영 상태를 투명하게 공개합니다.

```
Readiness profile: {Quick|Standard|Deep} | threshold: {0.30|0.20|0.15} | source: {explicit|router-inferred|skill-default}
```

자세한 사양은 `references/interview-readiness.md`를 참고하세요. v2.5.0의 모든 안전 가드(개인정보 비요구, 평가 증거 우선, mandatory gates)는 그대로 유지됩니다.

추가 공개 계약은 다음과 같습니다.

- provider 출력은 read-only input으로만 취급합니다. provider가 준 원문·응답은 `provider` record로만 들고 가며 `read_only_input: true`를 유지한 채 `author-ir`·`render` 단계에서 임의로 덮어써 provenance를 우회하지 않습니다.
- downstream-ready 결론은 summary 상태만으로 열지 않습니다. provider / provenance / license evidence를 record 단위로 보존하고, 각 record의 `provider` · `provenance_grade` · `source_reference` · `verification_evidence_type` · `verification_anchor` · `source_license.status` · `source_license.license_id` · `source_license.evidence_anchor` · `read_only_input`이 모두 맞아야 clearance 근거가 됩니다.
- provider / provenance / license 중 하나라도 비어 있거나 unresolved면 fail-closed로 유지합니다. 특히 `source_license.status`가 `verified-compatible`이 아니면 downstream-ready가 아닙니다.
- unresolved `:inferred`는 `to-lesson-brief` downstream-ready handoff, `author-ir`, `render`를 unblock하지 않습니다.
- `:provided`/`:web`로 provenance가 풀려도 `provider`, `source_license.status`, `source_license.license_id`, `source_license.evidence_anchor`, `read_only_input` evidence 없이는 downstream-ready가 아닙니다.
- mixed-revision 또는 source/version/trace가 정리되지 않은 provider record는 `quarantined`로 격리하며 downstream-ready handoff, `author-ir`, `render`를 열지 않습니다.

Tier 3 면제: `k-teacher-workflow-router`·`zoom-out-lesson`·`lesson-prototype`·`to-lesson-brief` 4개 Quick-profile 스킬은 Topology·Ontology·Challenge modes를 발동하지 않습니다.

## Which skill should I use?

처음에는 아래 기준으로 고르세요.

- **수업 아이디어는 있는데 아직 목표·학생 맥락·평가 기준이 흐릿하다**
  - `grill-me-for-k-teacher`

- **성취기준, 교육과정, 기존 평가계획, 활동지를 기준으로 수업을 점검하고 싶다**
  - `grill-with-curriculum`

- **활동지나 수행평가를 만들기 전에 무엇을 평가해야 하는지부터 정하고 싶다**
  - `assessment-first-design`

- **수업이 기대대로 되지 않았고 다음 차시를 어떻게 바꿀지 진단하고 싶다**
  - `diagnose-lesson-failure`

- **PPT, 활동지, 퀴즈, 루브릭이 흩어져 있고 수업 흐름을 깊게 재구조화하고 싶다**
  - `improve-lesson-architecture`

- **활동 하나가 좋아 보이지만 전체 수업 흐름에서 맞는지 모르겠다**
  - `zoom-out-lesson`

- **바로 완성안을 만들기보다 활동/발문/평가 후보를 비교해보고 싶다**
  - `lesson-prototype`

- **긴 대화를 동료 공유용 또는 다음 AI 작업용 수업 브리프로 정리하고 싶다**
  - `to-lesson-brief`

- **ChatGPT 복붙, AI 대응 과제, 보고서/수행평가 재설계가 고민이다**
  - `ai-resilient-assignment-redesign`

- **학생 사고를 보이게 하는 발문·사고 루틴이 필요하다**
  - `thinking-routine-selector`

- **단원을 핵심 개념, 일반화, 탐구 질문 중심으로 깊게 재구성하고 싶다**
  - `concept-based-inquiry-designer`

- **학생 수준 차이, 기초/심화 경로, 선택형 과제가 필요하다**
  - `differentiate-lesson-pathways`

- **루브릭의 준거와 수준 기술이 모호해서 검토하고 싶다**
  - `rubric-quality-guard`

- **수업 중 오개념을 확인하는 형성평가나 힌지 질문이 필요하다**
  - `hinge-question-designer`

- **PBL, 프로젝트, 지역 문제 기반 수업을 설계하고 싶다**
  - `pbl-design-coach`

- **UDL, 접근성, 참여/표상/표현 장벽을 낮추고 싶다**
  - `udl-barrier-remover`

- **어떤 스킬을 써야 할지 모르겠고, 요청에 맞는 흐름을 자동으로 고르고 싶다**
  - `k-teacher-workflow-router`

추천 흐름:

```text
grill-me-for-k-teacher
→ assessment-first-design
→ lesson-prototype
→ to-lesson-brief
```

성취기준이나 기존 자료가 있다면:

```text
grill-with-curriculum
→ assessment-first-design
→ improve-lesson-architecture
```

수업 후 성찰이라면:

```text
diagnose-lesson-failure
→ grill-me-for-k-teacher
→ assessment-first-design
```

아이디어 비교와 정리가 필요하다면:

```text
zoom-out-lesson
→ lesson-prototype
→ to-lesson-brief
```

AI 대응 과제 재설계라면:

```text
ai-resilient-assignment-redesign
→ assessment-first-design
→ to-lesson-brief
```

개념 기반 탐구라면:

```text
grill-with-curriculum
→ concept-based-inquiry-designer
→ thinking-routine-selector
→ assessment-first-design
```

평가 품질을 높이고 싶다면:

```text
assessment-first-design
→ hinge-question-designer
→ rubric-quality-guard
```

## Repository structure

```text
k-teacher-skills/
├─ README.md
├─ WORKFLOWS.md
├─ skill-pack.json
├─ LICENSE
├─ scripts/
│  ├─ install-codex.ps1
│  ├─ install-claude.ps1
│  └─ install-all.ps1
├─ skills/                                # v2.0: 7-group hierarchy
│  ├─ entry/                              # 진입점·인터뷰
│  │  ├─ k-teacher-workflow-router/
│  │  ├─ grill-me-for-k-teacher/
│  │  └─ grill-with-curriculum/
│  ├─ lesson-design/                      # 수업 설계
│  │  ├─ lesson-prototype/
│  │  ├─ to-lesson-brief/
│  │  ├─ improve-lesson-architecture/
│  │  ├─ zoom-out-lesson/
│  │  └─ thinking-routine-selector/
│  ├─ inquiry-pbl/                        # 탐구·프로젝트
│  │  ├─ concept-based-inquiry-designer/
│  │  └─ pbl-design-coach/
│  ├─ assessment/                         # 평가·루브릭
│  │  ├─ assessment-first-design/
│  │  ├─ rubric-quality-guard/
│  │  └─ hinge-question-designer/
│  ├─ individualization/                  # 개별화·접근성
│  │  ├─ differentiate-lesson-pathways/
│  │  └─ udl-barrier-remover/
│  ├─ diagnostics/                        # 진단
│  │  └─ diagnose-lesson-failure/
│  └─ ai-era/                             # AI 시대 과제
│     └─ ai-resilient-assignment-redesign/
├─ workflows/
│  ├─ new-lesson-design.md
│  ├─ curriculum-grounded-redesign.md
│  ├─ lesson-failure-recovery.md
│  ├─ material-architecture-improvement.md
│  ├─ ai-resilient-assignment-redesign.md
│  ├─ conceptual-inquiry-lesson.md
│  ├─ differentiated-lesson-redesign.md
│  ├─ assessment-quality-upgrade.md
│  ├─ pbl-design-workflow.md
│  └─ udl-accessible-lesson-redesign.md
├─ references/
│  ├─ questioning-style.md
│  ├─ interview-readiness.md
│  ├─ ai-assignment-templates.md
│  ├─ thinking-routines-matrix.md
│  ├─ concept-based-inquiry.md
│  ├─ differentiation-patterns.md
│  ├─ rubric-quality.md
│  ├─ hinge-question-design.md
│  ├─ pbl-design.md
│  └─ udl-barrier-check.md
└─ examples/
   ├─ classroom-context-template.md
   ├─ curriculum-context-template.md
   └─ lesson-brief-template.md
```

## Usage

### Claude

Claude Skills use folders containing `SKILL.md` files.

Option A — Claude Code local skills (권장: 설치 스크립트 사용):

```powershell
.\scripts\install-claude.ps1
```

수동으로 복사하려면 7개 그룹을 순회합니다:

```bash
mkdir -p ~/.claude/skills
cp -r skills/entry/k-teacher-workflow-router ~/.claude/skills/
cp -r skills/entry/grill-me-for-k-teacher ~/.claude/skills/
cp -r skills/entry/grill-with-curriculum ~/.claude/skills/
cp -r skills/lesson-design/lesson-prototype ~/.claude/skills/
cp -r skills/lesson-design/to-lesson-brief ~/.claude/skills/
cp -r skills/lesson-design/improve-lesson-architecture ~/.claude/skills/
cp -r skills/lesson-design/zoom-out-lesson ~/.claude/skills/
cp -r skills/lesson-design/thinking-routine-selector ~/.claude/skills/
cp -r skills/inquiry-pbl/concept-based-inquiry-designer ~/.claude/skills/
cp -r skills/inquiry-pbl/pbl-design-coach ~/.claude/skills/
cp -r skills/assessment/assessment-first-design ~/.claude/skills/
cp -r skills/assessment/rubric-quality-guard ~/.claude/skills/
cp -r skills/assessment/hinge-question-designer ~/.claude/skills/
cp -r skills/individualization/differentiate-lesson-pathways ~/.claude/skills/
cp -r skills/individualization/udl-barrier-remover ~/.claude/skills/
cp -r skills/diagnostics/diagnose-lesson-failure ~/.claude/skills/
cp -r skills/ai-era/ai-resilient-assignment-redesign ~/.claude/skills/
```

Option B — Claude.ai Skills:

1. Zip one skill folder, for example `skills/grill-me-for-k-teacher/`.
2. Upload the zip file in Claude's Skills interface.
3. Repeat for the other skills if needed.

If Claude does not automatically trigger a skill, mention the skill name directly:

```text
grill-me-for-k-teacher를 사용해서 이 수업 아이디어를 먼저 질문해줘.
```

### Codex

Codex skills also use `SKILL.md` files with YAML frontmatter.

Local install example (권장: 설치 스크립트 사용):

```powershell
.\scripts\install-codex.ps1
```

수동으로 복사하려면 7개 그룹을 순회합니다:

```bash
mkdir -p ~/.codex/skills
cp -r skills/entry/k-teacher-workflow-router ~/.codex/skills/
cp -r skills/entry/grill-me-for-k-teacher ~/.codex/skills/
cp -r skills/entry/grill-with-curriculum ~/.codex/skills/
cp -r skills/lesson-design/lesson-prototype ~/.codex/skills/
cp -r skills/lesson-design/to-lesson-brief ~/.codex/skills/
cp -r skills/lesson-design/improve-lesson-architecture ~/.codex/skills/
cp -r skills/lesson-design/zoom-out-lesson ~/.codex/skills/
cp -r skills/lesson-design/thinking-routine-selector ~/.codex/skills/
cp -r skills/inquiry-pbl/concept-based-inquiry-designer ~/.codex/skills/
cp -r skills/inquiry-pbl/pbl-design-coach ~/.codex/skills/
cp -r skills/assessment/assessment-first-design ~/.codex/skills/
cp -r skills/assessment/rubric-quality-guard ~/.codex/skills/
cp -r skills/assessment/hinge-question-designer ~/.codex/skills/
cp -r skills/individualization/differentiate-lesson-pathways ~/.codex/skills/
cp -r skills/individualization/udl-barrier-remover ~/.codex/skills/
cp -r skills/diagnostics/diagnose-lesson-failure ~/.codex/skills/
cp -r skills/ai-era/ai-resilient-assignment-redesign ~/.codex/skills/
```

Project-local usage:

Keep this repository in a Codex workspace and ask Codex to use a named skill.

```text
assessment-first-design 스킬로 이 수행평가를 활동보다 평가 증거부터 설계해줘.
```

## Example dialogues

Each skill includes a `examples/sample-dialogue.md` file. Read it when you want to see how the skill should behave before using it with real lesson planning.

## Suggested first prompt

```text
grill-me-for-k-teacher를 사용해서, 아래 수업 아이디어를 바로 자료로 만들지 말고 먼저 나를 질문해줘.

수업 아이디어:
- 과목:
- 학년:
- 단원:
- 하고 싶은 활동:
- 고민되는 점:
```

## Safety and privacy

이 저장소의 스킬은 1차 릴리스에서 다음을 하지 않습니다.

- LMS, Google Classroom, Class팅 등 외부 서비스 연동
- 학생 실명, 민감정보, 실제 학생 사례 수집
- 완성 수업안 자동 생성만을 목표로 하는 "딸깍" 워크플로우

## License

MIT
