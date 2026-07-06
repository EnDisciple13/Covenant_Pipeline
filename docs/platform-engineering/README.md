<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/README.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

---
id: projects-covenant-platform-engineering-README
type: project_strategy
status: draft
dependencies:
tags: []
invariants: []
---
# Platform Engineering Documentation

Canonical PE strategy docs for the Covenant Extraction Pipeline. Mirrors are
auto-synced into `covenant_pipeline/docs/platform-engineering/` by
`scripts/sync_project_docs.py`. Edit files here in the Notes repo, then run
`python scripts/sync_project_docs.py --write` (Windows: `py scripts/sync_project_docs.py --write`).

## Domain scope (decision record, 2026-07-03)

`platform-engineering` is the **umbrella strategy domain** for the entire Covenant project — application-layer strategy (the CA pipeline itself) and platform-layer strategy both mirror here. In milestone terms: the application layer is effectively **M0**, the current containerization/deployment work is **M1**, and true platform engineering (the IDP generalization) is **M2**.

This is tracked naming debt, deliberately deferred — not an accident. The volume of application-layer strategy (currently one note, [PE_Invariant_Suite.md](PE_Invariant_Suite.md), which already separates pipeline vs platform invariants internally) does not yet justify a second domain. **Revisit when M2 work begins:** add a second mirror group for an application domain in `registry.yaml` (mirror `pairs` support arbitrary paths; only the singular `strategy_domain` label needs extending) and move the pipeline half of the invariant suite into it.

## Strategy docs (canonical in Notes)

| Document | Local | GitHub |
|----------|-------|--------|
| M1 hub roadmap | [PE_Roadmap_M1.md](PE_Roadmap_M1.md) | [PE_Roadmap_M1.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/platform-engineering/PE_Roadmap_M1.md) |
| M2 IDP vision | [PE_Roadmap_M2.md](PE_Roadmap_M2.md) | [PE_Roadmap_M2.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/platform-engineering/PE_Roadmap_M2.md) |
| Phase 1: Local containerization blueprint | [blueprints/PE_RM_Phase1.md](blueprints/PE_RM_Phase1.md) | [PE_RM_Phase1.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/platform-engineering/blueprints/PE_RM_Phase1.md) |
| Phase 2: Cloud topology blueprint | [blueprints/PE_RM_Phase2.md](blueprints/PE_RM_Phase2.md) | [PE_RM_Phase2.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/platform-engineering/blueprints/PE_RM_Phase2.md) |
| Phase 3: Terraform blueprint | [blueprints/PE_RM_Phase3.md](blueprints/PE_RM_Phase3.md) | [PE_RM_Phase3.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/platform-engineering/blueprints/PE_RM_Phase3.md) |
| Phase 4: CI/CD blueprint | [blueprints/PE_RM_Phase4.md](blueprints/PE_RM_Phase4.md) | [PE_RM_Phase4.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/platform-engineering/blueprints/PE_RM_Phase4.md) |
| Invariant suite (pipeline + Docker) | [PE_Invariant_Suite.md](PE_Invariant_Suite.md) | [PE_Invariant_Suite.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/platform-engineering/PE_Invariant_Suite.md) |
| Property test specs (Hypothesis) | [blueprints/PE_Property_Test_Specs.md](blueprints/PE_Property_Test_Specs.md) | [PE_Property_Test_Specs.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/platform-engineering/blueprints/PE_Property_Test_Specs.md) |

## Math (canonical in Notes, mirrored to covenant_pipeline)

Edit in **Notes** `math/platform-engineering/`. Mirrors land in `covenant_pipeline/docs/platform-engineering/math/`.

| Document | Canonical (Notes) | Mirror (covenant_pipeline) |
|----------|-------------------|----------------------------|
| Math index | [math/README.md](../../../Notes/math/README.md) | — (Notes-only index) |
| [Math_Containerization.md](math/Math_Containerization.md) | [GitHub](https://github.com/endisciple13/notes/blob/main/math/platform-engineering/Math_Containerization.md) | [math/Math_Containerization.md](https://github.com/endisciple13/covenant_pipeline/blob/main/docs/platform-engineering/math/Math_Containerization.md) |
| [Math_Notes_Platform_Engineer.md](math/Math_Notes_Platform_Engineer.md) | [GitHub](https://github.com/endisciple13/notes/blob/main/math/platform-engineering/Math_Notes_Platform_Engineer.md) | [math/Math_Notes_Platform_Engineer.md](https://github.com/endisciple13/covenant_pipeline/blob/main/docs/platform-engineering/math/Math_Notes_Platform_Engineer.md) |
| [Math_Application_Pipeline.md](math/Math_Application_Pipeline.md) | [GitHub](https://github.com/endisciple13/notes/blob/main/math/platform-engineering/Math_Application_Pipeline.md) | [math/Math_Application_Pipeline.md](https://github.com/endisciple13/covenant_pipeline/blob/main/docs/platform-engineering/math/Math_Application_Pipeline.md) |

## Phase status (navigation aid)

| Phase | Status | Implementation doc |
|-------|--------|-------------------|
| Phase 1: Local Containerization | **Implemented** | [Docker_Documentation.md](https://github.com/endisciple13/covenant_pipeline/blob/main/Docker_Documentation.md) |
| Phase 2: Cloud Topology (AWS) | Design only | — |
| Phase 3: Infrastructure as Code (Terraform) | Design only | — |
| Phase 4: CI/CD Orchestration | Design only | — |

## Implementation docs (covenant_pipeline, not mirrored)

| Document | Purpose |
|----------|---------|
| [Docker_Documentation.md](https://github.com/endisciple13/covenant_pipeline/blob/main/Docker_Documentation.md) | As-built Phase 1: Dockerfiles, Compose, workflows |
| [Reading the Docker Code.md](https://github.com/endisciple13/covenant_pipeline/blob/main/docs/platform-engineering/learning/Reading%20the%20Docker%20Code.md) | Line-by-line Docker infrastructure walkthrough |
| [Reading the Pipeline Code.md](https://github.com/endisciple13/covenant_pipeline/blob/main/docs/platform-engineering/learning/Reading%20the%20Pipeline%20Code.md) | Line-by-line application code walkthrough |
| [PROJECT_DOCUMENTATION.md](https://github.com/endisciple13/covenant_pipeline/blob/main/PROJECT_DOCUMENTATION.md) | Operational architecture reference |

## Keeping mirrors in sync

```bash
# from the Notes repo root
python scripts/sync_project_docs.py --check   # detect drift (used in CI / pre-commit)
python scripts/sync_project_docs.py --write   # regenerate mirror files in covenant_pipeline
```

Full project note index: [../README.md](../../../Notes/projects/covenant/README.md)
