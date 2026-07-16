# Independent QA Brief — K-Teacher Skills provider/materials build

**For:** a fresh, independent reviewer (e.g. Claude Opus 4.8) in a **new context**.
**Mandate:** READ-ONLY. Do **not** modify product files, run `git reset/restore/stash/checkout`,
normalize line endings, `git add .`, commit, or push. Verify claims against current repo state.
Treat the ~60 CRLF/EOL-only dirty WIP files as user work to preserve.

The implementing session (ralplan → ultragoal, run `019f68d6-…`) built a two-provider
grounding layer + secondary-material system across 9 vertical slices (VS0–VS7). This brief
lists every completion condition and exactly how to check it.

## How to run the whole gate

```sh
cd /mnt/e/github/k-teacher-skills
# 8-validator documented lane + the new provider/renderer/material validators
for v in validate_skill_pack validate_workflow_envelope validate_lesson_package_ir \
         validate_backport_marker validate_renderer_parity validate_release_gate_assets \
         validate_public_surface_regressions validate_provider_authority \
         validate_curriculum_provider validate_school_evaluation validate_alignment \
         validate_renderer_spike validate_materials validate_axisd_assets \
         validate_provider_observability validate_provider_skills; do
  python3 tests/$v.py || echo "FAIL $v"
done
python3 -m compileall -q tests providers renderers
```

All 16 should print PASS/exit 0. `compileall` should be clean.

## Completion conditions ↔ verification

| # | Condition | How to verify | Expected | Status |
|---|-----------|---------------|----------|--------|
| 1 | 9 durable goals | `gjc ultragoal status --json`; read `.gjc/_session-019f68d6-…/ultragoal/goals.json` + `ledger.jsonl` | 9 VS goals (G001–G009) all complete; G007's registration blocker (G010) resolved as a separate provider-skill class → G007 superseded | ✅ all complete (G010 registered the class; G007 superseded) |
| 2 | Real provider lookup | `python3 -c "import sys;sys.path.insert(0,'.');from providers.curriculum.importer import import_dataset;from providers.curriculum.provider import CurriculumProvider;import_dataset();p=CurriculumProvider('providers/_local/curriculum-2022/normalized.jsonl');print(p.lookup_standard_by_code('[9과17-01]',school_level='중학교',subject='과학').record['content'])"` | Prints the real 기권과 날씨 standard text | ✅ real |
| 3 | Real schoolinfo plan E2E | `python3` calling `providers.school_evaluation.adapter.SchoolEvaluationAdapter().get_evaluation_plan(...)`; also inspect `.gjc/…/ultragoal/artifacts/g003-e2e.json` | MCP connects + find_school works; keyed disclosure returns `유효하지 않은 apiKey` | ⚠️ **BLOCKED upstream** (invalid hosted key; adapter+masking proven on fixtures) |
| 4 | Teacher-approval fixture | `python3 tests/validate_materials.py` | Approval gate fail-closed; `tests/golden/materials/approval.json` (synthetic, no PII) | ✅ |
| 5 | Student + teacher materials | `python3 tests/validate_materials.py` | One IR → student(활동지/자기점검) + teacher(운영안/루브릭/체크리스트); facet separation + bidirectional alignment | ✅ |
| 6 | HWPX/DOCX/HTML semantic parity | `python3 tests/validate_renderer_spike.py` | Real 3-format files, markers at canonical locations, identical content_fingerprint — this proves **semantic parity/round-trip only, NOT Word/Hancom usability** | ✅ real files (parity) |
| 6b | Production open-safety & visual quality | `. .venv/bin/activate && python tests/validate_production_document_quality.py` (deps: `requirements-render.txt`) | DOCX reopened by python-docx (styles/settings/rels, A4, sections≥1, real tables); HWPX `validate_package` 0 ERROR + `HwpxDocument.open` reopen + text extract (residual masterPage/history/version fallback warnings are non-corrupting); HTML `@page A4`+`@media print`+self-contained. **MS Word / Hancom apps themselves are not executed here — final application open is stated unverified.** | ✅ library-consumer reopen |
| 7 | Semantic eval | `python3 tests/validate_provider_observability.py` + `python3 tests/validate_release_gate_assets.py` | 5 canonical dimensions; locked release-gate assets untouched/green | ✅ |
| 8 | README drift | `python3 tests/validate_public_surface_regressions.py` | Baseline green; mutating plugin/marketplace/registry fails closed | ✅ |
| 9 | Full validator/compileall green | the loop above | 16 PASS + compileall clean | ✅ |
| 10 | Scope review | `git diff --ignore-space-at-eol --numstat \| awk '$1!=0\|\|$2!=0'` | Exactly 9 files: .gitignore, README.md, schemas ×3 (lesson-package-ir, workflow-envelope, routing-gate-registry), skill-pack.json, registry/routing-gate-registry.json, validate_lesson_package_ir.py, validate_skill_pack.py | ✅ |
| 11 | Residual blocker ledger | this file's Residuals section + `.gjc/…/ultragoal/ledger.jsonl` | residuals recorded, not hidden | ✅ |

## Safety invariants to independently verify

- **No GEPAI data committed:** `git check-ignore providers/_local/curriculum-2022/normalized.jsonl` → ignored; `git ls-files providers/_local` → empty.
- **No PII / no keys committed:** grep the tracked additions; `tests/golden/school-evaluation/*` and `tests/golden/materials/approval.json` are synthetic (note "합성 예시 / 실데이터 아님").
- **EOL WIP preserved:** `git diff --ignore-space-at-eol --numstat | awk '$1!=0||$2!=0' | wc -l` == 9 (matches condition #10; the other ~60 modified files are EOL-only).
- **Authority separation:** confirm `providers/alignment` emits a separate national `curriculum-record` and never mutates the school `curriculum-context` (INV-1) — see `tests/validate_alignment.py`.
- **Fail-closed:** unverified provenance/license, quarantine, unmasked PII, or missing teacher approval must block downstream-ready (validators cover each).
- **Attribution:** `THIRD_PARTY_NOTICES.md` — anthropics Apache-2.0 (ideas only, no code/text copied, change-notice clause), schoolinfo MIT; no US standard frameworks in `references/subject/*`.

## Residuals / known blockers (verify they are honestly recorded, not faked)

1. **National `:web` live verification** (G002): official NCIC/교육부 source auto-match not achievable in this sandbox (portals JS-gated; search engines unindexed for the text). The `:web` overlay path is implemented + offline-tested; the pilot record correctly stays fail-closed. Manual fallback: supply an official 고시 URL to `web_verify.verify_via_web`. Evidence: `artifacts/g002-e2e.json`.
2. **Live schoolinfo disclosure fetch** (G003): hosted MCP's schoolinfo OpenAPI key is invalid; no local key. Adapter live path implemented; masking/limits/fallback proven on fixtures. Manual fallback: valid `SCHOOLINFO_API_KEY` or teacher-local `parse_evaluation_file`. Evidence: `artifacts/g003-e2e.json`.
3. **Axis D skill registration** (G007 → G010, RESOLVED): the 6 `skills/school-materials/*` skills are registered as a **separate closed-world `provider_skills` class** (maintainer-approved architecture), NOT forced into the 17-skill Gate-v2 interview projection. Contract in `registry.provider_skills` (schema-extended) + `skill-pack.json` `providerSkills` + README; enforced by `tests/validate_provider_skills.py` (closed-world triad + 5 negative mutation regressions). The 17 interview skills, `registry.skills`, `repo_facts.skill_count`, and plugin/marketplace projections are provably unchanged. Verify: `python3 tests/validate_provider_skills.py`.
4. **New observability counters** are shipped as an **additive** fixture (`tests/golden/provider-observability/valid.json`) rather than merged into the locked 7-counter release-gate contract, to keep release-gate assets green. Merging them into the release-gate contract is a follow-up closed-world change.

## Adversarial angles worth probing

- Try to make the curriculum provider return a quarantined record as downstream-ready (should be impossible).
- Try a school plan with a bare teacher name in a `담당교사` table column (should block render).
- Try to get `verify_standard` to report downstream_ready without verified provenance+license (should stay False).
- Tamper a rendered file's content and re-run parity (should fail).
- Confirm a valid teacher approval cannot pass a facet-violating IR.
