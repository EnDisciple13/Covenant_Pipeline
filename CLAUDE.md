# Covenant Pipeline — agent entry point

Credit-agreement extraction pipeline. Registry id `covenant_pipeline` in the sibling Notes repo (`../Notes/registry.yaml`). This repo is **proof space** (implementation); strategy and roadmap truth is proposition space in Notes.

## Read order

1. [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) — application doc
2. [Docker_Documentation.md](Docker_Documentation.md) — implementation / as-built doc
3. `docs/platform-engineering/` — strategy mirrors, generated from Notes

## Critical rules

- **Never edit files under `docs/platform-engineering/`** — they carry a `MIRROR:` banner and are overwritten on sync. Canonical files live in `../Notes/projects/covenant/platform-engineering/`; edit there, then run `py scripts/sync_project_docs.py --write` from the Notes repo root, and commit the regenerated mirrors here separately.
- Roadmap/planning status is canonical in Notes; as-built truth is canonical here (`Docker_Documentation.md`).
- Cross-repo conventions: `../Notes/AGENTS.md`. Agent config channels: `../Notes/Agent_Routing.md`.
- Windows: use `py`, not `python`, for scripts.
