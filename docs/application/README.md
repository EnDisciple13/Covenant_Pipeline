<!-- MIRROR: auto-synced from notes/projects/covenant/application/README.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

---
id: projects-covenant-application-README
type: project_strategy
status: draft
dependencies:
  - projects/covenant/Covenant_Problem_and_Motivation.md
  - projects/covenant/application/Pipeline_Invariants.md
tags: [covenant, application, strategy-index]
invariants: []
---
# Covenant Extraction Pipeline — Application Strategy (`M0`)

> **Rule of Thumb:** Keep application data schemas, Pydantic contracts, and extraction invariants cleanly separated from container and infrastructure roadmaps.

This directory houses the `Milestone 0` (`M0`) strategy documentation for the Covenant Extraction Pipeline (`covenant_pipeline`). While `platform-engineering/` governs how the system is containerized (`M1`) and hosted (`M2`), this directory governs *what* the system extracts, how neuro-symbolic contracts validate unstructured legal text, and how extracted invariants feed downstream headroom calculations.

## Strategy Documents (Canonical in Notes)

| Document | Focus | Mirror (`covenant_pipeline`) |
| :--- | :--- | :--- |
| **[Covenant_Problem_and_Motivation.md](../Covenant_Problem_and_Motivation.md)** | Overarching M0 domain problem, Feynman matrix bridges, neuro-symbolic vision | `docs/Covenant_Problem_and_Motivation.md` |
| **[Pipeline_Invariants.md](Pipeline_Invariants.md)** | Pre-model Pydantic schemas, OCR/LLM boundaries, deterministic extraction checks | `docs/application/Pipeline_Invariants.md` |

## Related Meta & Domain Notes
- [../../Problem_Matrix.md](../../../Notes/projects/Problem_Matrix.md) — Feynman problems #1, #2, #3.
- [../platform-engineering/README.md](../platform-engineering/README.md) — M1 & M2 infrastructure roadmaps.
