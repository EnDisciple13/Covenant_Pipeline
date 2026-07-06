# Covenant mutation drill — property tests (2026-07-06)

Executor: Composer | Post-implementation anchor: Hypothesis property suite in `tests/invariants/`

## Preconditions

- `py -m pytest tests/invariants/ -q` → 25 passed, 1 skipped, 1 xfailed (whitespace-only `GEMINI_API_KEY` — implementation defect per spec P4)
- Drill driver: `tests/mutation/run_property_drill.py` (M2/M5/M6/M7 focus)

## Kill matrix (M2/M5/M6/M7 — mandatory exit)

| Mutant | Applied cleanly? | Invariants red | Killed? | Notes |
|--------|------------------|----------------|---------|-------|
| M2 Reorder chunks | Y | `chunker-partition` | **Y** | Single-row golden fixture: start-page skew; 2-row oracle class test |
| M5 Circular glossary | Y | `glossary-acyclic` | **Y** | Injected MutA↔MutB cycle into glossary output |
| M6 Silent env default | Y | `config-totality` | **Y** | Silent default in `get_client()` |
| M7 Bbox outside page | Y | `chunker-partition` | **Y** | `Absolute_End_Page = 99999` |

**Exit condition: SATISFIED** — M2, M5, M6, M7 dead.

## Full v0 matrix (unchanged baseline for M1/M3/M4/M8)

| Mutant | Killed? | Killer |
|--------|---------|--------|
| M1 Drop TOC section | Y | `chunker-coverage-audit` |
| M3 Fabricated citation span | Y | `provenance-grounding` |
| M4 Numeric → string | N/A | No compile-stage property yet |
| M8 Wrong receipt section | Y | `provenance-grounding` |

## Spec defects noted

- **config-totality P4:** whitespace-only `GEMINI_API_KEY` accepted (xfail test documents gap).

## Regression

Re-run after suite or mutation list changes. Record in `tests/mutation/reports/`.
