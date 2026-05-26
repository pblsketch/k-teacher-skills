# K-Teacher Skills

AI로 수업자료를 "딸깍" 생성하는 대신, 교사의 수업 의도·학생 맥락·평가 기준을 먼저 묻고 검증하게 만드는 한국 교사용 Skill Pack입니다.

이 저장소는 Matt Pocock의 개발자용 agent skills 철학을 교사 맥락으로 전환합니다. 핵심은 자료를 빨리 뽑는 것이 아니라, 수업과 평가가 무너지기 쉬운 지점을 구조화하는 것입니다.

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

### `k-teacher-workflow-router`

교사의 요청을 분석해 단일 스킬이 아니라 적절한 workflow를 선택하고 첫 스킬로 연결합니다. 교사가 스킬 이름을 명시하지 않아도 자동 진입점을 제공합니다.

## Workflow recipes

이 저장소는 개별 스킬뿐 아니라 스킬 체인도 제공합니다.

### New lesson design

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

- **어떤 스킬을 써야 할지 모르겠고, 요청에 맞는 흐름을 자동으로 고르고 싶다**
  - `k-teacher-workflow-router`

추천 흐름:

```text
grill-me-for-k-teacher
→ assessment-first-design
→ improve-lesson-architecture
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

## Repository structure

```text
k-teacher-skills/
├─ README.md
├─ LICENSE
├─ skills/
│  ├─ grill-me-for-k-teacher/
│  │  └─ SKILL.md
│  ├─ grill-with-curriculum/
│  │  └─ SKILL.md
│  ├─ assessment-first-design/
│  │  └─ SKILL.md
│  ├─ diagnose-lesson-failure/
│  │  └─ SKILL.md
│  ├─ improve-lesson-architecture/
│  │  └─ SKILL.md
│  ├─ zoom-out-lesson/
│  │  └─ SKILL.md
│  ├─ lesson-prototype/
│  │  └─ SKILL.md
│  ├─ to-lesson-brief/
│  │  └─ SKILL.md
│  ├─ ai-resilient-assignment-redesign/
│  │  └─ SKILL.md
│  └─ k-teacher-workflow-router/
│     └─ SKILL.md
├─ workflows/
│  ├─ new-lesson-design.md
│  ├─ curriculum-grounded-redesign.md
│  ├─ lesson-failure-recovery.md
│  ├─ material-architecture-improvement.md
│  └─ ai-resilient-assignment-redesign.md
├─ references/
│  ├─ questioning-style.md
│  ├─ interview-readiness.md
│  └─ ai-assignment-templates.md
└─ examples/
   ├─ classroom-context-template.md
   ├─ curriculum-context-template.md
   └─ lesson-brief-template.md
```

## Usage

### Claude

Claude Skills use folders containing `SKILL.md` files.

Option A — Claude Code local skills:

```bash
mkdir -p ~/.claude/skills
cp -r skills/grill-me-for-k-teacher ~/.claude/skills/
cp -r skills/grill-with-curriculum ~/.claude/skills/
cp -r skills/assessment-first-design ~/.claude/skills/
cp -r skills/diagnose-lesson-failure ~/.claude/skills/
cp -r skills/improve-lesson-architecture ~/.claude/skills/
cp -r skills/zoom-out-lesson ~/.claude/skills/
cp -r skills/lesson-prototype ~/.claude/skills/
cp -r skills/to-lesson-brief ~/.claude/skills/
cp -r skills/ai-resilient-assignment-redesign ~/.claude/skills/
cp -r skills/k-teacher-workflow-router ~/.claude/skills/
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

Local install example:

```bash
mkdir -p ~/.codex/skills
cp -r skills/grill-me-for-k-teacher ~/.codex/skills/
cp -r skills/grill-with-curriculum ~/.codex/skills/
cp -r skills/assessment-first-design ~/.codex/skills/
cp -r skills/diagnose-lesson-failure ~/.codex/skills/
cp -r skills/improve-lesson-architecture ~/.codex/skills/
cp -r skills/zoom-out-lesson ~/.codex/skills/
cp -r skills/lesson-prototype ~/.codex/skills/
cp -r skills/to-lesson-brief ~/.codex/skills/
cp -r skills/ai-resilient-assignment-redesign ~/.codex/skills/
cp -r skills/k-teacher-workflow-router ~/.codex/skills/
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
