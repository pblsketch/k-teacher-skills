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
│  └─ improve-lesson-architecture/
│     └─ SKILL.md
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
