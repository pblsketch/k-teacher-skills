# Third-Party Notices

This project's grounding providers and secondary-material system draw **ideas and
structural patterns** from the projects below. No third-party source text, rubric
CSV, or renderer code was copied; all implementations here are independent. Where a
project is reused at runtime (network calls), its own terms apply on its own servers.

---

## 1. anthropics/k12-teacher-skills — Apache-2.0 (patterns only, no code/text copied)

- Source: https://github.com/anthropics/k12-teacher-skills
- Reference commit reviewed: `7c03c83db8223b050b6569ffbe14cd94e229396e`
- License: Apache License 2.0

**What was borrowed:** ideas and structural patterns only — a single shared source of
truth feeding multiple documents, observable failure conditions (vs. value statements),
teacher/student facet separation, bidirectional teacher↔student alignment, rigor
preservation, misconception "what + why + teacher response", a hardest-case exit ticket,
and atomic/conditional evaluation criteria.

**What was NOT taken:** no SKILL.md prose, no rubric CSV files, no renderer/`render_documents.py`
code, and **no United States standards frameworks** (Common Core, NGSS, C3, or any state
standards). All Korean pedagogy references here are written independently against the
2022 개정 교육과정 context.

**Change notice (Apache-2.0 §4):** This is not a derivative distribution of Apache-2.0
files. Should any Apache-2.0 file ever be vendored, a copy of the Apache-2.0 license,
prominent change notices on modified files, retained copyright/attribution, and the
upstream `NOTICE` (Anthropic · Learning Commons) MUST be included, and Anthropic /
Learning Commons trademarks MUST NOT be used to imply endorsement or affiliation.

Apache License 2.0 summary: https://www.apache.org/licenses/LICENSE-2.0

---

## 2. schoolinfo-mcp (chrisryugj) — MIT (contract mirrored, no code copied)

- Source: https://github.com/chrisryugj/schoolinfo-mcp
- Reference commit reviewed: `d7c78a38bd613ff77ae4372f408def9a532d62be`
- License: MIT

**What was borrowed:** the tool contract shape (`find_school`, `get_evaluation_plan`,
local `parse_evaluation_file`), documented operational limits (`MAX_ALL_DOCS=20`,
50MB download cap, `MIN_USEFUL_MD=200`), and the remote-vs-local file-tool exposure
separation. `providers/school_evaluation/` is an independent Python client/adapter; no
schoolinfo TypeScript source was copied.

**Runtime use:** when configured, this adapter calls the hosted schoolinfo MCP
(`https://mcp.gomdori.app/school`). That service and the underlying 학교알리미 OpenAPI /
NEIS 개방포털 operate under their own terms; this repository ships no API keys and no
downloaded disclosure documents.

MIT License text: https://opensource.org/license/mit

---

## 3. National curriculum data (GEPAI backup) — owner-authorized MIT redistribution (dataset), provenance-unverified

The 2022-revision achievement-standard search index is a **local normalization** of the GEPAI
Supabase backup. The **raw** source is never committed. The **normalized public bundle** at
`providers/curriculum/bundle/2022/{normalized.jsonl,manifest.json}` is committed under an
**owner-authorized MIT** redistribution: the repository owner (`wnsdl` / Park Jun-il) is the
copyright holder and has authorized MIT redistribution of the normalized dataset.

- Bundle manifest: `license_id: "MIT"`, `license_authority: "owner-authorized-mit"`,
  `distribution: "owner-authorized-mit"`, `official_source: false`.
- Deterministic generation: the exact external source (`source_sha256:
  3e27351e78b76a01520f9dfb9b46dd6cc845ac7bab5dccbc0c7eeeff848aa91d`) is hash-verified BEFORE
  generation; the bundle carries no time-dependent release id and recounts hermetically to
  **3,274 records = 2,952 usable + 322 quarantined** (elementary 5~6 no-bracket set flagged as
  2015 mixed-revision).

**Distribution ≠ authority.** Owner-authorized MIT redistribution is a *copyright* fact only.
This is **owner-provided data, NOT an official Ministry (교육부 / NCIC) source**. Every record
ships provenance-unverified (`source.license_status: "unverified"`, `source.verified: false`,
`source.url: null`) and stays downstream **fail-closed** until independently verified via
`verify_standard()`. National-standard text becomes downstream-ready only after `:web`
verification against an official public source whose public terms are determinable.
