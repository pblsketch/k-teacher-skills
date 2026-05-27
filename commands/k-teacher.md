---
description: K-Teacher Skills 진입점 — 교사 요청을 분석해 적절한 workflow와 첫 스킬로 라우팅. 어떤 스킬을 써야 할지 모를 때 이 명령을 먼저 부른다.
---

# K-Teacher Skills router

이 명령은 `skills/entry/k-teacher-workflow-router/SKILL.md`를 그대로 따른다. router는 사용자 요청을 분석해 10개 workflow 중 하나를 선택하고 첫 스킬로 연결한다.

## Dispatch

1. `skills/entry/k-teacher-workflow-router/SKILL.md`를 로딩한다. plugin root가 직접 접근 불가능하면 `CLAUDE_PLUGIN_ROOT` 또는 설치된 k-teacher-skills 디렉토리에서 찾는다.
2. SKILL.md 지시를 그대로 따라 실행하되, **첫 줄에 Readiness Gate v2 banner**를 출력한다:
   ```
   Readiness profile: {Quick|Standard|Deep} | threshold: {0.30|0.20|0.15} | source: {explicit|router-inferred|skill-default}
   ```
3. 사용자 요청:
   ```
   $ARGUMENTS
   ```
4. Readiness Gate v2(`references/interview-readiness.md`) + provenance grading(§7 v2.5.2+)을 매 라운드 적용.
5. 모호하면 객관식 선택지로 요청 유형을 좁힌다(`questioning-style.md`).

## Related

- `references/interview-readiness.md` — Gate v2 SSOT
- `WORKFLOWS.md` — 10 workflow chain index
- `tests/readiness_gate_v2_mapping.json` — 17 skill × (profile, stage, labels) 매핑
