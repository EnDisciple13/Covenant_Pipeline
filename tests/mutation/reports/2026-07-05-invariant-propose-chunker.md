# Invariant Proposals: `covenant_pipeline/phases/chunker.py`

Executor: Composer 2.5 | `/invariant-propose` first exercise | Kill-matrix input: [2026-07-05-baseline.md](2026-07-05-baseline.md)

## Spec-derived list (Layer 1 notes only)

| # | class | statement | source note |
|---|-------|-----------|-------------|
| S1 | coverage / completeness | Every skeleton section yields non-empty `Raw_Text` | PE_Invariant_Suite `chunker-coverage-audit` |
| S2 | structural / partition | Chunks non-overlapping, monotone in (page, position); bboxes within page; text conserved in declared domain | PE_Invariant_Suite `chunker-partition` |
| S3 | provenance | Receipt metadata `(Article, Section)` rehydrates to the chunk that supplied extraction text | PE_Invariant_Suite `provenance-grounding` (via receipt join) |
| S4 | metamorphic | Formatting perturbations leave deterministic-prefix chunk output unchanged | PE_Invariant_Suite `metamorphic-stability` |
| S5 | functional law | TOC body-scan reconciles with skeleton; exclusion manifest records deliberate skips | PE_Invariant_Suite `chunker-coverage-audit` (full spec) |

## Code-derived list (repo only)

| # | class | statement | source module |
|---|-------|-----------|---------------|
| C1 | coverage | `run_extraction_engine` never emits empty `Raw_Text` for skeleton rows | `chunker.py` |
| C2 | structural | `Printed_End_Page` derived via `.shift(-1)` on skeleton ordering | `chunker.py` `calculate_printed_end_page` |
| C3 | structural | Header window search falls back to `abs_start` when section header not found (silent omission risk) | `chunker.py` `calculate_exact_boundaries` |
| C4 | structural | `build_page_spread_map` hardcodes `Absolute_Start_Page: 11` for printed page 1 | `chunker.py` |
| C5 | domain | TOC scan limited to first 20 pages — body sections in that window can duplicate skeleton rows | `chunker.py` `build_simplified_skeleton` |

## DIFF (top priority — user adjudicates)

| spec says | code says | implication |
|-----------|-----------|-------------|
| S2: monotone chunk ordering, no overlaps | C2: ordering follows TOC parse order only; reorder mutation M2 survives | **Undocumented axiom or suite gap** — need explicit monotonicity test on `(Absolute_Start_Page, position)` |
| S5: TOC body-scan reconciliation | C3: fallback path leaves section in skeleton with empty or wrong bounds | **Bug risk** — empty `Raw_Text` without warning is current behavior; coverage test catches but does not reconcile |
| S4: metamorphic stability under formatting | C5: TOC false-positive from body text in first 20 pages | **Spec/code tension** — metamorphic test must include TOC-page placement, not just whitespace |

## Ranked candidates

| rank | id (proposed) | class | statement | kills mutant? | cost | provenance |
|------|---------------|-------|-----------|---------------|------|------------|
| 1 | `chunker-partition` | structural / partition | Skeleton rows map to monotone non-overlapping absolute page ranges; reordering two chunks fails | **M2** (survivor) | medium — property test on spatial map CSV | spec S2 |
| 2 | `chunker-coverage-toc-reconcile` | coverage | Independent body scan for section headers matches TOC skeleton; mismatches reported | extends S5 | medium — second pass over PDF text | spec S5 |
| 3 | `chunker-bbox-in-page` | structural | All bbox coordinates lie within page media box | **M7** (survivor) | low — geometry check on spatial map | spec S2 |
| 4 | `chunker-toc-window-guard` | domain | Section headers on pages `< max_toc_pages` cannot duplicate skeleton unless listed in TOC block | C5 false-positive class | low — regression on synthetic PDF | code C5 |
| 5 | `chunker-spread-map-parameterized` | refinement | Page spread map derived from document footers without Hallador-specific constants | portability | high — golden + multiple PDFs | code C4 |

## Escalations

- **Sufficiency:** Stage 0 `chunker-coverage-audit` v0 (non-empty only) does not close S5 — escalate whether body-scan is Phase 1 or Phase 2 scope.
- **Diff row 1:** M2 survivor confirms `chunker-partition` is highest-value next invariant — rank 1 stands.
- **staging-parity:** from `Math_Application_Pipeline` mapping transfer — candidate cross-phase invariant; not chunker-local; user ratification pending separately.

**NOT written to any frontmatter — user ratifies selections manually.**
