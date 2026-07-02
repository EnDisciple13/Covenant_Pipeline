# Platform Engineering Documentation

This folder holds the platform-engineering docs for `covenant_pipeline`. The
strategy docs below are **mirrors**: the canonical copies live in the companion
[notes](https://github.com/endisciple13/notes) repo and are auto-synced here by
`notes/scripts/sync_pe_docs.py`. Do not edit the mirror files directly (they
carry a `MIRROR:` banner) — edit the canonical file in `notes` and re-run sync.

## Strategy docs (mirrored from notes)

| Document | Local mirror | Canonical (notes) |
|----------|--------------|-------------------|
| M1 hub roadmap | [PE_Roadmap_1.md](PE_Roadmap_1.md) | [notes/PE_Roadmap_1.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/PE_Roadmap_1.md) |
| M2 IDP vision | [PE_Roadmap_M2.md](PE_Roadmap_M2.md) | [notes/PE_Roadmap_M2.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/PE_Roadmap_M2.md) |
| Phase 1: Local containerization blueprint | [blueprints/PE_RM_Phase1.md](blueprints/PE_RM_Phase1.md) | [notes/PE_RM_Phase1.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/PE_RM_Phase1.md) |
| Phase 2: Cloud topology blueprint | [blueprints/PE_RM_Phase2.md](blueprints/PE_RM_Phase2.md) | [notes/PE_RM_Phase2.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/PE_RM_Phase2.md) |
| Phase 3: Terraform blueprint | [blueprints/PE_RM_Phase3.md](blueprints/PE_RM_Phase3.md) | [notes/PE_RM_Phase3.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/PE_RM_Phase3.md) |
| Phase 4: CI/CD blueprint | [blueprints/PE_RM_Phase4.md](blueprints/PE_RM_Phase4.md) | [notes/PE_RM_Phase4.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/PE_RM_Phase4.md) |
| Application pipeline math | [math/Math_Application_Pipeline.md](math/Math_Application_Pipeline.md) | [notes/Math_Application_Pipeline.md](https://github.com/endisciple13/notes/blob/main/projects/covenant/Math_Application_Pipeline.md) |

## Reusable theory (notes-only, not mirrored)

| Document | Canonical (notes) |
|----------|-------------------|
| [Math_Containerization.md](../../../notes/math/Math_Containerization.md) | [notes/Math_Containerization.md](https://github.com/endisciple13/notes/blob/main/math/Math_Containerization.md) |
| [Math_Notes_Platform_Engineer.md](../../../notes/math/Math_Notes_Platform_Engineer.md) | [notes/Math_Notes_Platform_Engineer.md](https://github.com/endisciple13/notes/blob/main/math/Math_Notes_Platform_Engineer.md) |

## Phase status (navigation aid)

| Phase | Status | Local implementation doc |
|-------|--------|--------------------------|
| Phase 1: Local Containerization | **Implemented** | [Docker_Documentation.md](../../Docker_Documentation.md) |
| Phase 2: Cloud Topology (AWS) | Design only | — |
| Phase 3: Infrastructure as Code (Terraform) | Design only | — |
| Phase 4: CI/CD Orchestration | Design only | — |

## Implementation docs (this repo, not mirrored)

| Document | Purpose |
|----------|---------|
| [Docker_Documentation.md](../../Docker_Documentation.md) | As-built Phase 1: Dockerfiles, Compose, workflows |
| [learning/Reading the Docker Code.md](learning/Reading%20the%20Docker%20Code.md) | Line-by-line Docker infrastructure walkthrough |
| [learning/Reading the Pipeline Code.md](learning/Reading%20the%20Pipeline%20Code.md) | Line-by-line application code walkthrough |

## Keeping mirrors in sync

Mirrors are regenerated from `notes` via a registry-driven script:

```bash
# from the notes repo root
python scripts/sync_pe_docs.py --check   # detect drift (used in CI / pre-commit)
python scripts/sync_pe_docs.py --write   # regenerate mirror files
```

Full project note index: [notes/projects/covenant/README.md](../../../notes/projects/covenant/README.md)
