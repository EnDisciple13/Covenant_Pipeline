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

> **Rule of Thumb:** Check the motivation column's tier before leaning on a row's math framing — `heuristic` means scaffold, and the operational driver is the real justification.

Containerization is a structure-preserving map; the master invariant is faithfulness of that functor. The **Motivation** column locates each invariant's origin — a graded mapping (with tier), a taxonomy class, or an operational driver — without restating the math; full derivations live with the math notes.

| # | Invariant id | Class | Statement | Motivation (source · tier) |
|---|--------------|-------|-----------|----------------------------|
| 7 | `container-parity` | Refinement | Golden-fixture run inside container == outside. One test catches env drift, dependency skew, and path bugs simultaneously | [`container-context-collapse`](math/Math_Notes_Platform_Engineer.md) (tight — its transfer claim names this test); the CCC exponential story ([`container-exponential-object`](math/Math_Containerization.md)) is heuristic scaffold only |
| 8 | `config-totality` | Functional law (totality) | Missing required env var ⇒ fail fast with named error; never start on a silent default | Dependency-product framing in [Math_Containerization.md](math/Math_Containerization.md) (heuristic scaffold); operational driver: a silent default is a latent misconfiguration |
| 9 | — (candidate) | Contract inhabitation | Declared ports listening; healthcheck returns schema-valid response | [`eval-generality-interface`](math/Math_Containerization.md) (tight — platform sees only the OCI interface) |
| 10 | — (candidate) | Reproducibility | Base images pinned by digest; dependencies locked | `image-immutability` invariant ([Math_Notes_Platform_Engineer.md](math/Math_Notes_Platform_Engineer.md)): digests immutable, tags mutable pointers |
| 11 | — (candidate) | Topological | Compose dependency graph acyclic; rerun on same mounted volume reproduces artifacts | Topological class ([Invariant_Authorship.md](../../../Notes/meta/rigor/Invariant_Authorship.md) §III); no dedicated mapping yet |

Candidates 9–11 graduate to frontmatter `invariants:` entries when the platform-engineering roadmap phases that own them are implemented.

## Related Notes

- [Invariant_Authorship.md](../../../Notes/meta/rigor/Invariant_Authorship.md) — theory, taxonomy, authorship split.
- [PE_Roadmap_M1.md](PE_Roadmap_M1.md) — platform-engineering phases; later phases inherit these invariants.
- [Math_Containerization.md](math/Math_Containerization.md) — container formalism behind the parity invariant.
- [Pipeline_Invariants.md](../application/Pipeline_Invariants.md) — extraction pipeline invariants.
