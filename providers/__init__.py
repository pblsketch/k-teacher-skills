"""K-Teacher read-only grounding providers.

Two authority-separated providers converge on the fail-closed provider/
provenance/license contract in schemas/lesson-package-ir.schema.json:

- curriculum  : national 2022 achievement standards (Tier 0, curriculum-record)
- school_evaluation : school public disclosure plans (Tier 1, curriculum-context)

Provider working data (GEPAI import, downloaded plans) is non-distributed and
lives under providers/_local/ (gitignored). Nothing here redistributes upstream
data or embeds PII.
"""
