<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/PE_Infrastructure_Invariants.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

---
id: projects-covenant-platform-engineering-PE_Infrastructure_Invariants
type: project_strategy
status: draft
dependencies:
  - math/platform-engineering/Math_Containerization.md
  - meta/rigor/Invariant_Authorship.md
  - meta/verification/Layer4_TypeB_Auditing.md
tags:
  - invariants
  - layer4
invariants:
  - id: container-parity
    statement: "Pipeline output on a golden fixture inside the container equals output outside the container"
  - id: config-totality
    statement: "A container missing a required env var fails fast with a named error; it never starts on a silent default"
---
# Platform Infrastructure Invariants (Docker Layer)

> Applied inventory of Layer 4 invariants for the Covenant pipeline's Docker platform layer. Theory and taxonomy: [Invariant_Authorship.md](../../../Notes/meta/rigor/Invariant_Authorship.md). Audit mechanisms: [Layer4_TypeB_Auditing.md](../../../Notes/meta/verification/Layer4_TypeB_Auditing.md). Container formalism: [Math_Containerization.md](math/Math_Containerization.md).

## Enforcement status (as of 2026-07-06)

**Hypothesis property suite implemented** in `covenant_pipeline/tests/invariants/` (pytest + hypothesis). **Named tests:** `config-totality`, `container-parity`; legacy Stage 0 anchors retained. **Mutation drill 2026-07-06:** M2/M5/M6/M7 killed (property-tests report). M1/M3/M8 class remain killed.

**Spec defects (reported, not patched ad hoc):** whitespace-only `GEMINI_API_KEY` accepted (`config-totality` P4 xfail).

## Platform invariants (Docker layer)

Containerization is a structure-preserving map; the master invariant is faithfulness of that functor:

| # | Invariant id | Class | Statement |
|---|--------------|-------|-----------|
| 7 | `container-parity` | Refinement | Golden-fixture run inside container == outside. One test catches env drift, dependency skew, and path bugs simultaneously |
| 8 | `config-totality` | Functional law (totality) | Missing required env var ⇒ fail fast with named error; never start on a silent default |
| 9 | — (candidate) | Contract inhabitation | Declared ports listening; healthcheck returns schema-valid response |
| 10 | — (candidate) | Reproducibility | Base images pinned by digest; dependencies locked |
| 11 | — (candidate) | Topological | Compose dependency graph acyclic; rerun on same mounted volume reproduces artifacts |

Candidates 9–11 graduate to frontmatter `invariants:` entries when the platform-engineering roadmap phases that own them are implemented.

## Related Notes

- [Invariant_Authorship.md](../../../Notes/meta/rigor/Invariant_Authorship.md) — theory, taxonomy, authorship split.
- [PE_Roadmap_M1.md](PE_Roadmap_M1.md) — platform-engineering phases; later phases inherit these invariants.
- [Math_Containerization.md](math/Math_Containerization.md) — container formalism behind the parity invariant.
- [Pipeline_Invariants.md](../application/Pipeline_Invariants.md) — extraction pipeline invariants.
