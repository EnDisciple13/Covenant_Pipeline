<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/PE_Invariant_Suite.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

---
id: projects-covenant-platform-engineering-PE_Invariant_Suite
type: project_strategy
status: draft
dependencies:
  - math/platform-engineering/Math_Application_Pipeline.md
  - math/platform-engineering/Math_Containerization.md
  - meta/Layer4_TypeB_Auditing.md
  - meta/Invariant_Authorship.md
tags:
  - invariants
  - layer4
invariants:
  - id: provenance-grounding
    statement: "Every extracted field cites a source span that verifiably occurs in the cited chunk"
  - id: chunker-partition
    statement: "Chunks are non-overlapping and monotone in (page, position); every bbox lies within its page; the covered domain is explicitly declared, and chunk text conserves source text within that domain"
  - id: chunker-coverage-audit
    statement: "Every skeleton section yields non-empty extracted text; an independent body scan for section headers reconciles with the TOC skeleton (differences reported); an exclusion manifest records what was deliberately not covered"
  - id: router-rule-dispatch
    statement: "For each routing rule r: exactly one envelope is dispatched iff |S_r| = 1, else deterministic abstention; rule evaluations are independent and deterministic across runs; a chunk may serve multiple rules"
  - id: glossary-acyclic
    statement: "The term-definition dependency graph is a DAG; multi-hop resolution terminates within declared depth; all dangling references are detected, reported, and classified as excluded-domain (expected) or in-domain (defect)"
  - id: metamorphic-stability
    statement: "Whitespace reflow and page-break shifts leave deterministic-prefix outputs (chunk, route, glossary) unchanged; LLM-stage stability holds modulo declared stochasticity at temperature 0"
  - id: container-parity
    statement: "Pipeline output on a golden fixture inside the container equals output outside the container"
  - id: config-totality
    statement: "A container missing a required env var fails fast with a named error; it never starts on a silent default"
---
# PE Invariant Suite (Covenant Pipeline + Platform Layer)

> Applied inventory of Layer 4 invariants for the Covenant pipeline's **already-implemented** phases and the Docker platform layer. Theory and taxonomy: [Invariant_Authorship.md](../../../Notes/meta/Invariant_Authorship.md). Audit mechanisms: [Layer4_TypeB_Auditing.md](../../../Notes/meta/Layer4_TypeB_Auditing.md). Pipeline phase structure: [Math_Application_Pipeline.md](math/Math_Application_Pipeline.md); container formalism: [Math_Containerization.md](math/Math_Containerization.md).

## Enforcement status (as of 2026-07-03)

Partially enforced. **Existing:** Pydantic schemas at the LLM boundary (`covenant_pipeline/schemas/` — domain and cardinality invariants); an integrity-audit phase (`phases/audit.py`, cross-reference resolution over the compiled payload); an actor-critic validation agent. **Absent:** everything below — no property-based testing (no Hypothesis), no chunker/router invariant tests, no provenance grounding check, no container parity test.

## Pipeline invariants (implemented phases)

| # | Invariant id | Class | Statement | Target modules |
|---|--------------|-------|-----------|----------------|
| 1 | `provenance-grounding` | Provenance | Every extracted field cites a span that verifiably occurs in the cited chunk (substring/offset check) | `phases/extraction.py` + `schemas/` |
| 2 | `chunker-partition` | Structural (partition) | No overlaps, nothing invented; bboxes within page bounds; monotone ordering; covered domain explicitly declared, with text conservation inside it | `phases/chunker.py` |
| 3 | `chunker-coverage-audit` | Coverage / completeness | Every skeleton section yields **non-empty** `Raw_Text`; independent body scan for section headers reconciles with the TOC skeleton; exclusion manifest in `Document_Metadata` records what was deliberately skipped | `phases/chunker.py` |
| 4 | `router-rule-dispatch` | Functional law | Per **rule** $r$: dispatch exactly one envelope iff $\|S_r\| = 1$, else deterministic abstention; evaluations independent; a chunk may serve multiple rules (fiber product, not a partition — per [Math_Application_Pipeline.md](math/Math_Application_Pipeline.md) §5) | `phases/router.py` |
| 5 | `glossary-acyclic` | Topological | Definition graph is a DAG; bounded multi-hop depth; dangling references *detected, reported, and classified*: excluded-domain (expected) vs in-domain (defect) | `phases/glossary.py`, `phases/compiler.py` |
| 6 | `metamorphic-stability` | Metamorphic / equivariance | Formatting perturbations leave the deterministic prefix $P_{\text{det}}$ (chunk, route, glossary) unchanged; LLM-stage version holds modulo temperature-0 stochasticity — tests phases without knowing the right answer | `orchestrator.py` (`--skip-llm` prefix first) |

**Priority:** provenance grounding first. It converts "did the LLM hallucinate?" from vibes into a mechanical audit — the single most valuable invariant class for an LLM pipeline.

**Audit notes (2026-07-03):** invariants were restated after a Knowledge Tier 1 audit against [Math_Application_Pipeline.md](math/Math_Application_Pipeline.md) (original router phrasing contradicted §5's fiber-product semantics; closure and metamorphic phrasings were stronger than §§7–9 entail). Two Layer 0 decisions were then **resolved** (same day):

1. **TOC-driven partial coverage is confirmed design intent** — the older full-document-tiling idea is superseded. `chunker-partition` stays domain-scoped, and `chunker-coverage-audit` was added because partial coverage shifts the existential failure mode from noise to **silent omission** (a TOC regex miss, a window search that never matches a header — the extraction engine currently exports empty sections without warning). For a covenant tool, a silently missing covenant is worse than a hallucinated one: provenance grounding catches hallucination; only a coverage audit catches omission.
2. **Glossary closure remains detect-and-report** (soft-fail confirmed). Hard-fail would false-alarm on legitimate references into deliberately excluded content (e.g. "as set forth in Exhibit B"). Dangles are instead *classified*: excluded-domain (expected, informational) vs in-domain (genuine defect).

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

## First rep

Implement the **non-empty-extraction check** from `chunker-coverage-audit` first — it is the cheapest test in the inventory and guards the scariest failure (silent covenant omission). Then `provenance-grounding` (pipeline side) and `container-parity` (platform side). Then mutation drills: an agent deliberately drops a TOC section, reorders chunks, fabricates a citation span, or perturbs the container env; the suite must go red. Track kill rate per invariant.

## Related Notes

- [Invariant_Authorship.md](../../../Notes/meta/Invariant_Authorship.md) — theory, taxonomy, authorship split.
- [PE_Roadmap_M1.md](PE_Roadmap_M1.md) — platform-engineering phases; later phases inherit this suite.
- [Math_Application_Pipeline.md](math/Math_Application_Pipeline.md) — phase morphisms these invariants defend.
- [Math_Containerization.md](math/Math_Containerization.md) — container formalism behind the parity invariant.
