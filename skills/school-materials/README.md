# School-materials skills (Axis D — provider/orchestration lane)

These are **provider/orchestration** skills, distinct from the 17 Gate-v2 interview/design
skills. They turn a real school evaluation plan + national 2022 achievement standards into
teacher/student secondary materials, grounded in the `providers/` modules:

- `providers/curriculum` — national 2022 standard provider (Tier 0)
- `providers/school_evaluation` — school disclosure plan adapter + PII mask-or-block (Tier 1)
- `providers/alignment` — school↔national alignment / promotion / quarantine
- `providers/materials` — single-IR secondary-material builder + teacher-approval gate
- `renderers/` — single canonical IR → HWPX/DOCX/HTML with parity

Authority order (never inverted): 국가 2022 성취기준 > 학교 공시 평가계획 > 교사 자료/판단 > inferred.
Final application judgment is always the teacher.

> Registration note: these skills are authored artifacts. Wiring them into the closed-world
> 17-skill routing-gate registry projection (`registry/routing-gate-registry.json`,
> `.claude-plugin/*`, `skill-pack.json`) is a separate, reviewed registry migration
> (see the run's residual-blocker ledger) so the existing green validator suite stays green.

Skills:
- `school-evaluation-plan-to-materials` (orchestrator)
- `school-plan-grounding`
- `standard-alignment-verify`
- `assessment-evidence-builder`
- `secondary-material-builder`
- `material-rubric-qa`
- `student-worksheet-builder` (orchestrator, direct-entry) — 단일 IR `content.blocks` 학생 활동지: 물리성 게이트·facet 블록 재귀·quick-draft fail-closed
- `individualized-material-package-builder` (orchestrator, direct-entry) — 개별화 자료 패키지: 교사 운영안 1 + 학생 Group A/B/C 활동지 3, 단일 IR·12개 렌더, 공통 계약 불변·진단어 격리·rigor 유지
